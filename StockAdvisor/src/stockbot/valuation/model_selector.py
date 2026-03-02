from typing import Literal


def select_valuation_model(
    revenue_growth_5y: float | None,
    fcf_margin: float | None,
) -> Literal["dcf", "reverse_dcf"]:
    """Select a valuation model based on growth and profitability signals.

    High historical revenue growth indicates a growth-case where reverse DCF is
    often a better framing. Low or negative free-cash-flow margin suggests a
    growth profile or unstable profitability, which also points to reverse DCF.
    Otherwise, the company is treated as relatively stable and a classic DCF is
    used.
    """
    if revenue_growth_5y is not None and revenue_growth_5y > 0.15:
        return "reverse_dcf"
    if fcf_margin is not None and fcf_margin < 0.05:
        return "reverse_dcf"
    return "dcf"
