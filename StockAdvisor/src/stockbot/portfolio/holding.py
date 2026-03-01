from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Holding(BaseModel):
    platform: Literal["saxo", "nordnet"]
    ticker: str
    name: str | None = None
    quantity: float
    currency: str | None = None
    provider_id: str | int | None = None
