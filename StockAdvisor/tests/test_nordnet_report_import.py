from __future__ import annotations

from pathlib import Path

import pytest

from stockbot.portfolio.nordnet_report_import import load_nordnet_holdings_from_report


def test_load_nordnet_holdings_from_report_parses_utf16_tab_file(tmp_path: Path) -> None:
    report_content = (
        "Navn\tValuta\tAntal\tGAK\tSeneste kurs\tVærdi DKK\n"
        "Apple Inc\tUSD\t10\t836,88\t900,50\t6.543,21\n"
        "Novo Nordisk A/S\tDKK\t3,5\t741,20\t800,00\t2.800,00\n"
    )
    report_path = tmp_path / "nordnet_report.tsv"
    report_path.write_text(report_content, encoding="utf-16")

    holdings = load_nordnet_holdings_from_report(str(report_path))

    assert len(holdings) == 2
    assert holdings[0] == {
        "platform": "nordnet",
        "name": "Apple Inc",
        "currency": "USD",
        "quantity": 10.0,
        "avg_price": pytest.approx(836.88),
        "current_price": pytest.approx(900.50),
        "market_value_dkk": pytest.approx(6543.21),
        "ticker": None,
    }
    assert holdings[1]["quantity"] == pytest.approx(3.5)
    assert holdings[1]["avg_price"] == pytest.approx(741.20)
    assert holdings[1]["current_price"] == pytest.approx(800.00)
    assert holdings[1]["market_value_dkk"] == pytest.approx(2800.00)


def test_load_nordnet_holdings_from_report_raises_for_missing_columns(tmp_path: Path) -> None:
    report_content = (
        "Navn\tValuta\tAntal\tGAK\n"
        "Apple Inc\tUSD\t10\t836,88\n"
    )
    report_path = tmp_path / "invalid.tsv"
    report_path.write_text(report_content, encoding="utf-16")

    with pytest.raises(ValueError, match="Missing required Nordnet report columns"):
        load_nordnet_holdings_from_report(str(report_path))


def test_load_nordnet_holdings_from_report_normalizes_currency(tmp_path: Path) -> None:
    report_content = (
        "Navn\tValuta\tAntal\tGAK\tSeneste kurs\n"
        "ASML Holding\t eur \t1\t100,00\t110,00\n"
    )
    report_path = tmp_path / "currency.tsv"
    report_path.write_text(report_content, encoding="utf-16")

    holdings = load_nordnet_holdings_from_report(str(report_path))

    assert holdings[0]["currency"] == "EUR"
