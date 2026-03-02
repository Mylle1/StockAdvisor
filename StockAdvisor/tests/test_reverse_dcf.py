import math

from stockbot.valuation.reverse_dcf import reverse_dcf_implied_growth


def _equity_value_from_growth(
    growth_rate: float,
    revenue_last_year: float,
    target_fcf_margin: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
    net_debt: float,
) -> float:
    revenue = revenue_last_year
    pv_fcf = 0.0

    for year in range(1, forecast_years + 1):
        revenue *= 1.0 + growth_rate
        fcf = revenue * target_fcf_margin
        pv_fcf += fcf / ((1.0 + wacc) ** year)

    terminal_fcf = revenue * target_fcf_margin * (1.0 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    enterprise_value = pv_fcf + terminal_value / ((1.0 + wacc) ** forecast_years)
    return enterprise_value - net_debt


def test_reverse_dcf_converges_to_known_growth_rate() -> None:
    true_growth = 0.12
    shares_outstanding = 100_000_000
    revenue_last_year = 5_000_000_000
    target_fcf_margin = 0.20
    wacc = 0.09
    terminal_growth = 0.03
    forecast_years = 10
    net_debt = 1_000_000_000

    market_cap = _equity_value_from_growth(
        growth_rate=true_growth,
        revenue_last_year=revenue_last_year,
        target_fcf_margin=target_fcf_margin,
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        net_debt=net_debt,
    )
    current_price = market_cap / shares_outstanding

    result = reverse_dcf_implied_growth(
        current_price=current_price,
        shares_outstanding=shares_outstanding,
        revenue_last_year=revenue_last_year,
        target_fcf_margin=target_fcf_margin,
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        net_debt=net_debt,
    )

    assert math.isclose(result["implied_revenue_growth"], true_growth, abs_tol=1e-5)
    assert math.isclose(result["equity_value"], result["market_cap"], rel_tol=1e-7)
    assert result["enterprise_value"] > result["equity_value"]
    assert result["forecast_years"] == forecast_years
