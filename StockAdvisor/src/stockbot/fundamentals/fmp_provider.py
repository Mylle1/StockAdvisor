from __future__ import annotations

import requests

from stockbot.fundamentals.models import Fundamentals


class FMPFundamentalsProvider:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FMP API key is required")
        self.api_key = api_key

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = ticker.strip().upper()
        if not symbol:
            raise ValueError("Ticker is required")

        income_statement = self._fetch_dict("/income-statement", symbol, limit=1)
        cashflow_statement = self._fetch_dict("/cash-flow-statement", symbol, limit=1)
        balance_sheet = self._fetch_dict("/balance-sheet-statement", symbol, limit=1)

        revenue_last_year = self._require_number(income_statement, "revenue", symbol)
        free_cash_flow = self._require_number(cashflow_statement, "freeCashFlow", symbol)

        total_debt = self._require_number(balance_sheet, "totalDebt", symbol)
        cash = self._require_number(balance_sheet, "cashAndCashEquivalents", symbol)

        # Use diluted shares outstanding from income statement
        shares_outstanding = self._require_number(
            income_statement, "weightedAverageShsOutDil", symbol
        )

        net_debt = total_debt - cash
        fcf_margin = free_cash_flow / revenue_last_year
        
        # For 5-year growth, we need to fetch multiple years
        revenue_growth_5y = self._calculate_revenue_growth_5y(symbol)

        return Fundamentals(
            ticker=symbol,
            revenue_last_year=revenue_last_year,
            shares_outstanding=shares_outstanding,
            net_debt=net_debt,
            revenue_growth_5y=revenue_growth_5y,
            fcf_margin=fcf_margin,
        )

    def _fetch_dict(self, endpoint: str, symbol: str, limit: int | None = None) -> dict:
        params: dict[str, str | int] = {
            "symbol": symbol,
            "apikey": self.api_key,
        }
        if limit is not None:
            params["limit"] = limit

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        payload = response.json()
        
        # New stable API returns list, we want the first (most recent) item
        if isinstance(payload, list):
            if not payload:
                raise ValueError(f"Ticker '{symbol}' not found in FMP.")
            return payload[0]
        
        if not isinstance(payload, dict) or not payload:
            raise ValueError(f"Ticker '{symbol}' not found in FMP.")

        return payload

    @staticmethod
    def _require_number(data: dict, field: str, ticker: str) -> float:
        value = data.get(field)
        if value is None:
            raise ValueError(f"Missing required field '{field}' for ticker '{ticker}'.")
        return float(value)

    def _calculate_revenue_growth_5y(self, symbol: str) -> float | None:
        """Calculate 5-year revenue CAGR. Returns None if insufficient data."""
        try:
            # Fetch last 5 years of annual income statements
            url = f"{self.BASE_URL}/income-statement"
            params = {"symbol": symbol, "apikey": self.api_key, "limit": 5}
            response = requests.get(url, params=params, timeout=10)
            
            if not response.ok:
                return None
                
            income_statements = response.json()
            if not isinstance(income_statements, list) or len(income_statements) < 5:
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
        except Exception:
            return None
