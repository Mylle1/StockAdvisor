from __future__ import annotations

import json

from stockbot.fundamentals.models import Fundamentals


def load_fundamentals_from_json(path: str) -> dict[str, Fundamentals]:
    with open(path, encoding="utf-8") as file:
        raw_data = json.load(file)

    fundamentals_by_ticker: dict[str, Fundamentals] = {}
    for ticker, payload in raw_data.items():
        fundamentals_by_ticker[ticker] = Fundamentals(
            ticker=ticker,
            revenue_last_year=payload["revenue_last_year"],
            shares_outstanding=payload["shares_outstanding"],
            net_debt=payload.get("net_debt", 0.0),
            revenue_growth_5y=payload.get("revenue_growth_5y"),
            revenue_growth_years_used=payload.get("revenue_growth_years_used"),
            fcf_margin=payload.get("fcf_margin"),
        )

    return fundamentals_by_ticker
