from __future__ import annotations

import csv
from typing import Any

_REQUIRED_COLUMNS = [
    "Navn",
    "Valuta",
    "Antal",
    "GAK",
    "Seneste kurs",
    "Værdi",
    "Værdi DKK",
    "Ureal.afkast %",
    "Afkast DKK",
]


def _parse_danish_float(value: str | None) -> float | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    # Handle common Danish formatting, e.g. "1.234,56" and "1 234,56".
    cleaned = cleaned.replace(" ", "").replace(".", "").replace(",", ".")
    return float(cleaned)


def load_nordnet_holdings_from_report(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-16", newline="") as report_file:
        reader = csv.DictReader(report_file, delimiter="\t")
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in _REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise ValueError(
                "Nordnet report is missing required columns: " + ", ".join(missing_columns)
            )

        holdings: list[dict[str, Any]] = []
        for row in reader:
            holdings.append(
                {
                    "platform": "nordnet",
                    "name": (row.get("Navn") or "").strip(),
                    "currency": (row.get("Valuta") or "").strip(),
                    "quantity": _parse_danish_float(row.get("Antal")),
                    "avg_price": _parse_danish_float(row.get("GAK")),
                    "current_price": _parse_danish_float(row.get("Seneste kurs")),
                    "market_value": _parse_danish_float(row.get("Værdi")),
                    "market_value_dkk": _parse_danish_float(row.get("Værdi DKK")),
                    "gain_pct": _parse_danish_float(row.get("Ureal.afkast %")),
                    "gain_dkk": _parse_danish_float(row.get("Afkast DKK")),
                    "ticker": None,
                }
            )

    return holdings
