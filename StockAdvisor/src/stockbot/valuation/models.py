from dataclasses import dataclass


@dataclass(slots=True)
class ReverseDCFResult:
    """Container for output from a reverse DCF valuation."""

    implied_revenue_growth: float
    enterprise_value: float
    equity_value: float
    market_cap: float
    forecast_years: int


@dataclass(slots=True)
class DCFResult:
    """Container for output from a forward two-stage FCFF DCF valuation."""

    enterprise_value: float
    equity_value: float
    fair_value_per_share: float
    upside_pct: float
