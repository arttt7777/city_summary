import unittest

from processing.preprocessing import DEFAULT_DESCRIPTION, preprocess_rate, preprocess_weather


class PreprocessWeatherTest(unittest.TestCase):
    def test_cold_needs_warm_clothes(self) -> None:
        result = preprocess_weather({"temp_c": -3.24, "description": "clear sky"})
        self.assertEqual(result, {"temp_c": -3.2, "description": "clear sky", "warm_clothes": True})

    def test_zero_is_not_cold(self) -> None:
        self.assertFalse(preprocess_weather({"temp_c": 0, "description": "fog"})["warm_clothes"])

    def test_empty_description_gets_default(self) -> None:
        result = preprocess_weather({"temp_c": 5, "description": "  "})
        self.assertEqual(result["description"], DEFAULT_DESCRIPTION)


class PreprocessRateTest(unittest.TestCase):
    def test_expensive_rate(self) -> None:
        result = preprocess_rate("eur", 100.004)
        self.assertEqual(result, {"currency": "EUR", "rate_to_rub": 100.0, "expensive": False})

    def test_rate_above_threshold(self) -> None:
        self.assertTrue(preprocess_rate("EUR", 100.5)["expensive"])


if __name__ == "__main__":
    unittest.main()
