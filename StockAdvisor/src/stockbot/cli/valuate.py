from __future__ import annotations

import argparse

from stockbot.fundamentals.local_provider import load_fundamentals_from_json
from stockbot.valuation.service import valuate_stock

DEFAULT_DCF_PARAMS = {
    "revenue_growth": 0.08,
    "target_fcf_margin": 0.2,
    "wacc": 0.1,
    "terminal_growth": 0.03,
    "forecast_years": 10,
}

DEFAULT_REVERSE_DCF_PARAMS = {
    "target_fcf_margin": 0.2,
    "wacc": 0.1,
    "terminal_growth": 0.03,
    "forecast_years": 10,
}


def _parse_prices(raw_prices: str) -> dict[str, float]:
    prices: dict[str, float] = {}
    if not raw_prices:
        return prices

    for entry in raw_prices.split(","):
        ticker, price = entry.split("=", maxsplit=1)
        prices[ticker.strip()] = float(price)
    return prices


def _format_number(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local stock valuations")
    parser.add_argument("--fundamentals", required=True, help="Path to fundamentals JSON")
    parser.add_argument("--tickers", required=True, help="Comma separated list, e.g. AAPL,MSFT")
    parser.add_argument("--prices", required=True, help="Ticker prices, e.g. AAPL=180,MSFT=420")
    parser.add_argument("--model-override", choices=["dcf", "reverse_dcf"], default=None)
    args = parser.parse_args()

    fundamentals_by_ticker = load_fundamentals_from_json(args.fundamentals)
    prices = _parse_prices(args.prices)
    tickers = [ticker.strip() for ticker in args.tickers.split(",") if ticker.strip()]

    rows: list[dict] = []
    for ticker in tickers:
        fundamentals = fundamentals_by_ticker.get(ticker)
        if fundamentals is None:
            print(f"{ticker}: MISSING FUNDAMENTALS")
            continue

        if ticker not in prices:
            print(f"{ticker}: MISSING PRICE")
            continue

        rows.append(
            valuate_stock(
                ticker=ticker,
                current_price=prices[ticker],
                fundamentals=fundamentals,
                dcf_params=DEFAULT_DCF_PARAMS,
                reverse_dcf_params=DEFAULT_REVERSE_DCF_PARAMS,
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
