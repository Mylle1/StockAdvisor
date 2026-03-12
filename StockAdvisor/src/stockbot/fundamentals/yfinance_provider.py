from __future__ import annotations

import math
from typing import Iterable

import yfinance as yf

from stockbot.fundamentals.models import Fundamentals


class YahooFundamentalsProvider:
    _REVENUE_LABELS = ["Total Revenue", "Operating Revenue", "Revenue"]

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
        revenue_last_year = self._extract_latest_numeric_value(revenue_frame, self._REVENUE_LABELS)
        if revenue_last_year is None:
            raise ValueError(f"Missing revenue data for ticker '{symbol}'")

        shares_outstanding = info.get("sharesOutstanding")
        if shares_outstanding is None:
            raise ValueError(f"Missing shares outstanding for ticker '{symbol}'")

        total_debt = self._extract_latest_numeric_value(balance_sheet, ["Total Debt"])
        if total_debt is None:
            raise ValueError(f"Missing total debt for ticker '{symbol}'")

        cash_and_equivalents = self._extract_latest_numeric_value(
            balance_sheet,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments",
                "Cash",
            ],
        )
        if cash_and_equivalents is None:
            raise ValueError(f"Missing cash and cash equivalents for ticker '{symbol}'")

        free_cash_flow = self._extract_latest_numeric_value(cashflow, ["Free Cash Flow", "FreeCashFlow"])
        if free_cash_flow is None:
            raise ValueError(f"Missing free cash flow for ticker '{symbol}'")

        revenue_growth_5y, revenue_growth_years_used = self._calculate_revenue_growth(revenue_frame)

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=float(revenue_last_year),
            shares_outstanding=float(shares_outstanding),
            net_debt=float(total_debt) - float(cash_and_equivalents),
            revenue_growth_5y=revenue_growth_5y,
            revenue_growth_years_used=revenue_growth_years_used,
            fcf_margin=float(free_cash_flow) / float(revenue_last_year),
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
            for value in series.dropna().tolist():
                number = self._to_positive_or_negative_number(value)
                if number is not None:
                    return number

        return None

    def _calculate_revenue_growth(self, revenue_frame: object) -> tuple[float | None, int | None]:
        revenue_values = self._extract_valid_revenue_values(revenue_frame)
        if len(revenue_values) < 3:
            return None, None

        years_used = min(5, len(revenue_values))
        latest_revenue = revenue_values[0]
        oldest_revenue = revenue_values[years_used - 1]

        periods = years_used - 1
        cagr = (latest_revenue / oldest_revenue) ** (1 / periods) - 1
        return cagr, years_used

    def _extract_valid_revenue_values(self, revenue_frame: object) -> list[float]:
        if revenue_frame is None or getattr(revenue_frame, "empty", True):
            return []

        index = getattr(revenue_frame, "index", None)
        if index is None:
            return []

        revenue_series = None
        for label in self._REVENUE_LABELS:
            if label in index:
                revenue_series = revenue_frame.loc[label]
                break

        if revenue_series is None:
            return []

        values: list[float] = []
        for value in revenue_series.dropna().tolist():
            number = self._to_positive_or_negative_number(value)
            if number is None:
                continue
            if number > 0:
                values.append(number)

        return values

    @staticmethod
    def _to_positive_or_negative_number(value: object) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if math.isnan(number):
            return None

        return number
