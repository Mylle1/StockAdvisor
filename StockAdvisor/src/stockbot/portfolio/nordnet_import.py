from __future__ import annotations

from stockbot.portfolio.holding import Holding


def load_nordnet_holdings_from_csv(path: str) -> list[Holding]:
    """Load Nordnet holdings from CSV.

    Expected columns (minimum):
    - ticker
    - name
    - quantity
    - currency
    - provider_id
    """
    raise NotImplementedError("Nordnet CSV import is not implemented yet.")
