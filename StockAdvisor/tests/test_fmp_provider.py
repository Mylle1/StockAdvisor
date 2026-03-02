from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from stockbot.fundamentals.fmp_provider import FMPFundamentalsProvider


def _mock_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_get_fundamentals_maps_fmp_payload_to_model() -> None:
    provider = FMPFundamentalsProvider(api_key="demo")

    with patch("stockbot.fundamentals.fmp_provider.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(
                [
                    {"revenue": 1400},
                    {"revenue": 1300},
                    {"revenue": 1200},
                    {"revenue": 1100},
                    {"revenue": 1000},
                ]
            ),
            _mock_response([{"freeCashFlow": 210}]),
            _mock_response([{"totalDebt": 500, "cashAndCashEquivalents": 120}]),
            _mock_response([{"sharesOutstanding": 100}]),
        ]

        fundamentals = provider.get_fundamentals("aapl")

    assert fundamentals.ticker == "AAPL"
    assert fundamentals.revenue_last_year == 1400
    assert fundamentals.shares_outstanding == 100
    assert fundamentals.net_debt == 380
    assert fundamentals.fcf_margin == pytest.approx(0.15)
    assert fundamentals.revenue_growth_5y == pytest.approx((1400 / 1000) ** (1 / 4) - 1)


def test_get_fundamentals_raises_value_error_for_missing_ticker() -> None:
    provider = FMPFundamentalsProvider(api_key="demo")

    with patch("stockbot.fundamentals.fmp_provider.requests.get") as mock_get:
        mock_get.return_value = _mock_response([])

        with pytest.raises(ValueError, match="Ticker 'MSFT' not found in FMP"):
            provider.get_fundamentals("MSFT")


def test_get_fundamentals_raises_value_error_when_required_data_missing() -> None:
    provider = FMPFundamentalsProvider(api_key="demo")

    with patch("stockbot.fundamentals.fmp_provider.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response([{"revenue": None}]),
            _mock_response([{"freeCashFlow": 50}]),
            _mock_response([{"totalDebt": 10, "cashAndCashEquivalents": 5}]),
            _mock_response([{"sharesOutstanding": 2}]),
        ]

        with pytest.raises(ValueError, match="Missing required field 'revenue'"):
            provider.get_fundamentals("TSLA")
