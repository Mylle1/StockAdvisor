from __future__ import annotations

from stockbot.portfolio.ticker_mapping import apply_ticker_mapping


def test_apply_ticker_mapping_returns_updated_holdings_and_unmapped_names() -> None:
    holdings = [
        {"name": "ASML Holding", "ticker": None},
        {"name": "Duolingo A", "ticker": None},
        {"name": "Unknown Co", "ticker": None},
    ]
    mapping = {
        "ASML Holding": "ASML",
        "Duolingo A": "DUOL",
    }

    updated_holdings, unmapped = apply_ticker_mapping(holdings, mapping)

    assert updated_holdings[0]["ticker"] == "ASML"
    assert updated_holdings[1]["ticker"] == "DUOL"
    assert updated_holdings[2]["ticker"] is None
    assert unmapped == ["Unknown Co"]
