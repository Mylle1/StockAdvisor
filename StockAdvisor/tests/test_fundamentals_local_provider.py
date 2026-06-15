import json
from pathlib import Path

from stockbot.fundamentals.local_provider import load_fundamentals_from_json


def test_load_fundamentals_from_json() -> None:
    test_data_dir = Path("tests/.tmp_fundamentals")
    test_data_dir.mkdir(exist_ok=True)
    fundamentals_file = test_data_dir / "fundamentals.json"
    fundamentals_file.write_text(
        json.dumps(
            {
                "AAPL": {
                    "revenue_last_year": 1000,
                    "shares_outstanding": 100,
                    "net_debt": 0,
                    "revenue_growth_5y": 0.10,
                    "recent_quarterly_yoy_revenue_growth": 0.15,
                    "fcf_margin": 0.22,
                    "country": "United States",
                },
                "MSFT": {
                    "revenue_last_year": 1200,
                    "shares_outstanding": 80,
                },
            }
        ),
        encoding="utf-8",
    )

    data = load_fundamentals_from_json(str(fundamentals_file))

    assert set(data.keys()) == {"AAPL", "MSFT"}
    assert data["AAPL"].ticker == "AAPL"
    assert data["AAPL"].revenue_growth_5y == 0.10
    assert data["AAPL"].recent_quarterly_yoy_revenue_growth == 0.15
    assert data["AAPL"].country == "United States"
    assert data["MSFT"].net_debt == 0.0
    assert data["MSFT"].fcf_margin is None
