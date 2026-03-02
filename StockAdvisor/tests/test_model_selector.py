from stockbot.valuation.model_selector import select_valuation_model


def test_selects_reverse_dcf_for_high_revenue_growth() -> None:
    assert select_valuation_model(revenue_growth_5y=0.20, fcf_margin=None) == "reverse_dcf"


def test_selects_dcf_at_revenue_growth_threshold() -> None:
    assert select_valuation_model(revenue_growth_5y=0.15, fcf_margin=None) == "dcf"


def test_selects_reverse_dcf_for_low_fcf_margin() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.03) == "reverse_dcf"


def test_selects_dcf_at_fcf_margin_threshold() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.05) == "dcf"


def test_selects_dcf_when_both_inputs_missing() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=None) == "dcf"


def test_selects_dcf_when_only_healthy_fcf_margin_present() -> None:
    assert select_valuation_model(revenue_growth_5y=None, fcf_margin=0.10) == "dcf"
