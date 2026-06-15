from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from stockbot.fundamentals.yfinance_provider import YFinanceFundamentalsProvider


def test_get_fundamentals_maps_yfinance_statements_to_model() -> None:
    stock = SimpleNamespace(
        financials=pd.DataFrame(
            [[1400.0, 1200.0, 1000.0]],
            index=["Total Revenue"],
        ),
        quarterly_financials=pd.DataFrame(
            [[350.0, 330.0, 320.0, 310.0, 280.0]],
            index=["Total Revenue"],
        ),
        cashflow=pd.DataFrame(
            [[210.0]],
            index=["Free Cash Flow"],
        ),
        balance_sheet=pd.DataFrame(
            [[500.0], [120.0]],
            index=["Total Debt", "Cash And Cash Equivalents"],
        ),
        info={"sharesOutstanding": 100, "country": "United States"},
    )

    with patch("stockbot.fundamentals.yfinance_provider.yf.Ticker", return_value=stock):
        fundamentals = YFinanceFundamentalsProvider().get_fundamentals("aapl")

    assert fundamentals.ticker == "AAPL"
    assert fundamentals.revenue_last_year == 1400
    assert fundamentals.shares_outstanding == 100
    assert fundamentals.net_debt == 380
    assert fundamentals.country == "United States"
    assert fundamentals.fcf_margin == pytest.approx(0.15)
    assert fundamentals.revenue_growth_5y == pytest.approx((1400 / 1000) ** (1 / 2) - 1)
    assert fundamentals.recent_quarterly_yoy_revenue_growth == pytest.approx(0.25)


def test_get_fundamentals_raises_for_missing_revenue() -> None:
    stock = SimpleNamespace(
        financials=pd.DataFrame(),
        quarterly_financials=pd.DataFrame(),
        cashflow=pd.DataFrame(),
        balance_sheet=pd.DataFrame(),
        info={"sharesOutstanding": 100},
    )

    with patch("stockbot.fundamentals.yfinance_provider.yf.Ticker", return_value=stock):
        with pytest.raises(ValueError, match="Total Revenue"):
            YFinanceFundamentalsProvider().get_fundamentals("MSFT")
