from __future__ import annotations

import csv


REQUIRED_COLUMNS = ["Navn", "Valuta", "Antal", "GAK", "Seneste kurs"]
OPTIONAL_COLUMNS = ["Værdi DKK"]


def _parse_danish_number(value: str, field_name: str) -> float:
    raw = value.strip()
    if not raw:
        raise ValueError(f"Field '{field_name}' is empty and cannot be parsed as a number.")

    normalized = raw.replace("\xa0", "").replace(" ", "")

    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    else:
        normalized = normalized.replace(",", "")

    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse numeric value '{value}' for field '{field_name}'."
        ) from exc


def _parse_optional_danish_number(value: str | None, field_name: str) -> float | None:
    if value is None:
        return None
    if not value.strip():
        return None
    return _parse_danish_number(value, field_name)


def load_nordnet_holdings_from_report(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-16", newline="") as report_file:
        reader = csv.DictReader(report_file, delimiter="\t")

        if reader.fieldnames is None:
            raise ValueError("Nordnet report appears empty or missing header row.")

        missing_required = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_required:
            raise ValueError(
                "Missing required Nordnet report columns: " + ", ".join(missing_required)
            )

        holdings: list[dict] = []
        for row in reader:
            holdings.append(
                {
                    "platform": "nordnet",
                    "name": row["Navn"],
                    "currency": row["Valuta"].strip().upper(),
                    "quantity": _parse_danish_number(row["Antal"], "Antal"),
                    "avg_price": _parse_danish_number(row["GAK"], "GAK"),
                    "current_price": _parse_danish_number(
                        row["Seneste kurs"], "Seneste kurs"
                    ),
                    "market_value_dkk": _parse_optional_danish_number(
                        row.get("Værdi DKK"), "Værdi DKK"
                    ),
                    "ticker": None,
                }
            )

    return holdings
