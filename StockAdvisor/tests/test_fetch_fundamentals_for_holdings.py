from __future__ import annotations

import json

from stockbot.cli.fetch_fundamentals_for_holdings import main
from stockbot.fundamentals.models import Fundamentals


def test_cli_skips_holdings_without_ticker(tmp_path, monkeypatch, capsys) -> None:
    holdings_file = tmp_path / "holdings.json"
    output_file = tmp_path / "fundamentals.json"

    holdings_file.write_text(
        json.dumps(
            [
                {"name": "No ticker 1", "ticker": ""},
                {"name": "No ticker 2", "ticker": None},
                {"name": "ASML Holding", "ticker": "ASML"},
            ]
        ),
        encoding="utf-8",
    )

    def fake_get_fundamentals(self, ticker: str) -> Fundamentals:
        return Fundamentals(
            ticker=ticker,
            revenue_last_year=100.0,
            shares_outstanding=10.0,
            net_debt=5.0,
            revenue_growth_5y=0.1,
            fcf_margin=0.2,
        )

    monkeypatch.setattr(
        "stockbot.fundamentals.yfinance_provider.YahooFundamentalsProvider.get_fundamentals",
        fake_get_fundamentals,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch_fundamentals_for_holdings",
            "--holdings",
            str(holdings_file),
            "--out",
            str(output_file),
        ],
    )

    main()

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert set(output_data.keys()) == {"ASML"}

    stdout = capsys.readouterr().out
    assert "Total holdings: 3" in stdout
    assert "Fetched fundamentals: 1" in stdout
    assert "Skipped missing ticker: 2" in stdout
    assert "Failed fetch: 0" in stdout


def test_cli_records_provider_failures(tmp_path, monkeypatch, capsys) -> None:
    holdings_file = tmp_path / "holdings.json"
    output_file = tmp_path / "fundamentals.json"

    holdings_file.write_text(
        json.dumps(
            [
                {"name": "ASML Holding", "ticker": "ASML"},
                {"name": "Duolingo", "ticker": "DUOL"},
            ]
        ),
        encoding="utf-8",
    )

    def fake_get_fundamentals(self, ticker: str) -> Fundamentals:
        if ticker == "DUOL":
            raise ValueError("Missing shares outstanding for ticker 'DUOL'")

        return Fundamentals(
            ticker=ticker,
            revenue_last_year=100.0,
            shares_outstanding=10.0,
            net_debt=5.0,
            revenue_growth_5y=0.1,
            fcf_margin=0.2,
        )

    monkeypatch.setattr(
        "stockbot.fundamentals.yfinance_provider.YahooFundamentalsProvider.get_fundamentals",
        fake_get_fundamentals,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch_fundamentals_for_holdings",
            "--holdings",
            str(holdings_file),
            "--out",
            str(output_file),
        ],
    )

    main()

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert set(output_data.keys()) == {"ASML"}

    stdout = capsys.readouterr().out
    assert "Failed fetch: 1" in stdout
    assert "- DUOL: Missing shares outstanding for ticker 'DUOL'" in stdout
