from __future__ import annotations

from unittest.mock import Mock, patch

from stockbot.fundamentals.symbol_resolver import normalize_company_name, resolve_ticker_by_name


def _mock_response(payload: list[dict]) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_normalize_company_name_removes_common_suffixes() -> None:
    assert normalize_company_name("ASML Holding") == "asml"
    assert normalize_company_name("Duolingo A") == "duolingo"
    assert normalize_company_name("Apple Inc.") == "apple"
    assert normalize_company_name("Berkshire Hathaway Class B") == "berkshire hathaway"


def test_resolve_ticker_by_name_prefers_exact_normalized_match() -> None:
    payload = [
        {"symbol": "ASML.AS", "name": "ASML Holding N.V."},
        {"symbol": "ASMIY", "name": "ASM International ADR"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("ASML Holding", api_key="demo") == "ASML.AS"


def test_resolve_ticker_by_name_returns_none_for_ambiguous_weak_matches() -> None:
    payload = [
        {"symbol": "ABC", "name": "Alpha Beta Corp"},
        {"symbol": "ABD", "name": "Alpha Beta Limited"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        assert resolve_ticker_by_name("Alpha Beta", api_key="demo") is None
