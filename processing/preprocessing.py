"""Правила предобработки данных, полученных от внешних API."""

from typing import Any

COLD_THRESHOLD_C = 0.0
EXPENSIVE_THRESHOLD_RUB = 100.0
DEFAULT_DESCRIPTION = "no description"


def preprocess_weather(weather: dict[str, Any]) -> dict[str, Any]:
    """Округляет температуру, подставляет описание по умолчанию, ставит warm_clothes."""
    temp_c = round(float(weather["temp_c"]), 1)
    description = (weather.get("description") or "").strip() or DEFAULT_DESCRIPTION
    return {
        "temp_c": temp_c,
        "description": description,
        "warm_clothes": temp_c < COLD_THRESHOLD_C,
    }


def preprocess_rate(currency: str, rate_to_rub: float) -> dict[str, Any]:
    """Округляет курс и ставит флаг expensive."""
    rate = round(float(rate_to_rub), 2)
    return {
        "currency": currency.upper(),
        "rate_to_rub": rate,
        "expensive": rate > EXPENSIVE_THRESHOLD_RUB,
    }
