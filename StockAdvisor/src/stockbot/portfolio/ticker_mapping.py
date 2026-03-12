from __future__ import annotations

import json
from typing import Any


def load_ticker_mapping(path: str) -> dict[str, str]:
    with open(path, "r", encoding="utf-8") as mapping_file:
        raw_mapping: dict[str, Any] = json.load(mapping_file)

    return {str(name): str(ticker) for name, ticker in raw_mapping.items()}


def apply_ticker_mapping(
    holdings: list[dict], mapping: dict[str, str]
) -> tuple[list[dict], list[str]]:
    updated_holdings: list[dict] = []

    for holding in holdings:
        updated_holding = dict(holding)
        name = str(updated_holding.get("name", ""))
        mapped_ticker = mapping.get(name)
        if mapped_ticker and mapped_ticker.strip():
            updated_holding["ticker"] = mapped_ticker
        updated_holdings.append(updated_holding)

    unmapped_names = [
        str(holding.get("name", ""))
        for holding in updated_holdings
        if not holding.get("ticker")
    ]
    return updated_holdings, unmapped_names
