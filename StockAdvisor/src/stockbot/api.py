from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from stockbot.fundamentals.models import Fundamentals
from stockbot.fundamentals.yfinance_provider import (
    YFinanceFundamentalsProvider,
    fundamentals_to_json_payload,
)
from stockbot.portfolio.nordnet_report_import import load_nordnet_holdings_from_report
from stockbot.portfolio.ticker_mapping import apply_ticker_mapping
from stockbot.valuation.parameter_estimator import estimate_valuation_params
from stockbot.valuation.service import valuate_stock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_PATH = DATA_DIR / "nordnet_report.csv"
HOLDINGS_RAW_PATH = DATA_DIR / "holdings_raw.json"
HOLDINGS_MAPPED_PATH = DATA_DIR / "holdings_mapped.json"
TICKER_MAPPING_PATH = DATA_DIR / "ticker_mapping.json"
FUNDAMENTALS_PATH = DATA_DIR / "fundamentals.json"


class TickerMappingItem(BaseModel):
    name: str
    ticker: str


class TickerMappingRequest(BaseModel):
    mappings: list[TickerMappingItem]


app = FastAPI(title="StockAdvisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _write_json(path: Path, payload: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _is_stock_holding(holding: dict[str, Any]) -> bool:
    name = str(holding.get("name") or "").strip().lower()
    if not name:
        return False

    non_stock_markers = (
        "kontant",
        "cash",
        "saldo",
        "total",
        "valuta",
        "currency",
        "deposit",
        "etf",
        "ucits",
        "indexfond",
        "indeksfond",
        "fund",
    )
    if any(marker in name for marker in non_stock_markers):
        return False

    return holding.get("quantity") is not None and holding.get("current_price") is not None


def _load_raw_holdings() -> list[dict[str, Any]]:
    holdings = _read_json(HOLDINGS_RAW_PATH, [])
    if not isinstance(holdings, list):
        raise HTTPException(status_code=500, detail="Saved holdings file is invalid.")
    return holdings


def _generate_fundamentals_for_holdings(
    holdings: list[dict[str, Any]],
) -> tuple[dict[str, Fundamentals], list[dict[str, str]]]:
    provider = YFinanceFundamentalsProvider()
    fundamentals_by_ticker: dict[str, Fundamentals] = {}
    errors: list[dict[str, str]] = []

    for holding in holdings:
        ticker = str(holding.get("ticker") or "").strip().upper()
        name = str(holding.get("name") or ticker)
        if not ticker or ticker in fundamentals_by_ticker:
            continue

        try:
            fundamentals_by_ticker[ticker] = provider.get_fundamentals(ticker)
        except Exception as error:
            errors.append(
                {
                    "name": name,
                    "ticker": ticker,
                    "message": f"Could not generate fundamentals from yfinance: {error}",
                }
            )

    _write_json(FUNDAMENTALS_PATH, fundamentals_to_json_payload(fundamentals_by_ticker))
    return fundamentals_by_ticker, errors


def _format_valuation_result(
    holding: dict[str, Any],
    valuation: dict[str, Any],
    fundamentals: Any,
    dcf_params: dict[str, Any],
    reverse_dcf_params: dict[str, Any],
) -> dict[str, Any]:
    model_used = valuation["model_used"]
    active_params = dcf_params if model_used == "dcf" else reverse_dcf_params
    assumptions: dict[str, Any] = {
        "revenueLastYear": fundamentals.revenue_last_year,
        "wacc": active_params["wacc"],
        "terminalGrowth": active_params["terminal_growth"],
        "forecastYears": active_params["forecast_years"],
        "netDebt": fundamentals.net_debt,
        "sharesOutstanding": fundamentals.shares_outstanding,
    }

    if model_used == "dcf":
        assumptions["revenueGrowth"] = dcf_params["revenue_growth"]
        assumptions["targetFcfMargin"] = dcf_params["target_fcf_margin"]
    else:
        assumptions["normalizedTargetFcfMargin"] = reverse_dcf_params["target_fcf_margin"]
        assumptions["impliedRevenueGrowth"] = valuation.get("implied_revenue_growth")

    return {
        "ticker": valuation["ticker"],
        "companyName": holding.get("name") or valuation["ticker"],
        "modelUsed": model_used,
        "currency": holding.get("currency") or "USD",
        "currentPrice": valuation["current_price"],
        "fairValue": valuation.get("fair_value_per_share"),
        "upsidePct": valuation.get("upside_pct"),
        "impliedGrowth": valuation.get("implied_revenue_growth"),
        "assumptions": assumptions,
        "holding": holding,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/uploads/nordnet")
async def upload_nordnet_report(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with UPLOAD_PATH.open("wb") as destination:
        shutil.copyfileobj(file.file, destination)

    try:
        imported_holdings = load_nordnet_holdings_from_report(str(UPLOAD_PATH))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    stock_holdings = [holding for holding in imported_holdings if _is_stock_holding(holding)]
    existing_mapping = _read_json(TICKER_MAPPING_PATH, {})
    if isinstance(existing_mapping, dict):
        stock_holdings, unmapped_names = apply_ticker_mapping(stock_holdings, existing_mapping)
    else:
        unmapped_names = [str(holding.get("name", "")) for holding in stock_holdings]

    _write_json(HOLDINGS_RAW_PATH, stock_holdings)

    return {
        "holdings": stock_holdings,
        "unmappedNames": unmapped_names,
        "importedCount": len(imported_holdings),
        "filteredOutCount": len(imported_holdings) - len(stock_holdings),
    }


@app.post("/api/ticker-mappings")
def confirm_ticker_mappings(request: TickerMappingRequest) -> dict[str, Any]:
    raw_holdings = _load_raw_holdings()

    existing_mapping = _read_json(TICKER_MAPPING_PATH, {})
    if not isinstance(existing_mapping, dict):
        existing_mapping = {}

    for item in request.mappings:
        name = item.name.strip()
        ticker = item.ticker.strip().upper()
        if name and ticker:
            existing_mapping[name] = ticker

    _write_json(TICKER_MAPPING_PATH, existing_mapping)
    mapped_holdings, unmapped_names = apply_ticker_mapping(raw_holdings, existing_mapping)
    _write_json(HOLDINGS_MAPPED_PATH, mapped_holdings)

    return {
        "holdings": mapped_holdings,
        "unmappedNames": unmapped_names,
        "mappingPath": str(TICKER_MAPPING_PATH),
    }


@app.post("/api/valuations/run")
def run_valuations() -> dict[str, Any]:
    mapped_holdings = _read_json(HOLDINGS_MAPPED_PATH, [])
    if not isinstance(mapped_holdings, list) or not mapped_holdings:
        raise HTTPException(status_code=400, detail="No mapped holdings are available.")

    fundamentals_by_ticker, errors = _generate_fundamentals_for_holdings(mapped_holdings)
    results: list[dict[str, Any]] = []

    for holding in mapped_holdings:
        ticker = str(holding.get("ticker") or "").strip().upper()
        name = str(holding.get("name") or ticker)
        current_price = holding.get("current_price")

        if not ticker:
            errors.append({"name": name, "message": "Ticker is missing."})
            continue
        if current_price is None:
            errors.append({"name": name, "ticker": ticker, "message": "Current price is missing."})
            continue

        fundamentals = fundamentals_by_ticker.get(ticker)
        if fundamentals is None:
            errors.append(
                {
                    "name": name,
                    "ticker": ticker,
                    "message": (
                        "Fundamentals were not generated for this ticker. "
                        "Check the yfinance ticker and try again."
                    ),
                }
            )
            continue

        try:
            estimated_params = estimate_valuation_params(
                fundamentals,
                trading_currency=str(holding.get("currency") or ""),
            )
            dcf_params = estimated_params["dcf"]
            reverse_dcf_params = estimated_params["reverse_dcf"]
            valuation = valuate_stock(
                ticker=ticker,
                current_price=float(current_price),
                fundamentals=fundamentals,
                dcf_params=dcf_params,
                reverse_dcf_params=reverse_dcf_params,
            )
            results.append(
                _format_valuation_result(
                    holding,
                    valuation,
                    fundamentals,
                    dcf_params=dcf_params,
                    reverse_dcf_params=reverse_dcf_params,
                )
            )
        except ValueError as error:
            errors.append({"name": name, "ticker": ticker, "message": str(error)})

    return {
        "results": results,
        "errors": errors,
        "parameters": {
            "note": "Parameters are estimated per stock and included on each result.",
        },
    }
