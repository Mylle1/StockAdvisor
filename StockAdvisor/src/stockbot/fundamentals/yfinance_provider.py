from __future__ import annotations

from typing import Iterable

import yfinance as yf

from stockbot.fundamentals.models import Fundamentals


class YahooFundamentalsProvider:
    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker is required")

        ticker_obj = yf.Ticker(symbol)

        financials = getattr(ticker_obj, "financials", None)
        income_stmt = getattr(ticker_obj, "income_stmt", None)
        balance_sheet = getattr(ticker_obj, "balance_sheet", None)
        cashflow = getattr(ticker_obj, "cashflow", None)
        info = getattr(ticker_obj, "info", {}) or {}

        revenue_frame = financials if financials is not None else income_stmt
        if revenue_frame is None:
            revenue_frame = income_stmt

        revenue_last_year = self._extract_latest_numeric_value(
            revenue_frame,
            ["Total Revenue", "Revenue", "Operating Revenue"],
        )
        if revenue_last_year is None:
            raise ValueError(f"Missing revenue data for ticker '{symbol}'")

        shares_outstanding = info.get("sharesOutstanding")
        if shares_outstanding is None:
            raise ValueError(f"Missing shares outstanding for ticker '{symbol}'")

        total_debt = self._extract_latest_numeric_value(
            balance_sheet,
            ["Total Debt", "Net Debt"],
        )
        if total_debt is None:
            raise ValueError(f"Missing total debt for ticker '{symbol}'")

        cash_and_equivalents = self._extract_latest_numeric_value(
            balance_sheet,
            ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash"],
        )
        if cash_and_equivalents is None:
            raise ValueError(f"Missing cash and cash equivalents for ticker '{symbol}'")

        free_cash_flow = self._extract_latest_numeric_value(
            cashflow,
            ["Free Cash Flow", "FreeCashFlow"],
        )
        if free_cash_flow is None:
            raise ValueError(f"Missing free cash flow for ticker '{symbol}'")

        net_debt = float(total_debt) - float(cash_and_equivalents)
        fcf_margin = float(free_cash_flow) / float(revenue_last_year)

        revenue_growth_5y = self._calculate_revenue_growth_5y(revenue_frame)

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=float(revenue_last_year),
            shares_outstanding=float(shares_outstanding),
            net_debt=float(net_debt),
            revenue_growth_5y=revenue_growth_5y,
            fcf_margin=float(fcf_margin),
        )

    def _extract_latest_numeric_value(self, frame: object, labels: Iterable[str]) -> float | None:
        if frame is None or getattr(frame, "empty", True):
            return None

        index = getattr(frame, "index", None)
        if index is None:
            return None

        for label in labels:
            if label not in index:
                continue

            series = frame.loc[label]
            values = series.dropna().tolist()
            for value in values:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    def _calculate_revenue_growth_5y(self, revenue_frame: object) -> float | None:
        if revenue_frame is None or getattr(revenue_frame, "empty", True):
            return None

        revenue_series = None
        for label in ["Total Revenue", "Revenue", "Operating Revenue"]:
            if label in getattr(revenue_frame, "index", []):
                revenue_series = revenue_frame.loc[label]
                break

        if revenue_series is None:
            return None

        values = [float(value) for value in revenue_series.dropna().tolist() if value is not None]
        if len(values) < 5:
            return None

        latest_revenue = values[0]
        oldest_revenue = values[4]
        if latest_revenue <= 0 or oldest_revenue <= 0:
            return None

        years = 4
        return (latest_revenue / oldest_revenue) ** (1 / years) - 1
