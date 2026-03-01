from __future__ import annotations

from typing import Any

from stockbot.portfolio.holding import Holding
from stockbot.saxo.client import SaxoClient
from stockbot.saxo.endpoints import get_positions


def _pick_numeric(source: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _pick_text(source: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def get_saxo_holdings(client: SaxoClient | None = None) -> tuple[list[Holding], dict[str, float]]:
    """Load Saxo positions and map them into provider-agnostic holdings.

    Returns:
        tuple[list[Holding], dict[str, float]]:
            - holdings mapped from Saxo positions
            - current prices keyed by ticker when available
    """
    resolved_client = client or SaxoClient()
    payload = get_positions(resolved_client)

    data = payload.get("Data", [])
    rows = data if isinstance(data, list) else []

    holdings: list[Holding] = []
    current_prices: dict[str, float] = {}

    for item in rows:
        if not isinstance(item, dict):
            continue

        position_base = item.get("PositionBase") if isinstance(item.get("PositionBase"), dict) else {}
        source = {**position_base, **item}

        provider_id = source.get("Uic") or source.get("InstrumentId")
        ticker = _pick_text(source, ["Symbol", "Identifier"])
        if not ticker:
            ticker = f"UIC-{provider_id}" if provider_id is not None else "UNKNOWN"

        quantity = _pick_numeric(source, ["Amount", "Quantity", "LongAmount"])
        if quantity is None:
            quantity = 0.0

        holding = Holding(
            platform="saxo",
            ticker=ticker,
            name=_pick_text(source, ["Description", "DisplayName"]),
            quantity=quantity,
            currency=_pick_text(source, ["CurrencyCode", "Currency"]),
            provider_id=provider_id,
        )
        holdings.append(holding)

        price = _pick_numeric(
            source,
            [
                "CurrentPrice",
                "MarketPrice",
                "Price",
                "LastPrice",
                "LastTraded",
            ],
        )
        if price is not None:
            current_prices[holding.ticker] = price

    return holdings, current_prices
