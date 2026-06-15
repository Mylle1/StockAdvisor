from __future__ import annotations

import json
from pathlib import Path

from stockbot.fundamentals.models import Fundamentals
import stockbot.api as api


def test_run_valuations_generates_fundamentals_before_valuation(monkeypatch) -> None:
    test_data_dir = Path("tests/.tmp_api_pipeline")
    test_data_dir.mkdir(exist_ok=True)
    mapped_holdings_path = test_data_dir / "holdings_mapped.json"
    fundamentals_path = test_data_dir / "fundamentals.json"
    if fundamentals_path.exists():
        fundamentals_path.unlink()

    mapped_holdings_path.write_text(
        json.dumps(
            [
                {
                    "name": "Example Co",
                    "ticker": "EXM",
                    "currency": "USD",
                    "current_price": 10.0,
                },
                {
                    "name": "Nordic Co",
                    "ticker": "NDC",
                    "currency": "NOK",
                    "current_price": 20.0,
                }
            ]
        ),
        encoding="utf-8",
    )

    class FakeProvider:
        def get_fundamentals(self, ticker: str) -> Fundamentals:
            if ticker == "NDC":
                return Fundamentals(
                    ticker=ticker,
                    revenue_last_year=500_000_000,
                    shares_outstanding=100,
                    net_debt=0,
                    revenue_growth_5y=0.02,
                    fcf_margin=0.08,
                )
            return Fundamentals(
                ticker=ticker,
                revenue_last_year=1000,
                shares_outstanding=100,
                net_debt=0,
                revenue_growth_5y=0.1,
                fcf_margin=0.2,
            )

    monkeypatch.setattr(api, "HOLDINGS_MAPPED_PATH", mapped_holdings_path)
    monkeypatch.setattr(api, "FUNDAMENTALS_PATH", fundamentals_path)
    monkeypatch.setattr(api, "YFinanceFundamentalsProvider", lambda: FakeProvider())

    result = api.run_valuations()

    assert result["errors"] == []
    assert [row["ticker"] for row in result["results"]] == ["EXM", "NDC"]
    assert (
        result["results"][0]["assumptions"]["wacc"]
        != result["results"][1]["assumptions"]["wacc"]
    )
    assert (
        result["results"][0]["assumptions"]["revenueGrowth"]
        != result["results"][1]["assumptions"]["revenueGrowth"]
    )
    assert fundamentals_path.exists()
    saved_fundamentals = json.loads(fundamentals_path.read_text(encoding="utf-8"))
    assert saved_fundamentals["EXM"]["revenue_last_year"] == 1000
    assert saved_fundamentals["NDC"]["revenue_last_year"] == 500_000_000
