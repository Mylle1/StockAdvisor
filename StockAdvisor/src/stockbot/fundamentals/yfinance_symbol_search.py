from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yfinance as yf

from stockbot.fundamentals.symbol_resolver import normalize_company_name
from stockbot.fundamentals.yfinance_cache import configure_yfinance_cache

_CURRENCY_EXCHANGE_PRIORITY: dict[str, list[str]] = {
    "USD": ["NMS", "NYQ", "NGM", "NASDAQ", "NYSE"],
    "DKK": ["CPH", "COPENHAGEN"],
    "EUR": ["AMS", "GER", "FRA", "PAR", "XETRA", "AMSTERDAM", "FRANKFURT", "PARIS"],
    "SEK": ["STO", "STOCKHOLM"],
    "NOK": ["OSL", "OSLO"],
    "GBP": ["LSE", "LONDON"],
}

_EQUITY_QUOTE_TYPES = {"EQUITY", "STOCK"}


@dataclass(frozen=True)
class TickerSearchCandidate:
    symbol: str
    name: str
    exchange: str | None
    exchange_display: str | None
    quote_type: str | None
    type_display: str | None

    def to_payload(self) -> dict[str, str | None]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange,
            "exchangeDisplay": self.exchange_display,
            "quoteType": self.quote_type,
            "typeDisplay": self.type_display,
        }


def search_yfinance_tickers(
    query: str,
    currency: str | None = None,
    max_results: int = 8,
) -> list[dict[str, str | None]]:
    search_queries = _search_query_variants(query)
    if not search_queries:
        return []

    candidates: list[TickerSearchCandidate] = []
    seen_symbols: set[str] = set()
    last_error: Exception | None = None

    configure_yfinance_cache()

    for search_query in search_queries:
        try:
            search = yf.Search(
                search_query,
                max_results=max(max_results * 2, 8),
                news_count=0,
                lists_count=0,
                include_cb=False,
                include_nav_links=False,
                include_research=False,
                include_cultural_assets=False,
                enable_fuzzy_query=True,
                recommended=0,
                timeout=10,
                raise_errors=False,
            )
        except Exception as error:
            last_error = error
            continue

        for quote in search.quotes:
            candidate = _candidate_from_quote(quote)
            if candidate is None or candidate.symbol in seen_symbols:
                continue

            seen_symbols.add(candidate.symbol)
            candidates.append(candidate)

    if not candidates and last_error is not None:
        raise RuntimeError(str(last_error)) from last_error

    ranked_candidates = sorted(
        enumerate(candidates),
        key=lambda item: (-_currency_priority_score(item[1], currency), item[0]),
    )
    return [candidate.to_payload() for _, candidate in ranked_candidates[:max_results]]


def _search_query_variants(query: str) -> list[str]:
    stripped_query = query.strip()
    normalized_query = normalize_company_name(stripped_query)
    variants: list[str] = []

    for candidate_query in (normalized_query, stripped_query):
        cleaned_query = candidate_query.strip()
        if cleaned_query and all(cleaned_query.lower() != existing.lower() for existing in variants):
            variants.append(cleaned_query)

    return variants


def _candidate_from_quote(quote: dict[str, Any]) -> TickerSearchCandidate | None:
    symbol = _clean_text(quote.get("symbol"))
    if not symbol:
        return None

    quote_type = _clean_text(quote.get("quoteType"))
    type_display = _clean_text(quote.get("typeDisp"))
    normalized_quote_type = (quote_type or type_display or "").upper()
    if normalized_quote_type not in _EQUITY_QUOTE_TYPES:
        return None

    name = (
        _clean_text(quote.get("longname"))
        or _clean_text(quote.get("shortname"))
        or symbol
    )

    return TickerSearchCandidate(
        symbol=symbol,
        name=name,
        exchange=_clean_text(quote.get("exchange")),
        exchange_display=_clean_text(quote.get("exchDisp")),
        quote_type=quote_type,
        type_display=type_display,
    )


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    stripped_value = value.strip()
    if not stripped_value:
        return None

    return stripped_value


def _currency_priority_score(
    candidate: TickerSearchCandidate,
    currency: str | None,
) -> int:
    if not currency:
        return 0

    normalized_currency = currency.strip().upper()
    priority_values = _CURRENCY_EXCHANGE_PRIORITY.get(normalized_currency, [])
    if not priority_values:
        return 0

    exchange_values = {
        value.upper()
        for value in (candidate.exchange, candidate.exchange_display)
        if value
    }
    for priority_index, priority_value in enumerate(priority_values):
        if priority_value in exchange_values:
            return len(priority_values) - priority_index

    return 0
