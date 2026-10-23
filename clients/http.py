"""Общий GET-запрос с timeout и retry."""

import logging
import time
from typing import Any

import requests

from clients.exceptions import InvalidResponseError, ServiceUnavailableError

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
MAX_RETRIES = 3  # повторы после первой попытки
BACKOFF_SECONDS = 0.5
MAX_RETRY_AFTER_SECONDS = 30
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    """Пауза перед следующей попыткой: Retry-After для 429, иначе экспоненциальная."""
    if response is not None and response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "")
        if retry_after.isdigit():
            return min(float(retry_after), MAX_RETRY_AFTER_SECONDS)
    return BACKOFF_SECONDS * 2**attempt


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    session: requests.Session | None = None,
) -> tuple[int, Any]:
    """Выполняет GET и возвращает (статус, JSON).

    Повторяет запрос при Timeout, ConnectionError, 429 и 500/502/503/504.
    Остальные статусы (в том числе 4xx) возвращает вызывающему клиенту:
    только он знает, что означает 404 или 422 для его API.
    """
    http = session or requests
    for attempt in range(MAX_RETRIES + 1):
        response: requests.Response | None = None
        try:
            response = http.get(url, params=params, timeout=TIMEOUT_SECONDS)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("GET %s failed (attempt %d): %s", url, attempt + 1, exc)
        else:
            logger.info("GET %s -> %d", url, response.status_code)
            if response.status_code not in RETRYABLE_STATUSES:
                try:
                    return response.status_code, response.json()
                except ValueError as exc:
                    raise InvalidResponseError(f"{url}: ответ не является JSON") from exc
            logger.warning(
                "GET %s returned %d (attempt %d)", url, response.status_code, attempt + 1
            )

        if attempt < MAX_RETRIES:
            time.sleep(_retry_delay(response, attempt))

    raise ServiceUnavailableError(f"{url}: сервис недоступен после {MAX_RETRIES} повторов")
