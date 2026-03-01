from __future__ import annotations

from stockbot.saxo.client import SaxoClient


def get_accounts(client: SaxoClient):
    return client.get("/port/v1/accounts/me")


def get_positions(client: SaxoClient):
    return client.get("/port/v1/positions/me")


def get_watchlists(client: SaxoClient):
    return client.get("/port/v1/watchlists")


def get_watchlist(client: SaxoClient, watchlist_id: str):
    return client.get(f"/port/v1/watchlists/{watchlist_id}")
