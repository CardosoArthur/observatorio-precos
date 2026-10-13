"""Small HTTP helper: GET JSON with retry and exponential backoff."""
from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 60
HEADERS = {"User-Agent": "observatorio-precos/0.1 (portfolio project)"}
RETRY_STATUS = (429, 500, 502, 503, 504)


def _session() -> requests.Session:
    """Session that retries transient failures (backoff: 1s, 2s, 4s, 8s, 16s)."""
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=RETRY_STATUS,
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(HEADERS)
    return session


def get_json(url: str) -> Any:
    """GET a URL and return the decoded JSON. Raises on a non-2xx final response."""
    log.debug("GET %s", url)
    with _session() as session:
        resp = session.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()
