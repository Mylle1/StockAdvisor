from __future__ import annotations

from unittest.mock import Mock, patch

from stockbot.fundamentals.symbol_resolver import resolve_ticker_by_name


def _mock_response(payload: list[dict]) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_resolve_ticker_by_name_returns_symbol_for_single_candidate() -> None:
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response([{"symbol": "AAPL", "name": "Apple Inc"}])

        assert resolve_ticker_by_name("Apple", api_key="demo") == "AAPL"


def test_resolve_ticker_by_name_picks_best_substring_match() -> None:
    payload = [
        {"symbol": "NOVO-B.CO", "name": "Novo Nordisk A/S"},
        {"symbol": "NVO", "name": "Novo Integrated Sciences"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("Novo Nordisk", api_key="demo") == "NOVO-B.CO"


def test_resolve_ticker_by_name_returns_none_for_ambiguous_candidates() -> None:
    payload = [
        {"symbol": "ABC", "name": "Alpha Beta Corp"},
        {"symbol": "ABD", "name": "Alpha Beta Dynamics"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("Alpha Beta", api_key="demo") is None
