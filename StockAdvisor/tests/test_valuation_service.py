from stockbot.fundamentals.models import Fundamentals
from stockbot.valuation.service import valuate_stock

DCF_PARAMS = {
    "revenue_growth": 0.08,
    "target_fcf_margin": 0.2,
    "wacc": 0.1,
    "terminal_growth": 0.03,
    "forecast_years": 10,
}

REVERSE_DCF_PARAMS = {
    "target_fcf_margin": 0.2,
    "wacc": 0.1,
    "terminal_growth": 0.03,
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
