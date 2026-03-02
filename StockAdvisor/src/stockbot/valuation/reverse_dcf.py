from __future__ import annotations

from stockbot.valuation.models import ReverseDCFResult


def _valuation_from_growth(
    growth_rate: float,
    revenue_last_year: float,
    target_fcf_margin: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
    net_debt: float,
) -> tuple[float, float]:
    """Return enterprise value and equity value for a given constant revenue CAGR."""
    revenue = revenue_last_year
    discounted_fcf_sum = 0.0

    for year in range(1, forecast_years + 1):
        revenue *= 1.0 + growth_rate
        fcf = revenue * target_fcf_margin
        discounted_fcf_sum += fcf / ((1.0 + wacc) ** year)

    terminal_fcf = revenue * target_fcf_margin * (1.0 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    discounted_terminal_value = terminal_value / ((1.0 + wacc) ** forecast_years)

    enterprise_value = discounted_fcf_sum + discounted_terminal_value
    equity_value = enterprise_value - net_debt
    return enterprise_value, equity_value


def reverse_dcf_implied_growth(
    current_price: float,
    shares_outstanding: float,
    revenue_last_year: float,
    target_fcf_margin: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int = 10,
    net_debt: float = 0.0,
) -> dict:
    """Solve for the implied revenue growth from a reverse DCF model.

    Mathematics:
    1) Market capitalization is computed as:
       market_cap = current_price * shares_outstanding
    2) Revenue is projected using a constant CAGR g over N years:
       revenue_t = revenue_last_year * (1 + g)^t
    3) Free cash flow each year is a fixed margin of revenue:
       fcf_t = revenue_t * target_fcf_margin
    4) Enterprise value is the discounted sum of explicit period FCF plus
       a Gordon Growth terminal value at year N:
       EV = sum_{t=1..N} fcf_t / (1 + wacc)^t
            + [fcf_N * (1 + terminal_growth) / (wacc - terminal_growth)] / (1 + wacc)^N
    5) Equity value is EV adjusted for net debt:
       equity_value = EV - net_debt

    The function uses binary search for g in [-10%, 50%] and finds the growth
    rate that makes equity_value match market_cap.
    """
    if shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be positive")
    if revenue_last_year <= 0:
        raise ValueError("revenue_last_year must be positive")
    if forecast_years <= 0:
        raise ValueError("forecast_years must be positive")
    if wacc <= terminal_growth:
        raise ValueError("wacc must be greater than terminal_growth")

    market_cap = current_price * shares_outstanding

    low, high = -0.10, 0.50
    tolerance = 1e-6
    max_iterations = 200

    enterprise_value = 0.0
    equity_value = 0.0

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        enterprise_value, equity_value = _valuation_from_growth(
            growth_rate=mid,
            revenue_last_year=revenue_last_year,
            target_fcf_margin=target_fcf_margin,
            wacc=wacc,
            terminal_growth=terminal_growth,
            forecast_years=forecast_years,
            net_debt=net_debt,
        )

        diff = equity_value - market_cap
        if abs(diff) < tolerance:
            break

        if diff < 0:
            low = mid
        else:
            high = mid

    implied_growth = (low + high) / 2.0
    enterprise_value, equity_value = _valuation_from_growth(
        growth_rate=implied_growth,
        revenue_last_year=revenue_last_year,
        target_fcf_margin=target_fcf_margin,
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        net_debt=net_debt,
    )

    result = ReverseDCFResult(
        implied_revenue_growth=implied_growth,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        market_cap=market_cap,
        forecast_years=forecast_years,
    )
    return {
        "implied_revenue_growth": result.implied_revenue_growth,
        "enterprise_value": result.enterprise_value,
        "equity_value": result.equity_value,
        "market_cap": result.market_cap,
        "forecast_years": result.forecast_years,
    }
