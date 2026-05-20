from __future__ import annotations

import argparse
import json

from stockbot.fundamentals.local_provider import load_fundamentals_from_json
from stockbot.valuation.model_selector import estimate_wacc
from stockbot.valuation.service import valuate_stock

DEFAULT_DCF_PARAMS = {
    "target_fcf_margin": 0.2,
    "forecast_years": 10,
}

DEFAULT_REVERSE_DCF_PARAMS = {
    "target_fcf_margin": 0.2,
    "forecast_years": 10,
}


def _normalize_currency(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    return normalized or None


def _load_price_lookup_from_holdings(path: str) -> dict[str, float]:
    return {
        ticker: holding["current_price"]
        for ticker, holding in _load_holding_lookup(path).items()
    }


def _load_holding_lookup(path: str) -> dict[str, dict]:
    with open(path, "r", encoding="utf-8") as holdings_file:
        holdings = json.load(holdings_file)

    holdings_by_ticker: dict[str, dict] = {}
    for holding in holdings:
        ticker = holding.get("ticker")
        current_price = holding.get("current_price")
        if not ticker or current_price is None:
            continue
        normalized_ticker = str(ticker).strip()
        holdings_by_ticker[normalized_ticker] = {
            **holding,
            "ticker": normalized_ticker,
            "current_price": float(current_price),
            "currency": _normalize_currency(holding.get("currency")),
        }

    return holdings_by_ticker


def _fetch_exchange_rate(from_currency: str, to_currency: str) -> float:
    if from_currency == to_currency:
        return 1.0

    import yfinance as yf

    ticker_symbol = f"{from_currency}{to_currency}=X"
    ticker_obj = yf.Ticker(ticker_symbol)
    info = getattr(ticker_obj, "info", {}) or {}
    for key in ("regularMarketPrice", "currentPrice", "previousClose"):
        value = info.get(key)
        if value:
            return float(value)

    history = ticker_obj.history(period="5d")
    if history is not None and not getattr(history, "empty", True):
        close_series = history["Close"].dropna()
        if not close_series.empty:
            return float(close_series.iloc[-1])

    raise ValueError(f"Missing exchange rate for {from_currency}->{to_currency}")


def _get_exchange_rate(
    from_currency: str | None,
    to_currency: str | None,
    exchange_rates: dict[tuple[str, str], float],
) -> float:
    if not from_currency or not to_currency or from_currency == to_currency:
        return 1.0

    key = (from_currency, to_currency)
    if key not in exchange_rates:
        exchange_rates[key] = _fetch_exchange_rate(*key)
    return exchange_rates[key]


def _format_number(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def _build_valuation_params(args: argparse.Namespace) -> tuple[dict, dict]:
    dcf_params = {
        "target_fcf_margin": args.target_fcf_margin,
        "forecast_years": args.forecast_years,
    }
    reverse_dcf_params = {
        "target_fcf_margin": args.target_fcf_margin,
        "forecast_years": args.forecast_years,
    }
    return dcf_params, reverse_dcf_params


def _parse_exchange_rate_overrides(values: list[str] | None) -> dict[tuple[str, str], float]:
    overrides: dict[tuple[str, str], float] = {}
    for value in values or []:
        pair, rate = value.split("=", 1)
        from_currency, to_currency = pair.split(":", 1)
        overrides[(_normalize_currency(from_currency) or "", _normalize_currency(to_currency) or "")] = float(rate)
    return overrides


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local stock valuations")
    parser.add_argument("--fundamentals", required=True, help="Path to fundamentals JSON")
    parser.add_argument("--holdings", required=True, help="Path to mapped holdings JSON")
    parser.add_argument("--tickers", required=True, help="Comma separated list, e.g. AAPL,MSFT")
    parser.add_argument(
        "--target-fcf-margin",
        type=float,
        default=DEFAULT_DCF_PARAMS["target_fcf_margin"],
        help="Target free-cash-flow margin used for both DCF and reverse DCF",
    )
    parser.add_argument(
        "--forecast-years",
        type=int,
        default=DEFAULT_DCF_PARAMS["forecast_years"],
        help="Forecast horizon in years used for both DCF and reverse DCF",
    )
    parser.add_argument("--model-override", choices=["dcf", "reverse_dcf"], default=None)
    parser.add_argument(
        "--exchange-rate",
        action="append",
        default=[],
        help="Override FX rate as FROM:TO=RATE, e.g. CNY:USD=0.147 or NOK:EUR=0.085",
    )
    args = parser.parse_args()

    fundamentals_by_ticker = load_fundamentals_from_json(args.fundamentals)
    holdings_by_ticker = _load_holding_lookup(args.holdings)
    dcf_params, reverse_dcf_params = _build_valuation_params(args)
    tickers = [ticker.strip() for ticker in args.tickers.split(",") if ticker.strip()]
    exchange_rates = _parse_exchange_rate_overrides(args.exchange_rate)

    rows: list[dict] = []
    for ticker in tickers:
        fundamentals = fundamentals_by_ticker.get(ticker)
        if fundamentals is None:
            print(f"{ticker}: MISSING FUNDAMENTALS")
            continue

        holding = holdings_by_ticker.get(ticker)
        if holding is None:
            print(f"{ticker}: MISSING PRICE")
            continue

        quote_currency = _normalize_currency(holding.get("currency"))
        financial_currency = _normalize_currency(fundamentals.financial_currency) or quote_currency
        quote_to_financial_rate = _get_exchange_rate(
            quote_currency,
            financial_currency,
            exchange_rates,
        )
        current_price = holding["current_price"]
        current_price_for_valuation = current_price * quote_to_financial_rate

        revenue_growth = fundamentals.revenue_growth_5y or 0.0
        dcf_params_for_ticker = {
            **dcf_params,
            "target_fcf_margin": fundamentals.fcf_margin if fundamentals.fcf_margin is not None else dcf_params["target_fcf_margin"],
        }

        reverse_dcf_params_for_ticker = {
            **reverse_dcf_params,
            "target_fcf_margin": fundamentals.fcf_margin if fundamentals.fcf_margin is not None else reverse_dcf_params["target_fcf_margin"],
            "wacc": estimate_wacc(revenue_growth),
        }

        rows.append(
            {
                **valuate_stock(
                    ticker=ticker,
                    current_price=current_price_for_valuation,
                    fundamentals=fundamentals,
                    dcf_params=dcf_params_for_ticker,
                    reverse_dcf_params=reverse_dcf_params_for_ticker,
                    model_override=args.model_override,
                ),
                "current_price": current_price,
                "quote_currency": quote_currency,
                "financial_currency": financial_currency,
                "exchange_rate": quote_to_financial_rate,
            }
        )

        if rows[-1].get("fair_value_per_share") is not None:
            financial_to_quote_rate = _get_exchange_rate(
                financial_currency,
                quote_currency,
                exchange_rates,
            )
            rows[-1]["fair_value_per_share"] *= financial_to_quote_rate
            rows[-1]["upside_pct"] = (
                rows[-1]["fair_value_per_share"] / current_price
            ) - 1.0

    header = (
        "ticker".ljust(12)
        + "model_used".ljust(14)
        + "currency".ljust(10)
        + "current_price".ljust(14)
        + "fair_value".ljust(14)
        + "upside_pct".ljust(14)
        + "implied_growth"
    )
    print(header)

    for row in rows:
        print(
            row["ticker"].ljust(12)
            + row["model_used"].ljust(14)
            + str(row.get("quote_currency") or "-").ljust(10)
            + _format_number(row.get("current_price")).ljust(14)
            + _format_number(row.get("fair_value_per_share")).ljust(14)
            + _format_number(row.get("upside_pct")).ljust(14)
            + _format_number(row.get("implied_revenue_growth"))
        )


if __name__ == "__main__":
    main()
