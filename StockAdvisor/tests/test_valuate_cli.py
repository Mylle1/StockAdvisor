import json
from argparse import Namespace

from stockbot.cli.valuate import (
    DEFAULT_DCF_PARAMS,
    DEFAULT_REVERSE_DCF_PARAMS,
    _build_valuation_params,
    _load_price_lookup_from_holdings,
)


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
