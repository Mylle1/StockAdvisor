from __future__ import annotations

import requests

BASE_URL = "https://financialmodelingprep.com/stable"

_SUFFIX_TOKENS = {
    "holding",
    "holdings",
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "ltd",
    "limited",
    "plc",
    "nv",
    "sa",
    "ab",
    "as",
    "a/s",
    "ag",
    "se",
    "spa",
    "oyj",
    "group",
}

_SHARE_CLASS_TOKENS = {"a", "b", "c", "class", "adr"}

_PUNCTUATION_TRANSLATION = str.maketrans({
    ".": " ",
    ",": " ",
    "(": " ",
    ")": " ",
    "-": " ",
})


def normalize_company_name(name: str) -> str:
    cleaned = name.strip().lower().translate(_PUNCTUATION_TRANSLATION)
    tokens = [token for token in cleaned.split() if token]
    normalized_tokens = [
        token
        for token in tokens
        if token not in _SUFFIX_TOKENS and token not in _SHARE_CLASS_TOKENS
    ]
    return " ".join(normalized_tokens)


def resolve_ticker_by_name(name: str, api_key: str) -> str | None:
    query = normalize_company_name(name)
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

    exact_matches: list[str] = []
    contains_matches: list[str] = []

    for candidate in payload:
        symbol = candidate.get("symbol")
        candidate_name = candidate.get("name")
        if not isinstance(symbol, str) or not symbol:
            continue
        if not isinstance(candidate_name, str):
            continue

        candidate_normalized = normalize_company_name(candidate_name)
        if not candidate_normalized:
            continue

        if candidate_normalized == query:
            exact_matches.append(symbol)
        elif query in candidate_normalized:
            contains_matches.append(symbol)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        return None
    if len(contains_matches) == 1:
        return contains_matches[0]

    return None
