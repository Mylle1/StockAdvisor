from __future__ import annotations

import json

from stockbot.fundamentals.models import Fundamentals


def test_fetch_fundamentals_for_holdings_handles_success_skip_and_fail(
    tmp_path, monkeypatch, capsys
) -> None:
    from stockbot.cli import fetch_fundamentals_for_holdings as cli

    holdings_path = tmp_path / "nordnet_holdings_mapped.json"
    out_path = tmp_path / "fundamentals_from_holdings.json"

    holdings_path.write_text(
        json.dumps(
            [
                {"name": "ASML Holding", "ticker": "ASML"},
                {"name": "No ticker", "ticker": ""},
                {"name": "Broken ticker", "ticker": "BROKEN"},
            ]
        ),
        encoding="utf-8",
    )

    class FakeProvider:
        def __init__(self, api_key: str):
            assert api_key == "demo"

        def get_fundamentals(self, ticker: str) -> Fundamentals:
            if ticker == "BROKEN":
                raise RuntimeError("upstream failure")
            return Fundamentals(
                ticker=ticker,
                revenue_last_year=123.45,
                shares_outstanding=1000,
                net_debt=50.0,
                revenue_growth_5y=0.12,
                fcf_margin=0.18,
            )

    monkeypatch.setattr(cli, "FMPFundamentalsProvider", FakeProvider)

    monkeypatch.setenv("FMP_API_KEY", "demo")
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch_fundamentals_for_holdings",
            "--holdings",
            str(holdings_path),
            "--out",
            str(out_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "Total holdings: 3" in output
    assert "Fetched fundamentals: 1" in output
    assert "Skipped missing ticker: 1" in output
    assert "Failed fetch: 1" in output
    assert "- BROKEN" in output

    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert sorted(written.keys()) == ["ASML"]
    assert written["ASML"] == {
        "ticker": "ASML",
        "revenue_last_year": 123.45,
        "shares_outstanding": 1000,
        "net_debt": 50.0,
        "revenue_growth_5y": 0.12,
        "fcf_margin": 0.18,
    }
