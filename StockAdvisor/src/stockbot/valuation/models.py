from dataclasses import dataclass


@dataclass(slots=True)
class ReverseDCFResult:
    """Container for output from a reverse DCF valuation."""

    implied_revenue_growth: float
    enterprise_value: float
    equity_value: float
    market_cap: float
    forecast_years: int
