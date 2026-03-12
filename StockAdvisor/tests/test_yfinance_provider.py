from __future__ import annotations

import math

import pytest

from stockbot.fundamentals.yfinance_provider import YahooFundamentalsProvider


class FakeSeries:
    def __init__(self, values):
        self._values = values

    def dropna(self) -> FakeSeries:
        return FakeSeries([value for value in self._values if value is not None])

    def tolist(self) -> list:
        return list(self._values)


class FakeLocAccessor:
    def __init__(self, rows: dict[str, list[float | None]]):
        self._rows = rows

    def __getitem__(self, label: str) -> FakeSeries:
        return FakeSeries(self._rows[label])


class FakeFrame:
    def __init__(self, rows: dict[str, list[float | None]]):
        self.index = set(rows.keys())
        self.empty = not bool(rows)
        self.loc = FakeLocAccessor(rows)


class FakeTicker:
    def __init__(self, *, financials: FakeFrame | None, balance_sheet: FakeFrame | None, cashflow: FakeFrame | None, info: dict):
        self.financials = financials
        self.income_stmt = financials
        self.balance_sheet = balance_sheet
        self.cashflow = cashflow
        self.info = info


def _build_ticker(revenues: list[float | None], *, revenue_label: str = "Total Revenue") -> FakeTicker:
    return FakeTicker(
        financials=FakeFrame({revenue_label: revenues}),
        balance_sheet=FakeFrame({"Total Debt": [50.0], "Cash And Cash Equivalents": [10.0]}),
        cashflow=FakeFrame({"Free Cash Flow": [30.0]}),
        info={"sharesOutstanding": 1000},
    )


def test_get_fundamentals_maps_yfinance_data_with_5_year_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: _build_ticker([200.0, 180.0, 160.0, 140.0, 120.0]))

    fundamentals = provider.get_fundamentals(" asml ")

    assert fundamentals.ticker == "ASML"
    assert fundamentals.revenue_last_year == 200.0
    assert fundamentals.shares_outstanding == 1000.0
    assert fundamentals.net_debt == 40.0
    assert fundamentals.fcf_margin == pytest.approx(0.15)
    assert fundamentals.revenue_growth_5y == pytest.approx((200.0 / 120.0) ** (1 / 4) - 1)
    assert fundamentals.revenue_growth_years_used == 5


def test_get_fundamentals_calculates_growth_for_4_valid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: _build_ticker([160.0, 140.0, 120.0, 100.0]))

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_growth_5y == pytest.approx((160.0 / 100.0) ** (1 / 3) - 1)
    assert fundamentals.revenue_growth_years_used == 4


def test_get_fundamentals_calculates_growth_for_3_valid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: _build_ticker([120.0, 100.0, 80.0]))

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_growth_5y == pytest.approx((120.0 / 80.0) ** (1 / 2) - 1)
    assert fundamentals.revenue_growth_years_used == 3


def test_get_fundamentals_returns_none_growth_with_less_than_3_valid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: _build_ticker([300.0, 270.0]))

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_growth_5y is None
    assert fundamentals.revenue_growth_years_used is None


def test_get_fundamentals_filters_nan_and_non_positive_for_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    revenues = [200.0, math.nan, -10.0, 150.0, 130.0, 110.0]
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: _build_ticker(revenues))

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_growth_5y == pytest.approx((200.0 / 110.0) ** (1 / 3) - 1)
    assert fundamentals.revenue_growth_years_used == 4


def test_get_fundamentals_supports_operating_revenue_label(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    monkeypatch.setattr(
        "stockbot.fundamentals.yfinance_provider.yf.Ticker",
        lambda ticker: _build_ticker([200.0, 180.0, 160.0], revenue_label="Operating Revenue"),
    )

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_last_year == 200.0


def test_get_fundamentals_raises_for_missing_revenue(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    fake_ticker = FakeTicker(
        financials=FakeFrame({}),
        balance_sheet=FakeFrame({"Total Debt": [10.0], "Cash And Cash Equivalents": [2.0]}),
        cashflow=FakeFrame({"Free Cash Flow": [3.0]}),
        info={"sharesOutstanding": 100},
    )
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: fake_ticker)

    with pytest.raises(ValueError, match="Missing revenue data for ticker 'AAPL'"):
        provider.get_fundamentals("AAPL")


def test_get_fundamentals_raises_for_missing_shares_outstanding(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    fake_ticker = FakeTicker(
        financials=FakeFrame({"Total Revenue": [100.0]}),
        balance_sheet=FakeFrame({"Total Debt": [10.0], "Cash And Cash Equivalents": [2.0]}),
        cashflow=FakeFrame({"Free Cash Flow": [3.0]}),
        info={},
    )
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: fake_ticker)

    with pytest.raises(ValueError, match="Missing shares outstanding for ticker 'MSFT'"):
        provider.get_fundamentals("MSFT")


def test_get_fundamentals_raises_for_missing_free_cash_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()
    fake_ticker = FakeTicker(
        financials=FakeFrame({"Total Revenue": [100.0]}),
        balance_sheet=FakeFrame({"Total Debt": [10.0], "Cash And Cash Equivalents": [2.0]}),
        cashflow=FakeFrame({}),
        info={"sharesOutstanding": 100},
    )
    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: fake_ticker)

    with pytest.raises(ValueError, match="Missing free cash flow for ticker 'NVDA'"):
        provider.get_fundamentals("NVDA")
