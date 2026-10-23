"""Клиент Open-Meteo: геокодинг города и текущая погода."""

from typing import Any

from clients.exceptions import CityNotFoundError, InvalidResponseError
from clients.http import get_json

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Коды погоды WMO: https://open-meteo.com/en/docs (раздел "WMO Weather interpretation codes")
WMO_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def _require_number(data: dict[str, Any], key: str, source: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidResponseError(f"{source}: поле {key!r} отсутствует или не число")
    return float(value)


def _geocode(city: str) -> tuple[str, float, float]:
    status, data = get_json(
        GEOCODING_URL, {"name": city, "count": 1, "language": "en", "format": "json"}
    )
    if status != 200 or not isinstance(data, dict):
        raise InvalidResponseError(f"geocoding: неожиданный ответ (HTTP {status})")

    results = data.get("results")
    if not results:
        raise CityNotFoundError(city)
    if not isinstance(results, list) or not isinstance(results[0], dict):
        raise InvalidResponseError("geocoding: поле 'results' имеет неверный формат")

    place = results[0]
    name = place.get("name")
    if not isinstance(name, str) or not name:
        raise InvalidResponseError("geocoding: поле 'name' отсутствует")
    return (
        name,
        _require_number(place, "latitude", "geocoding"),
        _require_number(place, "longitude", "geocoding"),
    )


def get_weather(city: str) -> dict[str, Any]:
    """Возвращает {"city", "temp_c", "description"} для города."""
    name, latitude, longitude = _geocode(city)

    status, data = get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
        },
    )
    if status != 200 or not isinstance(data, dict):
        raise InvalidResponseError(f"forecast: неожиданный ответ (HTTP {status})")

    current = data.get("current")
    if not isinstance(current, dict):
        raise InvalidResponseError("forecast: поле 'current' отсутствует")

    temp_c = _require_number(current, "temperature_2m", "forecast")
    code = current.get("weather_code")
    description = WMO_DESCRIPTIONS.get(code, "") if isinstance(code, int) else ""

    return {"city": name, "temp_c": temp_c, "description": description}
