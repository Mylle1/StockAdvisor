from __future__ import annotations

from unittest.mock import Mock, patch

from stockbot.fundamentals.symbol_resolver import resolve_ticker_by_name


def _mock_response(payload: list[dict]) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_debug_mode_does_not_change_result_for_single_candidate(capsys) -> None:
    payload = [{"symbol": "AAPL", "name": "Apple Inc", "exchange": "NASDAQ"}]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        normal = resolve_ticker_by_name("Apple", api_key="demo")
        debug = resolve_ticker_by_name("Apple", api_key="demo", debug=True)

    assert normal == "AAPL"
    assert debug == "AAPL"

    output = capsys.readouterr().out
    assert "original_name='Apple'" in output
    assert "normalized_query='apple'" in output
    assert "candidates=1" in output
    assert "selected='AAPL' reason=single_candidate" in output


def test_debug_mode_does_not_change_result_for_no_match(capsys) -> None:
    payload = [
        {"symbol": "ABC", "name": "Alpha Beta Corp", "exchange": "NYSE"},
        {"symbol": "ABD", "name": "Alpha Beta Limited", "exchange": "LSE"},
    ]
    with patch("stockbot.fundamentals.symbol_resolver.requests.get") as mock_get:
        mock_get.return_value = _mock_response(payload)

        normal = resolve_ticker_by_name("Alpha Beta", api_key="demo")
        debug = resolve_ticker_by_name("Alpha Beta", api_key="demo", debug=True)

    assert normal is None
    assert debug is None

    output = capsys.readouterr().out
    assert "candidates=2" in output
    assert "candidate symbol='ABC'" in output
    assert "candidate symbol='ABD'" in output
    assert "selected=None reason=ambiguous" in output
