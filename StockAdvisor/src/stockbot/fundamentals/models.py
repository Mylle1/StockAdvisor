from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fundamentals:
    ticker: str
    revenue_last_year: float
    shares_outstanding: float
    net_debt: float = 0.0
    revenue_growth_5y: float | None = None
    revenue_growth_years_used: int | None = None
    fcf_margin: float | None = None
