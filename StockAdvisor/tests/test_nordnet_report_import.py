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


def test_load_nordnet_holdings_from_report_skips_non_stock_products(tmp_path) -> None:
    report_path = tmp_path / "nordnet_report.tsv"
    report_content = (
        "Navn\tValuta\tAntal\tGAK\tSeneste kurs\tVÃ¦rdi\tVÃ¦rdi DKK\tUreal.afkast %\tAfkast DKK\n"
        "Alibaba Group ADR\tUSD\t15\t89,4667\t134,34\t2015,1\t12957,093\t38,8\t3621,9668895\n"
        "Amundi Prime All Country World UCITS ETF Acc\tEUR\t367\t11,1955\t12,32\t4521,44\t33787,4757138\t9,81\t3019,0747005\n"
        "iShares Core MSCI Europe UCITS ETF EUR (Acc)\tEUR\t29\t87,541\t99,8\t2894,2\t21627,5594082\t13,85\t2630,7690337\n"
        "Netcompany\tDKK\t51\t265,8059\t338,2\t17248,2\t17248,2\t27,24\t3692,1\n"
    )
    report_path.write_text(report_content, encoding="utf-16")

    holdings = load_nordnet_holdings_from_report(str(report_path))

    assert [holding["name"] for holding in holdings] == [
        "Alibaba Group ADR",
        "Netcompany",
    ]
