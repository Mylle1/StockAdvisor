import json
from argparse import Namespace

from stockbot.cli.valuate import (
    DEFAULT_DCF_PARAMS,
    DEFAULT_REVERSE_DCF_PARAMS,
    _build_valuation_params,
    _get_exchange_rate,
    _load_holding_lookup,
    _load_price_lookup_from_holdings,
    main,
)
from stockbot.fundamentals.models import Fundamentals


def test_load_price_lookup_from_holdings_uses_ticker_and_current_price(tmp_path) -> None:
    holdings_path = tmp_path / "nordnet_holdings_mapped.json"
    holdings_path.write_text(
        json.dumps(
            [
                {"ticker": "AAPL", "current_price": 180.5},
                {"ticker": "MSFT", "current_price": "420.10"},
                {"ticker": "NO_PRICE"},
                {"current_price": 123.0},
            ]
        ),
        encoding="utf-8",
    )

    prices = _load_price_lookup_from_holdings(str(holdings_path))

    assert prices == {"AAPL": 180.5, "MSFT": 420.1}


def test_load_holding_lookup_includes_currency(tmp_path) -> None:
    holdings_path = tmp_path / "nordnet_holdings_mapped.json"
    holdings_path.write_text(
        json.dumps([{"ticker": "TOM.OL", "current_price": "98.4", "currency": "nok"}]),
        encoding="utf-8",
    )

    holdings = _load_holding_lookup(str(holdings_path))

    assert holdings["TOM.OL"]["current_price"] == 98.4
    assert holdings["TOM.OL"]["currency"] == "NOK"


def test_get_exchange_rate_uses_override_without_fetching(monkeypatch) -> None:
    monkeypatch.setattr(
        "stockbot.cli.valuate._fetch_exchange_rate",
        lambda *_args: (_ for _ in ()).throw(AssertionError("should not fetch")),
    )

    rate = _get_exchange_rate("EUR", "NOK", {("EUR", "NOK"): 10.75})

    assert rate == 10.75


def test_build_valuation_params_uses_configured_values() -> None:
    dcf_params, reverse_dcf_params = _build_valuation_params(
        Namespace(target_fcf_margin=0.25, forecast_years=12)
    )

    assert dcf_params == {"target_fcf_margin": 0.25, "forecast_years": 12}
    assert reverse_dcf_params == {"target_fcf_margin": 0.25, "forecast_years": 12}


def test_default_params_only_include_margin_and_horizon() -> None:
    assert DEFAULT_DCF_PARAMS == {"target_fcf_margin": 0.2, "forecast_years": 10}
    assert DEFAULT_REVERSE_DCF_PARAMS == {"target_fcf_margin": 0.2, "forecast_years": 10}


def test_main_passes_fundamentals_to_service_for_dcf_growth_estimation(monkeypatch, capsys) -> None:
    fundamentals = Fundamentals(
        ticker="AAPL",
        revenue_last_year=1000.0,
        shares_outstanding=100.0,
        revenue_growth_5y=0.10,
        recent_quarterly_yoy_revenue_growth=0.30,
        fcf_margin=0.2,
    )

    monkeypatch.setattr(
        "stockbot.cli.valuate.load_fundamentals_from_json",
        lambda _path: {"AAPL": fundamentals},
    )
    monkeypatch.setattr(
        "stockbot.cli.valuate._load_holding_lookup",
        lambda _path: {"AAPL": {"ticker": "AAPL", "current_price": 180.0, "currency": "USD"}},
    )

    captured: dict[str, object] = {}

    def fake_valuate_stock(**kwargs):
        captured.update(kwargs)
        return {
            "ticker": "AAPL",
            "model_used": "dcf",
            "current_price": 180.0,
            "fair_value_per_share": 200.0,
            "upside_pct": 0.1111,
        }

    monkeypatch.setattr("stockbot.cli.valuate.valuate_stock", fake_valuate_stock)
    monkeypatch.setattr(
        "sys.argv",
        [
            "valuate",
            "--fundamentals",
            "fundamentals.json",
            "--holdings",
            "holdings.json",
            "--tickers",
            "AAPL",
            "--model-override",
            "dcf",
        ],
    )

    main()

    assert captured["fundamentals"] is fundamentals
    assert captured["dcf_params"] == {"target_fcf_margin": 0.2, "forecast_years": 10}

    output = capsys.readouterr().out
    assert "ticker" in output
    assert "AAPL" in output


