from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from typing import Any

from stockbot.fundamentals.fmp_provider import FMPFundamentalsProvider


def _load_holdings(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as holdings_file:
        payload = json.load(holdings_file)

    if not isinstance(payload, list):
        raise ValueError("Holdings JSON must be a list of holdings")

    return payload


def _normalize_ticker(raw_ticker: Any) -> str:
    if raw_ticker is None:
        return ""
    return str(raw_ticker).strip().upper()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch fundamentals for mapped holdings and write them to JSON."
    )
    parser.add_argument("--holdings", required=True, help="Path to mapped holdings JSON file.")
    parser.add_argument("--out", required=True, help="Path to output fundamentals JSON file.")
    parser.add_argument(
        "--api-key",
        default=os.getenv("FMP_API_KEY", ""),
        help="FMP API key (defaults to FMP_API_KEY environment variable).",
    )
    args = parser.parse_args()

    holdings = _load_holdings(args.holdings)
    provider = FMPFundamentalsProvider(api_key=args.api_key)

    fundamentals_by_ticker: dict[str, dict[str, Any]] = {}
    failed_tickers: list[str] = []
    skipped_missing_ticker_count = 0

    for holding in holdings:
        ticker = _normalize_ticker(holding.get("ticker"))
        if not ticker:
            skipped_missing_ticker_count += 1
            continue

        try:
            fundamentals = provider.get_fundamentals(ticker)
        except Exception:
            failed_tickers.append(ticker)
            continue

        fundamentals_by_ticker[ticker] = asdict(fundamentals)

    with open(args.out, "w", encoding="utf-8") as out_file:
        json.dump(fundamentals_by_ticker, out_file, indent=2, ensure_ascii=False)

    print(f"Total holdings: {len(holdings)}")
    print(f"Fetched fundamentals: {len(fundamentals_by_ticker)}")
    print(f"Skipped missing ticker: {skipped_missing_ticker_count}")
    print(f"Failed fetch: {len(failed_tickers)}")
    if failed_tickers:
        print("Failed tickers:")
        for ticker in failed_tickers:
            print(f"- {ticker}")


if __name__ == "__main__":
    main()
