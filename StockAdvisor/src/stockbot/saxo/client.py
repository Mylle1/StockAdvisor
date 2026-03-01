from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from stockbot.config.settings import settings


@dataclass
class SaxoClient:
    timeout: int = 20

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.saxo_access_token}",
            "Accept": "application/json",
        }

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = settings.saxo_base_url.rstrip("/") + "/" + path.lstrip("/")
        r = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)

        if not r.ok:
            raise RuntimeError(f"GET {url} failed: {r.status_code} {r.text}")

        return r.json()
