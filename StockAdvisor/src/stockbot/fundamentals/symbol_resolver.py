from __future__ import annotations

import requests

BASE_URL = "https://financialmodelingprep.com/stable"


def resolve_ticker_by_name(name: str, api_key: str) -> str | None:
    query = name.strip()
    if not query:
        return None
    if not api_key:
        raise ValueError("FMP API key is required")

    response = requests.get(
        f"{BASE_URL}/search-symbol",
        params={"query": query, "apikey": api_key},
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list) or not payload:
        return None

    if len(payload) == 1:
        symbol = payload[0].get("symbol")
        return symbol if isinstance(symbol, str) and symbol else None

    query_lower = query.lower()
    exact_matches: list[str] = []
    contains_matches: list[str] = []

    for candidate in payload:
        symbol = candidate.get("symbol")
        candidate_name = candidate.get("name")
        if not isinstance(symbol, str) or not symbol:
            continue
        if not isinstance(candidate_name, str):
            continue

        candidate_lower = candidate_name.lower()
        if candidate_lower == query_lower:
            exact_matches.append(symbol)
        elif query_lower in candidate_lower:
            contains_matches.append(symbol)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        return None
    if len(contains_matches) == 1:
        return contains_matches[0]

    return None
