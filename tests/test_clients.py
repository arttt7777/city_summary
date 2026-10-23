import unittest
from unittest import mock

import requests

from clients import http, rates, weather
from clients.exceptions import (
    CityNotFoundError,
    CurrencyNotFoundError,
    InvalidResponseError,
    ServiceUnavailableError,
)


def make_response(status: int, payload: object = None, headers: dict[str, str] | None = None):
    response = mock.Mock(spec=requests.Response)
    response.status_code = status
    response.headers = headers or {}
    response.json.return_value = payload
    return response


@mock.patch("clients.http.time.sleep")
@mock.patch("clients.http.requests.get")
class GetJsonTest(unittest.TestCase):
    def test_retries_on_timeout_and_5xx_then_succeeds(self, get, sleep) -> None:
        get.side_effect = [
            requests.exceptions.Timeout(),
            make_response(503),
            make_response(200, {"ok": True}),
        ]
        self.assertEqual(http.get_json("https://x"), (200, {"ok": True}))
        self.assertEqual(get.call_count, 3)
        for call in get.call_args_list:
            self.assertLessEqual(call.kwargs["timeout"], 10)

    def test_gives_up_after_retries(self, get, sleep) -> None:
        get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(ServiceUnavailableError):
            http.get_json("https://x")
        self.assertEqual(get.call_count, http.MAX_RETRIES + 1)

    def test_respects_numeric_retry_after(self, get, sleep) -> None:
        get.side_effect = [make_response(429, headers={"Retry-After": "7"}), make_response(200, {})]
        http.get_json("https://x")
        sleep.assert_called_once_with(7.0)

    def test_does_not_retry_client_errors(self, get, sleep) -> None:
        get.return_value = make_response(422, {"message": "invalid"})
        self.assertEqual(http.get_json("https://x")[0], 422)
        self.assertEqual(get.call_count, 1)

    def test_non_json_body_is_invalid_response(self, get, sleep) -> None:
        response = make_response(200)
        response.json.side_effect = ValueError()
        get.return_value = response
        with self.assertRaises(InvalidResponseError):
            http.get_json("https://x")


class WeatherClientTest(unittest.TestCase):
    @mock.patch("clients.weather.get_json")
    def test_parses_weather(self, get_json) -> None:
        get_json.side_effect = [
            (200, {"results": [{"name": "Moscow", "latitude": 55.7, "longitude": 37.6}]}),
            (200, {"current": {"temperature_2m": -3.2, "weather_code": 0}}),
        ]
        self.assertEqual(
            weather.get_weather("moscow"),
            {"city": "Moscow", "temp_c": -3.2, "description": "clear sky"},
        )

    @mock.patch("clients.weather.get_json", return_value=(200, {"generationtime_ms": 0.1}))
    def test_unknown_city(self, get_json) -> None:
        with self.assertRaises(CityNotFoundError):
            weather.get_weather("Qwzxqq")

    @mock.patch("clients.weather.get_json")
    def test_missing_temperature(self, get_json) -> None:
        get_json.side_effect = [
            (200, {"results": [{"name": "Moscow", "latitude": 55.7, "longitude": 37.6}]}),
            (200, {"current": {"weather_code": 0}}),
        ]
        with self.assertRaises(InvalidResponseError):
            weather.get_weather("Moscow")


class RatesClientTest(unittest.TestCase):
    def setUp(self) -> None:
        rates._cache.clear()

    @mock.patch("clients.rates.get_json")
    def test_parses_rate_and_caches_it(self, get_json) -> None:
        get_json.return_value = (200, {"base": "USD", "quote": "RUB", "rate": 92.15})
        self.assertEqual(rates.get_rate("usd"), 92.15)
        self.assertEqual(rates.get_rate("USD"), 92.15)
        get_json.assert_called_once()

    @mock.patch("clients.rates.get_json", return_value=(422, {"message": "invalid currency"}))
    def test_unknown_currency(self, get_json) -> None:
        with self.assertRaises(CurrencyNotFoundError):
            rates.get_rate("XYZ")

    @mock.patch("clients.rates.get_json", return_value=(200, {"base": "USD", "quote": "RUB"}))
    def test_missing_rate(self, get_json) -> None:
        with self.assertRaises(InvalidResponseError):
            rates.get_rate("USD")


if __name__ == "__main__":
    unittest.main()
