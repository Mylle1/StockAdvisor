from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stockbot.saxo.client import SaxoClient
from stockbot.saxo.endpoints import get_positions, get_watchlist, get_watchlists


def _as_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("Data", [])
    return data if isinstance(data, list) else []


def _extract_position_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _as_list(payload):
        pos = item.get("PositionBase") if isinstance(item, dict) else None
        source = pos if isinstance(pos, dict) else item
        if not isinstance(source, dict):
            continue

        uic = source.get("Uic")
        asset_type = source.get("AssetType")
        symbol = source.get("Symbol") or source.get("Identifier")
        description = source.get("Description") or source.get("DisplayName")

        if uic is None:
            continue

        rows.append(
            {
                "uic": uic,
                "asset_type": asset_type,
                "symbol": symbol,
                "name": description,
                "source": "position",
            }
        )

    return rows


def _extract_watchlist_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    candidates: list[dict[str, Any]] = []
    if isinstance(payload.get("Instruments"), list):
        candidates.extend(payload["Instruments"])
    candidates.extend(_as_list(payload))

    for item in candidates:
        if not isinstance(item, dict):
            continue

        uic = item.get("Uic")
        asset_type = item.get("AssetType")
        symbol = item.get("Symbol") or item.get("Identifier")
        description = item.get("Description") or item.get("DisplayName")

        if uic is None:
            continue

        rows.append(
            {
                "uic": uic,
                "asset_type": asset_type,
                "symbol": symbol,
                "name": description,
                "source": "watchlist",
            }
        )

    return rows


def _extract_watchlist_ids(payload: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for row in _as_list(payload):
        watchlist_id = row.get("WatchlistId") if isinstance(row, dict) else None
        if watchlist_id:
            ids.append(str(watchlist_id))
    return ids


def build_filter_universe(client: SaxoClient, out_path: str = "reports/filter_universe.json") -> dict[str, Any]:
    positions_payload = get_positions(client)
    position_rows = _extract_position_rows(positions_payload)

    watchlist_rows: list[dict[str, Any]] = []
    watchlists_payload = get_watchlists(client)
    for watchlist_id in _extract_watchlist_ids(watchlists_payload):
        watchlist_payload = get_watchlist(client, watchlist_id)
        watchlist_rows.extend(_extract_watchlist_rows(watchlist_payload))

    by_uic: dict[tuple[Any, Any], dict[str, Any]] = {}
    for row in position_rows + watchlist_rows:
        key = (row.get("uic"), row.get("asset_type"))
        existing = by_uic.get(key)
        if existing is None:
            by_uic[key] = row
            continue

        existing_source = set(existing["source"].split("+"))
        row_source = set(str(row["source"]).split("+"))
        existing["source"] = "+".join(sorted(existing_source | row_source))
        if not existing.get("symbol") and row.get("symbol"):
            existing["symbol"] = row["symbol"]
        if not existing.get("name") and row.get("name"):
            existing["name"] = row["name"]

    universe = {
        "positions": position_rows,
        "watchlist": watchlist_rows,
        "filter_universe": list(by_uic.values()),
    }

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(universe, indent=2), encoding="utf-8")

    return universe
