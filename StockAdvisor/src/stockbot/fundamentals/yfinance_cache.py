from __future__ import annotations

from pathlib import Path

import yfinance as yf

_CONFIGURED = False


def configure_yfinance_cache() -> None:
    global _CONFIGURED

    if _CONFIGURED:
        return

    cache_dir = Path(__file__).resolve().parents[3] / ".tmp" / "yfinance-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))
    _CONFIGURED = True
