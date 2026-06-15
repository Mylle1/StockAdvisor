from __future__ import annotations

from dataclasses import asdict
from typing import Any

import yfinance as yf

from stockbot.fundamentals.models import Fundamentals


class YFinanceFundamentalsProvider:
    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker is required")

        stock = yf.Ticker(symbol)
        info = getattr(stock, "info", {}) or {}
        income_statement = stock.financials
        quarterly_income_statement = stock.quarterly_financials
        cashflow_statement = stock.cashflow
        balance_sheet = stock.balance_sheet

        revenue_last_year = _latest_number(income_statement, "Total Revenue", symbol)
        free_cash_flow = _latest_optional_number(cashflow_statement, "Free Cash Flow")
        if free_cash_flow is None:
            operating_cash_flow = _latest_optional_number(cashflow_statement, "Operating Cash Flow")
            capital_expenditure = _latest_optional_number(cashflow_statement, "Capital Expenditure")
            if operating_cash_flow is not None and capital_expenditure is not None:
                free_cash_flow = operating_cash_flow + capital_expenditure

        shares_outstanding = _shares_outstanding(stock, symbol)
        total_debt = _latest_optional_number(balance_sheet, "Total Debt") or 0.0
        cash = _latest_optional_number(balance_sheet, "Cash And Cash Equivalents") or 0.0

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=revenue_last_year,
            shares_outstanding=shares_outstanding,
            net_debt=total_debt - cash,
            revenue_growth_5y=_revenue_growth(income_statement),
            recent_quarterly_yoy_revenue_growth=_recent_quarterly_yoy_revenue_growth(
                quarterly_income_statement
            ),
            fcf_margin=(free_cash_flow / revenue_last_year if free_cash_flow is not None else None),
            country=info.get("country"),
        )


def fundamentals_to_json_payload(fundamentals_by_ticker: dict[str, Fundamentals]) -> dict[str, Any]:
    return {
        ticker: asdict(fundamentals)
        for ticker, fundamentals in sorted(fundamentals_by_ticker.items())
    }


def _latest_number(statement: Any, row_name: str, ticker: str) -> float:
    value = _latest_optional_number(statement, row_name)
    if value is None:
        raise ValueError(f"Missing required yfinance field '{row_name}' for ticker '{ticker}'.")
    return value


def _latest_optional_number(statement: Any, row_name: str) -> float | None:
    if statement is None or getattr(statement, "empty", True):
        return None
    if row_name not in statement.index:
        return None

    row = statement.loc[row_name].dropna()
    if row.empty:
        return None
    return float(row.iloc[0])


def _revenue_growth(income_statement: Any) -> float | None:
    if income_statement is None or getattr(income_statement, "empty", True):
        return None
    if "Total Revenue" not in income_statement.index:
        return None

    revenues = [float(value) for value in income_statement.loc["Total Revenue"].dropna().tolist()]
    if len(revenues) < 2:
        return None

    latest_revenue = revenues[0]
    oldest_revenue = revenues[-1]
    years = len(revenues) - 1
    if latest_revenue <= 0 or oldest_revenue <= 0 or years <= 0:
        return None

    return (latest_revenue / oldest_revenue) ** (1 / years) - 1


def _recent_quarterly_yoy_revenue_growth(quarterly_income_statement: Any) -> float | None:
    if quarterly_income_statement is None or getattr(quarterly_income_statement, "empty", True):
        return None
    if "Total Revenue" not in quarterly_income_statement.index:
        return None

    revenues = [
        float(value)
        for value in quarterly_income_statement.loc["Total Revenue"].dropna().tolist()
    ]
    if len(revenues) < 5:
        return None

    latest_quarter_revenue = revenues[0]
    same_quarter_previous_year_revenue = revenues[4]
    if latest_quarter_revenue <= 0 or same_quarter_previous_year_revenue <= 0:
        return None

    return (latest_quarter_revenue / same_quarter_previous_year_revenue) - 1


def _shares_outstanding(stock: Any, ticker: str) -> float:
    info = getattr(stock, "info", {}) or {}
    shares_outstanding = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
    if shares_outstanding is None:
        raise ValueError(f"Missing required yfinance field 'sharesOutstanding' for ticker '{ticker}'.")
    return float(shares_outstanding)
