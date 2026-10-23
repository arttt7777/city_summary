"""Сборка сводки по городу из ответов клиентов."""

import logging
from typing import Any

from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import preprocess_rate, preprocess_weather

logger = logging.getLogger(__name__)


def build_city_summary(city: str, currency: str = "USD") -> dict[str, Any]:
    logger.info("Building summary for city=%r currency=%s", city, currency)
    weather = get_weather(city)
    rate = get_rate(currency)
    return {
        "city": weather["city"],
        "weather": preprocess_weather(weather),
        "rates": preprocess_rate(currency, rate),
    }
