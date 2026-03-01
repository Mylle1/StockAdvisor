from __future__ import annotations

from stockbot.saxo.client import SaxoClient


def get_accounts(client: SaxoClient):
    return client.get("/port/v1/accounts/me")


def get_positions(client: SaxoClient):
    return client.get("/port/v1/positions/me")
