import math

from stockbot.valuation.dcf import two_stage_dcf


def test_two_stage_dcf_with_dummy_inputs() -> None:
    current_price = 50
    revenue_last_year = 1000
    revenue_growth = 0.05
    target_fcf_margin = 0.20
    wacc = 0.08
    terminal_growth = 0.02
    forecast_years = 5
    net_debt = 100
    shares_outstanding = 100

    result = two_stage_dcf(
        current_price=current_price,
        revenue_last_year=revenue_last_year,
        revenue_growth=revenue_growth,
        target_fcf_margin=target_fcf_margin,
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        net_debt=net_debt,
        shares_outstanding=shares_outstanding,
    )

    assert result["fair_value_per_share"] > 0
    assert result["enterprise_value"] > result["equity_value"]

    expected_upside = (result["fair_value_per_share"] / current_price) - 1.0
    assert math.isclose(result["upside_pct"], expected_upside, rel_tol=1e-12)
