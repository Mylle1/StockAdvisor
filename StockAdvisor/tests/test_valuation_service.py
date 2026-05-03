import pytest

from stockbot.fundamentals.models import Fundamentals
from stockbot.valuation.service import valuate_stock

DCF_PARAMS = {
    "revenue_growth": 0.08,
    "target_fcf_margin": 0.2,
    "forecast_years": 10,
}

REVERSE_DCF_PARAMS = {
    "target_fcf_margin": 0.2,
    "wacc": 0.1,
    "forecast_years": 10,
}


def test_valuate_stock_selects_dcf_and_returns_required_fields() -> None:
    fundamentals = Fundamentals(
        ticker="AAPL",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=0.1,
        fcf_margin=0.2,
    )

    result = valuate_stock(
        ticker="AAPL",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert result["ticker"] == "AAPL"
    assert result["model_used"] == "dcf"
    assert "fair_value_per_share" in result
    assert "upside_pct" in result


def test_valuate_stock_selects_reverse_dcf_and_returns_required_fields() -> None:
    fundamentals = Fundamentals(
        ticker="SHOP",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=0.30,
        fcf_margin=0.1,
    )

    result = valuate_stock(
        ticker="SHOP",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert result["ticker"] == "SHOP"
    assert result["model_used"] == "reverse_dcf"
    assert "implied_revenue_growth" in result


def test_valuate_stock_model_override_is_respected() -> None:
    fundamentals = Fundamentals(
        ticker="MSFT",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=0.30,
        fcf_margin=0.2,
    )

    result = valuate_stock(
        ticker="MSFT",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
        model_override="dcf",
    )

    assert result["model_used"] == "dcf"
    assert "fair_value_per_share" in result


def test_valuate_stock_estimates_wacc_for_dcf_path(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured["wacc"] = kwargs["wacc"]
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)

    fundamentals = Fundamentals(
        ticker="ORCL",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=0.16,
        fcf_margin=0.2,
    )

    valuate_stock(
        ticker="ORCL",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["wacc"] == 0.11


def test_valuate_stock_estimates_terminal_growth_from_country_for_dcf(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured["terminal_growth"] = kwargs["terminal_growth"]
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)

    fundamentals = Fundamentals(
        ticker="INFY",
        revenue_last_year=1000,
        shares_outstanding=100,
        country="India",
        net_debt=0,
        revenue_growth_5y=0.10,
        fcf_margin=0.2,
    )

    valuate_stock(
        ticker="INFY",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["terminal_growth"] == 0.035


def test_valuate_stock_estimates_terminal_growth_from_country_for_reverse_dcf(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_reverse_dcf_implied_growth(**kwargs):
        captured["terminal_growth"] = kwargs["terminal_growth"]
        return {"implied_revenue_growth": 0.2}

    monkeypatch.setattr("stockbot.valuation.service.reverse_dcf_implied_growth", fake_reverse_dcf_implied_growth)

    fundamentals = Fundamentals(
        ticker="SAP",
        revenue_last_year=1000,
        shares_outstanding=100,
        country="Germany",
        net_debt=0,
        revenue_growth_5y=0.30,
        fcf_margin=0.1,
    )

    valuate_stock(
        ticker="SAP",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["terminal_growth"] == 0.025


def test_valuate_stock_blends_quarterly_and_historical_growth_for_dcf(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured["revenue_growth"] = kwargs["revenue_growth"]
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)

    fundamentals = Fundamentals(
        ticker="NOW",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=0.10,
        recent_quarterly_yoy_revenue_growth=0.20,
        fcf_margin=0.2,
    )

    valuate_stock(
        ticker="NOW",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["revenue_growth"] == pytest.approx(0.14)


def test_valuate_stock_uses_available_revenue_growth_input_for_dcf(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured["revenue_growth"] = kwargs["revenue_growth"]
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)

    fundamentals = Fundamentals(
        ticker="CRM",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=None,
        recent_quarterly_yoy_revenue_growth=0.22,
        fcf_margin=0.2,
    )

    valuate_stock(
        ticker="CRM",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["revenue_growth"] == pytest.approx(0.22)


def test_valuate_stock_defaults_revenue_growth_for_dcf_when_missing(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured["revenue_growth"] = kwargs["revenue_growth"]
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)

    fundamentals = Fundamentals(
        ticker="IBM",
        revenue_last_year=1000,
        shares_outstanding=100,
        net_debt=0,
        revenue_growth_5y=None,
        recent_quarterly_yoy_revenue_growth=None,
        fcf_margin=0.2,
    )

    valuate_stock(
        ticker="IBM",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=DCF_PARAMS,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
    )

    assert captured["revenue_growth"] == pytest.approx(0.05)


def test_valuate_stock_passes_expected_arguments_to_two_stage_dcf(monkeypatch) -> None:
    captured: dict[str, float] = {}

    def fake_two_stage_dcf(**kwargs):
        captured.update(kwargs)
        return {"fair_value_per_share": 200.0, "upside_pct": 0.1}

    monkeypatch.setattr("stockbot.valuation.service.two_stage_dcf", fake_two_stage_dcf)
    monkeypatch.setattr("stockbot.valuation.service.estimate_wacc", lambda _growth: 0.123)
    monkeypatch.setattr("stockbot.valuation.service.estimate_terminal_growth", lambda _country: 0.027)

    fundamentals = Fundamentals(
        ticker="AAPL",
        revenue_last_year=1234.0,
        shares_outstanding=555.0,
        net_debt=77.0,
        revenue_growth_5y=0.10,
        recent_quarterly_yoy_revenue_growth=0.20,
        fcf_margin=0.25,
        country="USA",
    )

    dcf_params = {"target_fcf_margin": 0.30, "forecast_years": 7}

    valuate_stock(
        ticker="AAPL",
        current_price=180.0,
        fundamentals=fundamentals,
        dcf_params=dcf_params,
        reverse_dcf_params=REVERSE_DCF_PARAMS,
        model_override="dcf",
    )

    assert captured == {
        "current_price": 180.0,
        "revenue_last_year": 1234.0,
        "revenue_growth": pytest.approx(0.14),
        "target_fcf_margin": 0.30,
        "wacc": 0.123,
        "terminal_growth": 0.027,
        "forecast_years": 7,
        "net_debt": 77.0,
        "shares_outstanding": 555.0,
    }
