from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from stockbot.fundamentals.symbol_resolver import resolve_ticker_by_name
from stockbot.portfolio.nordnet_report_import import load_nordnet_holdings_from_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Nordnet report to normalized holdings JSON")
    parser.add_argument("--report", required=True, help="Path to Nordnet report file")
    parser.add_argument("--out", required=True, help="Path to output normalized JSON")
    parser.add_argument(
        "--resolve-tickers",
        action="store_true",
        help="Resolve missing tickers using FMP search endpoint",
    )
    parser.add_argument(
        "--debug-resolve",
        action="store_true",
        help="Print debug output from symbol resolver while resolving tickers",
    )
    args = parser.parse_args()

    holdings = load_nordnet_holdings_from_report(args.report)

    resolved_count = 0
    if args.resolve_tickers:
        api_key = os.getenv("FMP_API_KEY", "").strip()
        if not api_key:
            raise ValueError("--resolve-tickers requires FMP_API_KEY to be set.")

        for holding in holdings:
            ticker = resolve_ticker_by_name(
                holding["name"],
                api_key,
                currency=holding["currency"],
                debug=args.debug_resolve,
            )
            if ticker:
                holding["ticker"] = ticker
                resolved_count += 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(holdings, indent=2, ensure_ascii=False), encoding="utf-8")

    unresolved = [holding for holding in holdings if not holding.get("ticker")]
    print(f"Holdings imported: {len(holdings)}")
    print(f"Tickers resolved: {resolved_count}")
    if unresolved:
        print("Missing tickers:")
        for holding in unresolved:
            print(f"- {holding['name']}")


if __name__ == "__main__":
    main()
