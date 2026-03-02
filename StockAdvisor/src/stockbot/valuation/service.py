from __future__ import annotations

from stockbot.fundamentals.models import Fundamentals
from stockbot.valuation.dcf import two_stage_dcf
from stockbot.valuation.model_selector import select_valuation_model
from stockbot.valuation.reverse_dcf import reverse_dcf_implied_growth


def valuate_stock(
    ticker: str,
    current_price: float,
    fundamentals: Fundamentals,
    dcf_params: dict,
    reverse_dcf_params: dict,
    model_override: str | None = None,
) -> dict:
    model_used = model_override or select_valuation_model(
        fundamentals.revenue_growth_5y,
        fundamentals.fcf_margin,
    )

    if model_used == "dcf":
        dcf_result = two_stage_dcf(
            current_price=current_price,
            revenue_last_year=fundamentals.revenue_last_year,
            revenue_growth=dcf_params["revenue_growth"],
            target_fcf_margin=dcf_params["target_fcf_margin"],
            wacc=dcf_params["wacc"],
            terminal_growth=dcf_params["terminal_growth"],
            forecast_years=dcf_params.get("forecast_years", 10),
            net_debt=fundamentals.net_debt,
            shares_outstanding=fundamentals.shares_outstanding,
        )
        return {
            "ticker": ticker,
            "model_used": "dcf",
            "current_price": current_price,
            "fair_value_per_share": dcf_result["fair_value_per_share"],
            "upside_pct": dcf_result["upside_pct"],
        }

    if model_used == "reverse_dcf":
        reverse_result = reverse_dcf_implied_growth(
            current_price=current_price,
            shares_outstanding=fundamentals.shares_outstanding,
            revenue_last_year=fundamentals.revenue_last_year,
            target_fcf_margin=reverse_dcf_params["target_fcf_margin"],
            wacc=reverse_dcf_params["wacc"],
            terminal_growth=reverse_dcf_params["terminal_growth"],
            forecast_years=reverse_dcf_params.get("forecast_years", 10),
            net_debt=fundamentals.net_debt,
        )
        return {
            "ticker": ticker,
            "model_used": "reverse_dcf",
            "current_price": current_price,
            "implied_revenue_growth": reverse_result["implied_revenue_growth"],
        }

    raise ValueError(f"Unsupported model override: {model_used}")
