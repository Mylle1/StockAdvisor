from __future__ import annotations

import argparse
import json

from stockbot.portfolio.ticker_mapping import apply_ticker_mapping, load_ticker_mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply manual ticker mapping to holdings JSON.")
    parser.add_argument("--holdings", required=True, help="Path to holdings JSON file.")
    parser.add_argument("--mapping", required=True, help="Path to ticker mapping JSON file.")
    parser.add_argument("--out", required=True, help="Path to output mapped holdings JSON file.")
    args = parser.parse_args()

    with open(args.holdings, "r", encoding="utf-8") as holdings_file:
        holdings = json.load(holdings_file)

    mapping = load_ticker_mapping(args.mapping)
    updated_holdings, unmapped_names = apply_ticker_mapping(holdings, mapping)

    with open(args.out, "w", encoding="utf-8") as out_file:
        json.dump(updated_holdings, out_file, indent=2, ensure_ascii=False)

    total_holdings = len(updated_holdings)
    mapped_count = total_holdings - len(unmapped_names)

    print(f"Total holdings: {total_holdings}")
    print(f"Mapped tickers: {mapped_count}")
    print(f"Unmapped holdings: {len(unmapped_names)}")
    if unmapped_names:
        print("Missing ticker mapping for:")
        for name in unmapped_names:
            print(f"- {name}")


if __name__ == "__main__":
    main()
