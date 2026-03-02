from __future__ import annotations

from stockbot.valuation.models import DCFResult


def two_stage_dcf(
    current_price: float,
    revenue_last_year: float,
    revenue_growth: float,
    target_fcf_margin: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
    net_debt: float,
    shares_outstanding: float,
) -> dict:
    """Run a two-stage FCFF DCF valuation with constant growth in stage one.

    FCFF (Free Cash Flow to Firm) represents cash flows available to all capital
    providers (debt and equity), before servicing debt. In this model FCFF is
    approximated as a fixed margin of revenue during the explicit forecast period.

    Terminal value is computed with the Gordon Growth formula at the end of the
    explicit forecast horizon:
        terminal_value = fcf_last_year * (1 + terminal_growth) / (wacc - terminal_growth)

    The denominator requires ``wacc > terminal_growth``. If this is not true, the
    perpetuity formula is undefined or economically implausible, so a ``ValueError``
    is raised.
    """
    if shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be positive")
    if revenue_last_year <= 0:
        raise ValueError("revenue_last_year must be positive")
    if forecast_years <= 0:
        raise ValueError("forecast_years must be positive")
    if wacc <= terminal_growth:
        raise ValueError("wacc must be greater than terminal_growth")

    discounted_fcf_sum = 0.0
    fcf_last_year = 0.0

    for year in range(1, forecast_years + 1):
        revenue_t = revenue_last_year * ((1.0 + revenue_growth) ** year)
        fcf_t = revenue_t * target_fcf_margin
        discounted_fcf_t = fcf_t / ((1.0 + wacc) ** year)
        discounted_fcf_sum += discounted_fcf_t
        fcf_last_year = fcf_t

    terminal_value = (fcf_last_year * (1.0 + terminal_growth)) / (wacc - terminal_growth)
    discounted_terminal_value = terminal_value / ((1.0 + wacc) ** forecast_years)

    enterprise_value = discounted_fcf_sum + discounted_terminal_value
    equity_value = enterprise_value - net_debt
    fair_value_per_share = equity_value / shares_outstanding
    upside_pct = (fair_value_per_share / current_price) - 1.0

    result = DCFResult(
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        fair_value_per_share=fair_value_per_share,
        upside_pct=upside_pct,
    )

    return {
        "enterprise_value": result.enterprise_value,
        "equity_value": result.equity_value,
        "fair_value_per_share": result.fair_value_per_share,
        "upside_pct": result.upside_pct,
        "forecast_years": forecast_years,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
    }
