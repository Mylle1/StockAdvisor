from typing import Literal


def select_valuation_model(
    revenue_growth: float | None,
    fcf_margin: float | None,
) -> Literal["dcf", "reverse_dcf"]:
    """Select a valuation model based on growth and profitability signals.

    High calculated revenue growth indicates a growth-case where reverse DCF is
    often a better framing. Negative calculated revenue growth or low/negative
    free-cash-flow margin suggests unstable profitability, which also points to
    reverse DCF. Otherwise, the company is treated as relatively stable and a
    classic DCF is used.
    """
    if revenue_growth is not None and revenue_growth < 0:
        return "reverse_dcf"
    if revenue_growth is not None and revenue_growth > 0.27:
        return "reverse_dcf"
    if fcf_margin is not None and fcf_margin < 0.05:
        return "reverse_dcf"
    return "dcf"
