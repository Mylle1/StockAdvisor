from __future__ import annotations

import logging

from stockbot.portfolio.saxo_holdings import get_saxo_holdings

logger = logging.getLogger(__name__)


def _print_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No holdings found.")
        return

    columns = ["platform", "ticker", "name", "quantity", "currency", "current_price"]
    widths = {
        col: max(len(col), *(len(str(row.get(col, ""))) for row in rows))
        for col in columns
    }

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)

    print(header)
    print(separator)

    for row in rows:
        print(" | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    holdings, current_prices = get_saxo_holdings()

    rows: list[dict[str, str]] = []
    for holding in holdings:
        price = current_prices.get(holding.ticker)
        if price is None:
            logger.warning(
                "Missing current_price for ticker=%s provider_id=%s (price key not present in Saxo response)",
                holding.ticker,
                holding.provider_id,
            )
            display_price = "N/A"
        else:
            display_price = str(price)

        rows.append(
            {
                "platform": holding.platform,
                "ticker": holding.ticker,
                "name": holding.name or "",
                "quantity": str(holding.quantity),
                "currency": holding.currency or "",
                "current_price": display_price,
            }
        )

    _print_table(rows)


if __name__ == "__main__":
    main()
