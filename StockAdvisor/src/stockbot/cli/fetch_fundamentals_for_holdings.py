from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from stockbot.fundamentals.yfinance_provider import YahooFundamentalsProvider


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch fundamentals for mapped holdings using Yahoo Finance (yfinance)."
    )
    parser.add_argument("--holdings", required=True, help="Path to mapped holdings JSON file.")
    parser.add_argument("--out", required=True, help="Path to output fundamentals JSON file.")
    args = parser.parse_args()

    with open(args.holdings, "r", encoding="utf-8") as holdings_file:
        holdings = json.load(holdings_file)

    provider = YahooFundamentalsProvider()

    result: dict[str, dict] = {}
    skipped_missing_ticker = 0
    failed: list[tuple[str, str]] = []

    for holding in holdings:
        raw_ticker = holding.get("ticker")
        ticker = raw_ticker.strip() if isinstance(raw_ticker, str) else ""
        if not ticker:
            skipped_missing_ticker += 1
            continue

        try:
            fundamentals = provider.get_fundamentals(ticker)
            result[fundamentals.ticker] = asdict(fundamentals)
        except ValueError as exc:
            failed.append((ticker.upper(), str(exc)))

    with open(args.out, "w", encoding="utf-8") as out_file:
        json.dump(result, out_file, indent=2, ensure_ascii=False)

    print(f"Total holdings: {len(holdings)}")
    print(f"Fetched fundamentals: {len(result)}")
    print(f"Skipped missing ticker: {skipped_missing_ticker}")
    print(f"Failed fetch: {len(failed)}")

    if failed:
        print("Failed tickers:")
        for ticker, message in failed:
            print(f"- {ticker}: {message}")


if __name__ == "__main__":
    main()
