from stockbot.valuation.model_selector import estimate_terminal_growth, estimate_wacc, select_valuation_model


def test_selects_reverse_dcf_for_high_revenue_growth() -> None:
    assert select_valuation_model(revenue_growth_5y=0.28, fcf_margin=None) == "reverse_dcf"


def test_selects_dcf_at_revenue_growth_threshold() -> None:
    assert select_valuation_model(revenue_growth_5y=0.27, fcf_margin=None) == "dcf"


def test_selects_reverse_dcf_for_low_fcf_margin() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.03) == "reverse_dcf"


def test_selects_dcf_at_fcf_margin_threshold() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.05) == "dcf"


def test_selects_dcf_when_both_inputs_missing() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=None) == "dcf"


def test_selects_dcf_when_only_healthy_fcf_margin_present() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.10) == "dcf"


def test_estimate_wacc_at_or_above_high_growth_bucket() -> None:
    assert estimate_wacc(0.27) == 0.13


def test_estimate_wacc_at_or_above_mid_growth_bucket() -> None:
    assert estimate_wacc(0.15) == 0.11


def test_estimate_wacc_at_or_above_low_growth_bucket() -> None:
    assert estimate_wacc(0.05) == 0.095


def test_estimate_wacc_for_very_low_growth() -> None:
    assert estimate_wacc(0.01) == 0.08


def test_estimate_terminal_growth_for_developed_market() -> None:
    assert estimate_terminal_growth("Germany") == 0.025


def test_estimate_terminal_growth_for_other_market() -> None:
    assert estimate_terminal_growth("India") == 0.035


def test_estimate_terminal_growth_for_missing_country() -> None:
    assert estimate_terminal_growth(None) == 0.035
