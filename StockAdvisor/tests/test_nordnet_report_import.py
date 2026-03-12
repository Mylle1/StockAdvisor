from __future__ import annotations

from stockbot.portfolio.nordnet_report_import import load_nordnet_holdings_from_report


def test_load_nordnet_holdings_from_report_parses_utf16_and_decimal_comma(tmp_path) -> None:
    report_path = tmp_path / "nordnet_report.tsv"
    report_content = (
        "Navn\tValuta\tAntal\tGAK\tSeneste kurs\tVærdi\tVærdi DKK\tUreal.afkast %\tAfkast DKK\n"
        "ASML Holding\tUSD\t10,5\t836,88\t910,15\t9.556,58\t65.123,45\t8,76\t4.321,00\n"
    )
    report_path.write_text(report_content, encoding="utf-16")

    holdings = load_nordnet_holdings_from_report(str(report_path))

    assert len(holdings) == 1
    holding = holdings[0]
    assert holding["platform"] == "nordnet"
    assert holding["name"] == "ASML Holding"
    assert holding["currency"] == "USD"
    assert holding["quantity"] == 10.5
    assert holding["avg_price"] == 836.88
    assert holding["current_price"] == 910.15
    assert holding["market_value"] == 9556.58
    assert holding["market_value_dkk"] == 65123.45
    assert holding["gain_pct"] == 8.76
    assert holding["gain_dkk"] == 4321.0
    assert holding["ticker"] is None
