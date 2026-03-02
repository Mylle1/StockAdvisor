from __future__ import annotations

import requests

from stockbot.fundamentals.models import Fundamentals


class FMPFundamentalsProvider:
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FMP API key is required")
        self.api_key = api_key

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker is required")

        income_statements = self._fetch_list(f"/income-statement/{symbol}", limit=5)
        cashflow_statements = self._fetch_list(f"/cash-flow-statement/{symbol}", limit=1)
        balance_sheets = self._fetch_list(f"/balance-sheet-statement/{symbol}", limit=1)
        profiles = self._fetch_list(f"/profile/{symbol}")

        latest_income = income_statements[0]
        latest_cashflow = cashflow_statements[0]
        latest_balance = balance_sheets[0]
        profile = profiles[0]

        revenue_last_year = self._require_number(latest_income, "revenue", symbol)
        free_cash_flow = self._require_number(latest_cashflow, "freeCashFlow", symbol)

        total_debt = self._require_number(latest_balance, "totalDebt", symbol)
        cash = self._require_number(latest_balance, "cashAndCashEquivalents", symbol)

        shares_outstanding = self._require_number(profile, "sharesOutstanding", symbol)

        net_debt = total_debt - cash
        fcf_margin = free_cash_flow / revenue_last_year
        revenue_growth_5y = self._calculate_revenue_growth_5y(income_statements)

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=revenue_last_year,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt,
            revenue_growth_5y=revenue_growth_5y,
            fcf_margin=fcf_margin,
        )

    def _fetch_list(self, path: str, limit: int | None = None) -> list[dict]:
        params: dict[str, str | int] = {"apikey": self.api_key}
        if limit is not None:
            params["limit"] = limit

        response = requests.get(f"{self.BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list) or not payload:
            ticker = path.rsplit("/", maxsplit=1)[-1]
            raise ValueError(f"Ticker '{ticker}' not found in FMP.")

        return payload

    @staticmethod
    def _require_number(data: dict, field: str, ticker: str) -> float:
        value = data.get(field)
        if value is None:
            raise ValueError(f"Missing required field '{field}' for ticker '{ticker}'.")
        return float(value)

    @staticmethod
    def _calculate_revenue_growth_5y(income_statements: list[dict]) -> float | None:
        if len(income_statements) < 5:
            return None

        latest_revenue = income_statements[0].get("revenue")
        oldest_revenue = income_statements[4].get("revenue")
        if latest_revenue is None or oldest_revenue is None:
            return None

        latest_revenue = float(latest_revenue)
        oldest_revenue = float(oldest_revenue)
        if oldest_revenue <= 0:
            return None

        years = 4
        return (latest_revenue / oldest_revenue) ** (1 / years) - 1
