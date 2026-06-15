from __future__ import annotations

from stockbot.fundamentals.models import Fundamentals
import pytest

from stockbot.valuation.parameter_estimator import (
    estimate_dcf_revenue_growth,
    estimate_terminal_growth,
    estimate_valuation_params,
    estimate_wacc,
)


def test_estimate_valuation_params_uses_company_specific_inputs() -> None:
    stable = Fundamentals(
        ticker="STABLE",
        revenue_last_year=10_000_000_000,
        shares_outstanding=100,
        revenue_growth_5y=0.04,
        fcf_margin=0.18,
        country="United States",
    )
    growth = Fundamentals(
        ticker="GROWTH",
        revenue_last_year=500_000_000,
        shares_outstanding=100,
        revenue_growth_5y=0.25,
        recent_quarterly_yoy_revenue_growth=0.10,
        fcf_margin=-0.02,
        country="Brazil",
    )

    stable_params = estimate_valuation_params(stable, trading_currency="USD")
    growth_params = estimate_valuation_params(growth, trading_currency="NOK")

    assert stable_params["dcf"]["revenue_growth"] == 0.04
    assert growth_params["dcf"]["revenue_growth"] == pytest.approx(0.205)
    assert stable_params["dcf"]["target_fcf_margin"] == 0.18
    assert growth_params["dcf"]["target_fcf_margin"] == 0.05
    assert stable_params["dcf"]["wacc"] != growth_params["dcf"]["wacc"]
    assert stable_params["dcf"]["terminal_growth"] == 0.025
    assert growth_params["dcf"]["terminal_growth"] == 0.032


def test_estimate_wacc_uses_revenue_growth_step_model() -> None:
    assert estimate_wacc(0.28) == 0.12
    assert estimate_wacc(0.16) == 0.10
    assert estimate_wacc(0.06) == 0.085
    assert estimate_wacc(0.05) == 0.08
    assert estimate_wacc(None) == 0.08


def test_estimate_dcf_revenue_growth_blends_quarterly_and_historical_growth() -> None:
    assert estimate_dcf_revenue_growth(
        Fundamentals(
            ticker="BLEND",
            revenue_last_year=100,
            shares_outstanding=10,
            revenue_growth_5y=0.10,
            recent_quarterly_yoy_revenue_growth=0.20,
        )
    ) == pytest.approx(0.13)
    assert estimate_dcf_revenue_growth(
        Fundamentals(
            ticker="QUARTER",
            revenue_last_year=100,
            shares_outstanding=10,
            recent_quarterly_yoy_revenue_growth=0.20,
        )
    ) == 0.20
    assert estimate_dcf_revenue_growth(
        Fundamentals(
            ticker="HISTORICAL",
            revenue_last_year=100,
            shares_outstanding=10,
            revenue_growth_5y=0.10,
        )
    ) == 0.10
    assert estimate_dcf_revenue_growth(
        Fundamentals(ticker="DEFAULT", revenue_last_year=100, shares_outstanding=10)
    ) == 0.05


def test_estimate_terminal_growth_uses_developed_country_rule() -> None:
    assert estimate_terminal_growth("Denmark") == 0.025
    assert estimate_terminal_growth("United States") == 0.025
    assert estimate_terminal_growth("Brazil") == 0.032
    assert estimate_terminal_growth(None) == 0.032
