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

_CURRENCY_EXCHANGE_PRIORITY: dict[str, list[str]] = {
    "USD": ["NASDAQ", "NYSE"],
    "EUR": ["AMS", "XETRA", "EPA", "BIT", "MAD"],
    "DKK": ["CPH"],
    "SEK": ["STO"],
    "NOK": ["OSL"],
    "GBP": ["LSE"],
}


def _candidate_symbol(candidate: dict) -> str | None:
    symbol = candidate.get("symbol") or candidate.get("ticker")
    if isinstance(symbol, str) and symbol:
        return symbol
    return None


def _candidate_name(candidate: dict) -> str | None:
    name = candidate.get("name") or candidate.get("companyName")
    if isinstance(name, str) and name:
        return name
    return None


def _candidate_exchange(candidate: dict) -> str | None:
    exchange = (
        candidate.get("exchange")
        or candidate.get("exchangeShortName")
        or candidate.get("stockExchange")
    )
    if isinstance(exchange, str) and exchange:
        return exchange.upper()
    return None


def _normalize_currency_code(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip().upper()
    if not normalized:
        return None

    return normalized


def _candidate_currency(candidate: dict) -> str | None:
    candidate_currency = candidate.get("currency")
    return _normalize_currency_code(candidate_currency)


def _is_otc_candidate(candidate: dict) -> bool:
    exchange = _candidate_exchange(candidate)
    return isinstance(exchange, str) and "OTC" in exchange


def _is_clean_symbol(symbol: str) -> bool:
    return "." not in symbol and "-" not in symbol


def _search_candidates_by_name(search_query: str, api_key: str) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/search-name",
        params={"query": search_query, "apikey": api_key, "limit": 10},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        return []
    return payload


def _search_candidates_by_symbol(search_query: str, api_key: str) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/search-symbol",
        params={"query": search_query, "apikey": api_key},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        return []
    return payload


def _score_candidate(
    candidate: dict,
    query: str,
    normalized_currency: str | None,
) -> int | None:
    symbol = _candidate_symbol(candidate)
    candidate_name = _candidate_name(candidate)
    if not symbol or not candidate_name:
        return None

    candidate_normalized = normalize_company_name(candidate_name)
    if not candidate_normalized:
        return None

    if candidate_normalized == query:
        score = 300
    elif query in candidate_normalized:
        score = 200
    else:
        score = 100

    candidate_currency = _candidate_currency(candidate)
    if normalized_currency and candidate_currency == normalized_currency:
        score += 100

    if normalized_currency:
        preferred_exchanges = _CURRENCY_EXCHANGE_PRIORITY.get(normalized_currency, [])
        if _candidate_exchange(candidate) in preferred_exchanges:
            score += 50

    if _is_otc_candidate(candidate):
        score -= 100

    return score


def normalize_company_name(name: str) -> str:
    cleaned = name.strip().lower().translate(_PUNCTUATION_TRANSLATION)
    tokens = [token for token in cleaned.split() if token]
    normalized_tokens = [
        token
        for token in tokens
        if token not in _SUFFIX_TOKENS and token not in _SHARE_CLASS_TOKENS
    ]
    return " ".join(normalized_tokens)


def resolve_ticker_by_name(
    name: str,
    api_key: str,
    currency: str | None = None,
    debug: bool = False,
) -> str | None:
    if debug:
        print(f"[resolve] original_name={name!r}")
    query = normalize_company_name(name)
    if debug:
        print(f"[resolve] normalized_query={query!r}")
    if not query:
        if debug:
            print("[resolve] selected=None reason=empty_query")
        return None
    if not api_key:
        raise ValueError("FMP API key is required")

    if debug:
        print("[resolve] endpoint='search-name'")
    payload = _search_candidates_by_name(query, api_key)

    if not payload:
        fallback_queries: list[str] = []
        original_tokens = [token for token in name.strip().split() if token]
        first_part = " ".join(original_tokens[:-1]).strip() if len(original_tokens) > 1 else name.strip()
        if first_part:
            fallback_queries.append(first_part)
            if "inc" not in first_part.lower().split():
                fallback_queries.append(f"{first_part} Inc")
            if "inc." not in first_part.lower().split():
                fallback_queries.append(f"{first_part}, Inc.")

        deduped_fallbacks: list[str] = []
        for fallback_query in fallback_queries:
            if fallback_query and all(fallback_query.lower() != existing.lower() for existing in deduped_fallbacks):
                deduped_fallbacks.append(fallback_query)

        if debug and deduped_fallbacks:
            print(f"[resolve] fallback_queries={deduped_fallbacks!r}")

        for fallback_query in deduped_fallbacks:
            payload = _search_candidates_by_name(fallback_query, api_key)
            if payload:
                break

    if not payload:
        first_word = query.split()[0] if query.split() else ""
        symbol_query = first_word[:4].upper()
        if symbol_query:
            if debug:
                print("[resolve] endpoint='search-symbol' fallback")
                print(f"[resolve] symbol_fallback_query={symbol_query!r}")
            payload = _search_candidates_by_symbol(symbol_query, api_key)

    if not payload:
        if debug:
            print("[resolve] candidates=0")
            print("[resolve] selected=None reason=no_candidates")
        return None

    if debug:
        print(f"[resolve] candidates={len(payload)}")
        for candidate in payload[:5]:
            print(
                "[resolve] candidate"
                f" symbol={_candidate_symbol(candidate)!r}"
                f" name={_candidate_name(candidate)!r}"
                f" exchange={_candidate_exchange(candidate)!r}"
                f" currency={_candidate_currency(candidate)!r}"
            )

    normalized_currency = _normalize_currency_code(currency)

    if len(payload) == 1:
        candidate = payload[0]
        symbol = _candidate_symbol(candidate)
        score = _score_candidate(candidate, query, normalized_currency)
        if symbol and score is not None:
            if debug:
                print("[resolve] selected=%r reason=single_candidate score=%s" % (symbol, score))
            return symbol
        if debug:
            print("[resolve] selected=None reason=single_candidate_missing_symbol")
        return None

    scored_candidates: list[tuple[int, str]] = []

    for candidate in payload:
        symbol = _candidate_symbol(candidate)
        score = _score_candidate(candidate, query, normalized_currency)
        if not symbol or score is None:
            continue

        scored_candidates.append((score, symbol))

    if not scored_candidates:
        if debug:
            print("[resolve] selected=None reason=no_match")
        return None

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    if len(scored_candidates) > 1 and scored_candidates[0][0] == scored_candidates[1][0]:
        if debug:
            print("[resolve] selected=None reason=ambiguous")
        return None

    selected_score, selected_symbol = scored_candidates[0]
    if debug:
        print(f"[resolve] selected={selected_symbol!r} reason=scored score={selected_score}")
    return selected_symbol
