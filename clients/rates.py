"""Клиент Frankfurter: курс валюты к рублю с кэшем на 5 минут."""

import logging
import time

from clients.exceptions import CurrencyNotFoundError, InvalidResponseError
from clients.http import get_json

RATE_URL = "https://api.frankfurter.dev/v2/rate/{currency}/RUB"
CACHE_TTL_SECONDS = 5 * 60

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, float]] = {}  # currency -> (время получения, курс)


def get_rate(currency: str) -> float:
    """Возвращает курс currency→RUB."""
    currency = currency.upper()
    if currency == "RUB":
        return 1.0

    cached = _cache.get(currency)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        logger.info("Rate %s->RUB taken from cache", currency)
        return cached[1]

    status, data = get_json(RATE_URL.format(currency=currency))
    # Frankfurter отвечает 422 "invalid currency" (или 404) на неизвестный код
    if status in (404, 422):
        raise CurrencyNotFoundError(currency)
    if status != 200 or not isinstance(data, dict):
        raise InvalidResponseError(f"rates: неожиданный ответ (HTTP {status})")

    rate = data.get("rate")
    if isinstance(rate, bool) or not isinstance(rate, int | float) or rate <= 0:
        raise InvalidResponseError("rates: поле 'rate' отсутствует или некорректно")
    if data.get("base") != currency or data.get("quote") != "RUB":
        raise InvalidResponseError("rates: ответ не соответствует запрошенной паре валют")

    _cache[currency] = (time.monotonic(), float(rate))
    return float(rate)
