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


def _is_otc_candidate(candidate: dict) -> bool:
    exchange_values = [
        candidate.get("exchange"),
        candidate.get("exchangeShortName"),
        candidate.get("stockExchange"),
    ]
    for value in exchange_values:
        if isinstance(value, str) and "OTC" in value.upper():
            return True
    return False


def _candidate_exchange(candidate: dict) -> str | None:
    exchange = candidate.get("exchangeShortName")
    if isinstance(exchange, str) and exchange:
        return exchange.upper()
    exchange = candidate.get("exchange")
    if isinstance(exchange, str) and exchange:
        return exchange.upper()
    return None


def _is_clean_symbol(symbol: str) -> bool:
    return "." not in symbol and "-" not in symbol


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
    def _search_candidates(search_query: str) -> list[dict]:
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

    payload = _search_candidates(query)

    if not payload:
        original_tokens = [token for token in name.strip().split() if token]
        fallback_1_tokens = [
            token for token in original_tokens if token.lower() not in _SHARE_CLASS_TOKENS
        ]
        fallback_1 = " ".join(fallback_1_tokens).strip()

        fallback_queries: list[str] = []
        if fallback_1 and fallback_1.lower() != query.lower():
            fallback_queries.append(fallback_1)

        if fallback_1_tokens:
            fallback_2 = fallback_1_tokens[0].strip()
            if fallback_2 and all(fallback_2.lower() != existing.lower() for existing in fallback_queries):
                fallback_queries.append(fallback_2)

        if fallback_1 and "inc" not in fallback_1.lower().split():
            fallback_3 = f"{fallback_1} Inc"
            if all(fallback_3.lower() != existing.lower() for existing in fallback_queries):
                fallback_queries.append(fallback_3)

        if debug and fallback_queries:
            print(f"[resolve] fallback_queries={fallback_queries!r}")

        selected_fallback_query: str | None = None
        for fallback_query in fallback_queries:
            if debug:
                print(f"[resolve] trying_fallback_query={fallback_query!r}")
            payload = _search_candidates(fallback_query)
            if payload:
                selected_fallback_query = fallback_query
                break

        if debug and selected_fallback_query:
            print(f"[resolve] fallback_selected_query={selected_fallback_query!r}")

    if not payload:
        if debug:
            print("[resolve] candidates=0")
            print("[resolve] selected=None reason=no_candidates")
        return None

    if debug:
        print(f"[resolve] candidates={len(payload)}")
        for candidate in payload[:5]:
            symbol = candidate.get("symbol")
            candidate_name = candidate.get("name")
            exchange = candidate.get("exchange")
            print(
                "[resolve] candidate"
                f" symbol={symbol!r}"
                f" name={candidate_name!r}"
                f" exchange={exchange!r}"
            )

    if len(payload) == 1:
        symbol = payload[0].get("symbol")
        if isinstance(symbol, str) and symbol:
            if debug:
                print(f"[resolve] selected={symbol!r} reason=single_candidate")
            return symbol
        if debug:
            print("[resolve] selected=None reason=single_candidate_missing_symbol")
        return None

    scored_candidates: list[tuple[int, int, bool, str]] = []
    normalized_currency = currency.upper() if isinstance(currency, str) and currency else None

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
            base_score = 200
        elif query in candidate_normalized:
            base_score = 100
        else:
            continue

        score = base_score

        if normalized_currency:
            candidate_currency = candidate.get("currency")
            if isinstance(candidate_currency, str) and candidate_currency:
                if candidate_currency.upper() == normalized_currency:
                    score += 100
            else:
                exchange = _candidate_exchange(candidate)
                preferred_exchanges = _CURRENCY_EXCHANGE_PRIORITY.get(normalized_currency, [])
                if exchange in preferred_exchanges:
                    score += 50

        is_otc = _is_otc_candidate(candidate)
        if is_otc:
            score -= 100
        if _is_clean_symbol(symbol):
            score += 5

        scored_candidates.append((score, base_score, is_otc, symbol))

    if not scored_candidates:
        if debug:
            print("[resolve] selected=None reason=no_match")
        return None

    if not normalized_currency:
        max_base = max(item[1] for item in scored_candidates)
        top_base_candidates = [item for item in scored_candidates if item[1] == max_base]
        non_otc_top_base = [item for item in top_base_candidates if not item[2]]
        comparable = non_otc_top_base or top_base_candidates
        if len(comparable) > 1:
            if debug:
                print("[resolve] selected=None reason=ambiguous_without_currency")
            return None
        if debug:
            print(f"[resolve] selected={comparable[0][3]!r} reason=single_best_base_match")
        return comparable[0][3]

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    top_score, _, _, top_symbol = scored_candidates[0]
    if len(scored_candidates) > 1 and scored_candidates[1][0] == top_score:
        if debug:
            print("[resolve] selected=None reason=ambiguous_top_score")
        return None

    if debug:
        print(f"[resolve] selected={top_symbol!r} reason=scored score={top_score}")
    return top_symbol
