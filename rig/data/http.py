"""Small retrying HTTP helper shared by the market-data downloaders.

Errors never include request headers, so API keys sent in headers can't leak.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

RETRY_STATUSES = {429, 500, 502, 503, 504}


class DataFetchError(RuntimeError):
    pass


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    attempts: int = 4,
    backoff_s: float = 2.0,
    timeout_s: float = 30.0,
    **kwargs: Any,
) -> Any:
    last = ""
    for attempt in range(1, attempts + 1):
        try:
            resp = session.request(method, url, timeout=timeout_s, **kwargs)
        except requests.RequestException as exc:
            last = type(exc).__name__
        else:
            if resp.status_code == 200:
                return resp.json()
            last = f"HTTP {resp.status_code}"
            if resp.status_code not in RETRY_STATUSES:
                break
        if attempt < attempts:
            wait = backoff_s * 2 ** (attempt - 1)
            log.info("%s %s failed (%s); retrying in %.0fs", method, url, last, wait)
            time.sleep(wait)
    raise DataFetchError(f"{method} {url} failed: {last}")
