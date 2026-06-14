from __future__ import annotations

import math
from typing import Iterable

import yfinance as yf

from stockbot.fundamentals.models import Fundamentals


class YahooFundamentalsProvider:
    _REVENUE_LABELS = ["Total Revenue", "Operating Revenue", "Revenue"]
    _FREE_CASH_FLOW_LABELS = ["Free Cash Flow", "FreeCashFlow"]

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker is required")

        ticker_obj = yf.Ticker(symbol)

        financials = getattr(ticker_obj, "financials", None)
        income_stmt = getattr(ticker_obj, "income_stmt", None)
        quarterly_financials = getattr(ticker_obj, "quarterly_financials", None)
        quarterly_income_stmt = getattr(ticker_obj, "quarterly_income_stmt", None)
        balance_sheet = getattr(ticker_obj, "balance_sheet", None)
        cashflow = getattr(ticker_obj, "cashflow", None)
        info = getattr(ticker_obj, "info", {}) or {}

        revenue_frame = financials if financials is not None else income_stmt
        quarterly_revenue_frame = quarterly_financials if quarterly_financials is not None else quarterly_income_stmt
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

        free_cash_flow = self._extract_latest_numeric_value(cashflow, self._FREE_CASH_FLOW_LABELS)
        if free_cash_flow is None:
            raise ValueError(f"Missing free cash flow for ticker '{symbol}'")

        revenue_growth_5y, revenue_growth_years_used = self._calculate_revenue_growth(revenue_frame)
        normalized_fcf_margin, fcf_margin_years_used = self._calculate_normalized_fcf_margin(
            revenue_frame,
            cashflow,
        )
        recent_quarterly_yoy_revenue_growth = self._calculate_recent_quarterly_yoy_revenue_growth(
            quarterly_revenue_frame
        )

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=float(revenue_last_year),
            shares_outstanding=float(shares_outstanding),
            net_debt=float(total_debt) - float(cash_and_equivalents),
            revenue_growth_5y=revenue_growth_5y,
            recent_quarterly_yoy_revenue_growth=recent_quarterly_yoy_revenue_growth,
            revenue_growth_years_used=revenue_growth_years_used,
            fcf_margin=float(free_cash_flow) / float(revenue_last_year),
            normalized_fcf_margin=normalized_fcf_margin,
            fcf_margin_years_used=fcf_margin_years_used,
            country=info.get("country"),
            financial_currency=info.get("financialCurrency") or info.get("currency"),
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

    def _calculate_recent_quarterly_yoy_revenue_growth(self, quarterly_revenue_frame: object) -> float | None:
        revenue_values = self._extract_valid_revenue_values(quarterly_revenue_frame)
        if len(revenue_values) < 5:
            return None

        latest_quarter_revenue = revenue_values[0]
        prior_year_same_quarter_revenue = revenue_values[4]
        return (latest_quarter_revenue / prior_year_same_quarter_revenue) - 1

    def _calculate_normalized_fcf_margin(
        self,
        revenue_frame: object,
        cashflow_frame: object,
    ) -> tuple[float | None, int | None]:
        revenue_values = self._extract_numeric_values(revenue_frame, self._REVENUE_LABELS)
        fcf_values = self._extract_numeric_values(cashflow_frame, self._FREE_CASH_FLOW_LABELS)

        matched_years: list[tuple[float, float]] = []
        for revenue, free_cash_flow in zip(revenue_values, fcf_values):
            if revenue is None or free_cash_flow is None:
                continue
            if revenue <= 0:
                continue
            matched_years.append((revenue, free_cash_flow))

        years_used = min(5, len(matched_years))
        if years_used < 3:
            return None, None

        selected_years = matched_years[:years_used]
        total_revenue = sum(revenue for revenue, _free_cash_flow in selected_years)
        total_free_cash_flow = sum(free_cash_flow for _revenue, free_cash_flow in selected_years)
        return total_free_cash_flow / total_revenue, years_used

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

    def _extract_numeric_values(self, frame: object, labels: Iterable[str]) -> list[float | None]:
        if frame is None or getattr(frame, "empty", True):
            return []

        index = getattr(frame, "index", None)
        if index is None:
            return []

        for label in labels:
            if label not in index:
                continue
            series = frame.loc[label]
            return [self._to_positive_or_negative_number(value) for value in series.tolist()]

        return []

    @staticmethod
    def _to_positive_or_negative_number(value: object) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if math.isnan(number):
            return None

        return number
