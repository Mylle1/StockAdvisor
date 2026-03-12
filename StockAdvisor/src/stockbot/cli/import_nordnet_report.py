from __future__ import annotations

import argparse
import json

from stockbot.portfolio.nordnet_report_import import load_nordnet_holdings_from_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Nordnet report to normalized holdings JSON.")
    parser.add_argument("--report", required=True, help="Path to Nordnet report file.")
    parser.add_argument("--out", required=True, help="Path to output holdings JSON.")
    args = parser.parse_args()

    holdings = load_nordnet_holdings_from_report(args.report)

    with open(args.out, "w", encoding="utf-8") as out_file:
        json.dump(holdings, out_file, indent=2, ensure_ascii=False)

    print(f"Holdings imported: {len(holdings)}")
    print(f"Output written to: {args.out}")


if __name__ == "__main__":
    main()
