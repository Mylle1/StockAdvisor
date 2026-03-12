from __future__ import annotations

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
        self._rows = rows
        self.index = set(rows.keys())
        self.empty = not bool(rows)
        self.loc = FakeLocAccessor(rows)


class FakeTicker:
    def __init__(
        self,
        *,
        financials: FakeFrame | None,
        balance_sheet: FakeFrame | None,
        cashflow: FakeFrame | None,
        info: dict,
    ):
        self.financials = financials
        self.income_stmt = financials
        self.balance_sheet = balance_sheet
        self.cashflow = cashflow
        self.info = info


def test_get_fundamentals_maps_yfinance_data(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooFundamentalsProvider()

    fake_ticker = FakeTicker(
        financials=FakeFrame({"Total Revenue": [200.0, 180.0, 160.0, 140.0, 120.0]}),
        balance_sheet=FakeFrame(
            {
                "Total Debt": [50.0],
                "Cash And Cash Equivalents": [10.0],
            }
        ),
        cashflow=FakeFrame({"Free Cash Flow": [30.0]}),
        info={"sharesOutstanding": 1000},
    )

    monkeypatch.setattr(
        "stockbot.fundamentals.yfinance_provider.yf.Ticker",
        lambda ticker: fake_ticker,
    )

    fundamentals = provider.get_fundamentals(" asml ")

    assert fundamentals.ticker == "ASML"
    assert fundamentals.revenue_last_year == 200.0
    assert fundamentals.shares_outstanding == 1000.0
    assert fundamentals.net_debt == 40.0
    assert fundamentals.fcf_margin == pytest.approx(0.15)
    assert fundamentals.revenue_growth_5y == pytest.approx((200.0 / 120.0) ** (1 / 4) - 1)


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


def test_get_fundamentals_raises_for_missing_shares_outstanding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_get_fundamentals_raises_for_missing_free_cash_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_get_fundamentals_returns_none_growth_with_insufficient_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = YahooFundamentalsProvider()
    fake_ticker = FakeTicker(
        financials=FakeFrame({"Total Revenue": [300.0, 270.0, 240.0]}),
        balance_sheet=FakeFrame({"Total Debt": [20.0], "Cash And Cash Equivalents": [5.0]}),
        cashflow=FakeFrame({"Free Cash Flow": [30.0]}),
        info={"sharesOutstanding": 10},
    )

    monkeypatch.setattr("stockbot.fundamentals.yfinance_provider.yf.Ticker", lambda ticker: fake_ticker)

    fundamentals = provider.get_fundamentals("DUOL")

    assert fundamentals.revenue_growth_5y is None
