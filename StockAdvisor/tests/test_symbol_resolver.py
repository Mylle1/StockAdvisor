from __future__ import annotations

from unittest.mock import Mock, patch

from stockbot.fundamentals.symbol_resolver import resolve_ticker_by_name


def _mock_response(payload: list[dict]) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_resolve_ticker_by_name_uses_search_name_for_duolingo() -> None:
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(
            [
                {
                    "symbol": "DUOL",
                    "name": "Duolingo, Inc.",
                    "exchangeShortName": "NASDAQ",
                    "currency": "USD",
                }
            ]
        )

        assert resolve_ticker_by_name("Duolingo A", api_key="demo") == "DUOL"


def test_resolve_ticker_by_name_uses_currency_tiebreaker_for_asml() -> None:
    payload = [
        {
            "symbol": "ASML",
            "name": "ASML Holding N.V.",
            "exchangeShortName": "NASDAQ",
            "currency": "USD",
        },
        {
            "symbol": "ASML.AS",
            "name": "ASML Holding N.V.",
            "exchangeShortName": "AMS",
            "currency": "EUR",
        },
        {
            "symbol": "ASMLF",
            "name": "ASML Holding N.V.",
            "exchangeShortName": "OTC",
            "currency": "USD",
        },
    ]

    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("ASML Holding", api_key="demo", currency="EUR") == "ASML.AS"
        assert resolve_ticker_by_name("ASML Holding", api_key="demo", currency="USD") == "ASML"


def test_resolve_ticker_by_name_returns_none_for_ambiguous_top_scores() -> None:
    payload = [
        {"symbol": "ABC", "name": "Alpha Beta", "exchangeShortName": "NYSE", "currency": "USD"},
        {"symbol": "ABD", "name": "Alpha Beta", "exchangeShortName": "NASDAQ", "currency": "USD"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("Alpha Beta", api_key="demo") is None