def test_main_passes_expected_cli_params_to_valuation_service(monkeypatch) -> None:
    fundamentals = Fundamentals(
        ticker="AAPL",
        revenue_last_year=1000.0,
        shares_outstanding=100.0,
        revenue_growth_5y=0.12,
        recent_quarterly_yoy_revenue_growth=0.25,
        fcf_margin=0.2,
    )

    monkeypatch.setattr(
        "stockbot.cli.valuate.load_fundamentals_from_json",
        lambda _path: {"AAPL": fundamentals},
    )
    monkeypatch.setattr(
        "stockbot.cli.valuate._load_holding_lookup",
        lambda _path: {"AAPL": {"ticker": "AAPL", "current_price": 180.0, "currency": "USD"}},
    )
    monkeypatch.setattr("stockbot.cli.valuate.estimate_wacc", lambda growth: 0.09)

    captured: dict[str, object] = {}

    def fake_valuate_stock(**kwargs):
        captured.update(kwargs)
        return {
            "ticker": "AAPL",
            "model_used": "reverse_dcf",
            "current_price": 180.0,
            "fair_value_per_share": 200.0,
            "upside_pct": 0.1111,
            "implied_revenue_growth": 0.08,
        }

    monkeypatch.setattr("stockbot.cli.valuate.valuate_stock", fake_valuate_stock)
    monkeypatch.setattr(
        "sys.argv",
        [
            "valuate",
            "--fundamentals",
            "fundamentals.json",
            "--holdings",
            "holdings.json",
            "--tickers",
            "AAPL",
            "--target-fcf-margin",
            "0.3",
            "--forecast-years",
            "7",
            "--model-override",
            "reverse_dcf",
        ],
    )

    main()

    assert captured["ticker"] == "AAPL"
    assert captured["current_price"] == 180.0
    assert captured["fundamentals"] is fundamentals
    assert captured["dcf_params"] == {"target_fcf_margin": 0.3, "forecast_years": 7}
    assert captured["reverse_dcf_params"] == {
        "target_fcf_margin": 0.3,
        "forecast_years": 7,
        "wacc": 0.09,
    }
    assert captured["model_override"] == "reverse_dcf"


def test_main_converts_price_to_financial_currency_and_fair_value_back(monkeypatch, capsys) -> None:
    fundamentals = Fundamentals(
        ticker="TOM.OL",
        revenue_last_year=1000.0,
        shares_outstanding=100.0,
        revenue_growth_5y=0.05,
        fcf_margin=0.2,
        financial_currency="EUR",
    )

    monkeypatch.setattr(
        "stockbot.cli.valuate.load_fundamentals_from_json",
        lambda _path: {"TOM.OL": fundamentals},
    )
    monkeypatch.setattr(
        "stockbot.cli.valuate._load_holding_lookup",
        lambda _path: {"TOM.OL": {"ticker": "TOM.OL", "current_price": 100.0, "currency": "NOK"}},
    )
    monkeypatch.setattr("stockbot.cli.valuate.estimate_wacc", lambda growth: 0.09)

    captured: dict[str, object] = {}

    def fake_valuate_stock(**kwargs):
        captured.update(kwargs)
        return {
            "ticker": "TOM.OL",
            "model_used": "dcf",
            "current_price": kwargs["current_price"],
            "fair_value_per_share": 12.0,
            "upside_pct": 0.0,
        }

    monkeypatch.setattr("stockbot.cli.valuate.valuate_stock", fake_valuate_stock)
    monkeypatch.setattr(
        "sys.argv",
        [
            "valuate",
            "--fundamentals",
            "fundamentals.json",
            "--holdings",
            "holdings.json",
            "--tickers",
            "TOM.OL",
            "--exchange-rate",
            "NOK:EUR=0.085",
            "--exchange-rate",
            "EUR:NOK=11.7647",
        ],
    )

    main()

    assert captured["current_price"] == 8.5
    output = capsys.readouterr().out
    assert "TOM.OL" in output
    assert "NOK" in output
    assert "141.1764" in output
