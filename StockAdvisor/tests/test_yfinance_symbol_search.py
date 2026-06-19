from __future__ import annotations

from stockbot.fundamentals import yfinance_symbol_search as symbol_search
from stockbot.fundamentals.yfinance_symbol_search import search_yfinance_tickers


def test_search_yfinance_tickers_normalizes_share_class_names(monkeypatch) -> None:
    calls: list[str] = []

    class FakeSearch:
        def __init__(self, query: str, **kwargs) -> None:
            calls.append(query)
            self.quotes = [
                {
                    "symbol": "DUOL",
                    "longname": "Duolingo, Inc.",
                    "exchange": "NMS",
                    "exchDisp": "NASDAQ",
                    "quoteType": "EQUITY",
                    "typeDisp": "Equity",
                }
            ] if query == "duolingo" else []

    monkeypatch.setattr(symbol_search.yf, "Search", FakeSearch)

    candidates = search_yfinance_tickers("Duolingo A", currency="USD")

    assert calls[0] == "duolingo"
    assert candidates[0]["symbol"] == "DUOL"
    assert candidates[0]["name"] == "Duolingo, Inc."


def test_search_yfinance_tickers_filters_to_equities_and_prefers_currency_exchange(
    monkeypatch,
) -> None:
    class FakeSearch:
        def __init__(self, query: str, **kwargs) -> None:
            self.quotes = [
                {
                    "symbol": "NVO",
                    "longname": "Novo Nordisk A/S",
                    "exchange": "NYQ",
                    "exchDisp": "NYSE",
                    "quoteType": "EQUITY",
                    "typeDisp": "Equity",
                },
                {
                    "symbol": "NOVO-B.CO",
                    "longname": "Novo Nordisk A/S",
                    "exchange": "CPH",
                    "exchDisp": "Copenhagen",
                    "quoteType": "EQUITY",
                    "typeDisp": "Equity",
                },
                {
                    "symbol": "NVOH",
                    "longname": "Novo Nordisk A/S B Shares ADRhedged",
                    "exchange": "PCX",
                    "exchDisp": "NYSEArca",
                    "quoteType": "ETF",
                    "typeDisp": "ETF",
                },
            ]

    monkeypatch.setattr(symbol_search.yf, "Search", FakeSearch)

    candidates = search_yfinance_tickers("Novo Nordisk B", currency="DKK")

    assert [candidate["symbol"] for candidate in candidates] == ["NOVO-B.CO", "NVO"]
