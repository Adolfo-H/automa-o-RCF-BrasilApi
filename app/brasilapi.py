import threading
import time

import requests

from app.config import (
    BACKOFF_BASE_SECONDS,
    MAX_RETRIES,
    REQUEST_INTERVAL_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
)

BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"

_session = requests.Session()
_rate_limit_lock = threading.Lock()
_next_request_at = 0.0


def _aguardar_janela():
    global _next_request_at

    with _rate_limit_lock:
        agora = time.monotonic()
        if agora < _next_request_at:
            time.sleep(_next_request_at - agora)

        _next_request_at = max(agora, _next_request_at) + REQUEST_INTERVAL_SECONDS


def consultar_cnpj(cnpj: str) -> dict:
    cnpj = "".join(filter(str.isdigit, cnpj))
    ultima_excecao = None

    for tentativa in range(1, MAX_RETRIES + 1):
        _aguardar_janela()
        try:
            response = _session.get(
                f"{BASE_URL}/{cnpj}",
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                espera = float(retry_after) if retry_after else BACKOFF_BASE_SECONDS * tentativa
                time.sleep(espera)
                continue

            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            ultima_excecao = exc
            if tentativa == MAX_RETRIES:
                break
            time.sleep(BACKOFF_BASE_SECONDS * tentativa)

    raise ultima_excecao
