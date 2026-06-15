from __future__ import annotations

from stockbot.fundamentals.models import Fundamentals

FORECAST_YEARS = 10

_DEVELOPED_COUNTRIES = {
    "australia",
    "austria",
    "belgium",
    "canada",
    "denmark",
    "finland",
    "france",
    "germany",
    "hong kong",
    "ireland",
    "israel",
    "italy",
    "japan",
    "netherlands",
    "new zealand",
    "norway",
    "singapore",
    "south korea",
    "spain",
    "sweden",
    "switzerland",
    "united kingdom",
    "united states",
}


def estimate_valuation_params(
    fundamentals: Fundamentals,
    trading_currency: str | None = None,
) -> dict[str, dict[str, float | int]]:
    """Estimate valuation model inputs from each company's fundamentals."""
    terminal_growth = estimate_terminal_growth(fundamentals.country)
    wacc = estimate_wacc(fundamentals.revenue_growth_5y)
    target_fcf_margin = _target_fcf_margin(fundamentals)

    return {
        "dcf": {
            "revenue_growth": estimate_dcf_revenue_growth(fundamentals),
            "target_fcf_margin": target_fcf_margin,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "forecast_years": FORECAST_YEARS,
        },
        "reverse_dcf": {
            "target_fcf_margin": target_fcf_margin,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "forecast_years": FORECAST_YEARS,
        },
    }


def estimate_dcf_revenue_growth(fundamentals: Fundamentals) -> float:
    quarterly_yoy_growth = fundamentals.recent_quarterly_yoy_revenue_growth
    historical_growth = fundamentals.revenue_growth_5y

    if quarterly_yoy_growth is not None and historical_growth is not None:
        return (0.4 * quarterly_yoy_growth) + (0.6 * historical_growth)
    if quarterly_yoy_growth is not None:
        return quarterly_yoy_growth
    if historical_growth is not None:
        return historical_growth
    return 0.05


def estimate_wacc(revenue_growth_5y: float | None) -> float:
    if revenue_growth_5y is not None and revenue_growth_5y > 0.27:
        return 0.12
    if revenue_growth_5y is not None and revenue_growth_5y > 0.15:
        return 0.10
    if revenue_growth_5y is not None and revenue_growth_5y > 0.05:
        return 0.085
    return 0.08


def estimate_terminal_growth(country: str | None) -> float:
    if country and country.strip().lower() in _DEVELOPED_COUNTRIES:
        return 0.025
    return 0.032


def _target_fcf_margin(fundamentals: Fundamentals) -> float:
    if fundamentals.fcf_margin is None:
        return 0.12
    return _clamp(fundamentals.fcf_margin, 0.05, 0.30)


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)
