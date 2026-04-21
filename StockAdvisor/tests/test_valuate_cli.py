import json
from argparse import Namespace

from stockbot.cli.valuate import (
    DEFAULT_DCF_PARAMS,
    DEFAULT_REVERSE_DCF_PARAMS,
    _build_valuation_params,
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
        "stockbot.cli.valuate._load_price_lookup_from_holdings",
        lambda _path: {"AAPL": 180.0},
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
