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


def _load_price_lookup_from_holdings(path: str) -> dict[str, float]:
    with open(path, "r", encoding="utf-8") as holdings_file:
        holdings = json.load(holdings_file)

    prices_by_ticker: dict[str, float] = {}
    for holding in holdings:
        ticker = holding.get("ticker")
        current_price = holding.get("current_price")
        if not ticker or current_price is None:
            continue
        prices_by_ticker[str(ticker).strip()] = float(current_price)

    return prices_by_ticker


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
    args = parser.parse_args()

    fundamentals_by_ticker = load_fundamentals_from_json(args.fundamentals)
    prices_by_ticker = _load_price_lookup_from_holdings(args.holdings)
    dcf_params, reverse_dcf_params = _build_valuation_params(args)
    tickers = [ticker.strip() for ticker in args.tickers.split(",") if ticker.strip()]

    rows: list[dict] = []
    for ticker in tickers:
        fundamentals = fundamentals_by_ticker.get(ticker)
        if fundamentals is None:
            print(f"{ticker}: MISSING FUNDAMENTALS")
            continue

        if ticker not in prices_by_ticker:
            print(f"{ticker}: MISSING PRICE")
            continue

        revenue_growth = fundamentals.revenue_growth_5y or 0.0
        dcf_params_for_ticker = {
            **dcf_params,
            "revenue_growth": revenue_growth,
        }
        reverse_dcf_params_for_ticker = {
            **reverse_dcf_params,
            "wacc": estimate_wacc(revenue_growth),
        }

        rows.append(
            valuate_stock(
                ticker=ticker,
                current_price=prices_by_ticker[ticker],
                fundamentals=fundamentals,
                dcf_params=dcf_params_for_ticker,
                reverse_dcf_params=reverse_dcf_params_for_ticker,
                model_override=args.model_override,
            )
        )

    header = (
        "ticker".ljust(8)
        + "model_used".ljust(14)
        + "current_price".ljust(14)
        + "fair_value".ljust(14)
        + "upside_pct".ljust(14)
        + "implied_growth"
    )
    print(header)

    for row in rows:
        print(
            row["ticker"].ljust(8)
            + row["model_used"].ljust(14)
            + _format_number(row.get("current_price")).ljust(14)
            + _format_number(row.get("fair_value_per_share")).ljust(14)
            + _format_number(row.get("upside_pct")).ljust(14)
            + _format_number(row.get("implied_revenue_growth"))
        )


if __name__ == "__main__":
    main()
