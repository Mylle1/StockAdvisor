from __future__ import annotations

from unittest.mock import Mock, patch

from stockbot.fundamentals.symbol_resolver import resolve_ticker_by_name


def _mock_response(payload: list[dict]) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_resolve_ticker_by_name_uses_fallback_query_when_normalized_has_no_candidates() -> None:
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response([]),
            _mock_response([{"symbol": "DUOL", "name": "Duolingo Inc"}]),
        ]

        assert resolve_ticker_by_name("Duolingo A", api_key="demo") == "DUOL"


def test_resolve_ticker_by_name_returns_none_when_all_fallback_queries_have_no_candidates() -> None:
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response([]),
            _mock_response([]),
            _mock_response([]),
            _mock_response([]),
            _mock_response([]),
        ]

        assert resolve_ticker_by_name("Duolingo A", api_key="demo") is None
