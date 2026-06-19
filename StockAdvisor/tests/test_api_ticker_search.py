from __future__ import annotations

import pytest
from fastapi import HTTPException

import stockbot.api as api


def test_search_tickers_returns_candidates(monkeypatch) -> None:
    def fake_search(query: str, currency: str | None = None) -> list[dict[str, str | None]]:
        assert query == "Novo Nordisk"
        assert currency == "DKK"
        return [
            {
                "symbol": "NOVO-B.CO",
                "name": "Novo Nordisk A/S",
                "exchange": "CPH",
                "exchangeDisplay": "Copenhagen",
                "quoteType": "EQUITY",
                "typeDisplay": "Equity",
            }
        ]

    monkeypatch.setattr(api, "search_yfinance_tickers", fake_search)

    result = api.search_tickers(" Novo Nordisk ", currency="DKK")

    assert result["query"] == "Novo Nordisk"
    assert result["candidates"][0]["symbol"] == "NOVO-B.CO"


def test_search_tickers_rejects_empty_query() -> None:
    with pytest.raises(HTTPException) as error:
        api.search_tickers("   ")

    assert error.value.status_code == 400
