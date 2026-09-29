"""Unit tests for the command-line weather app."""

import unittest
from unittest.mock import patch

import weather_app


class WeatherAppTests(unittest.TestCase):
    @patch("weather_app.requests.get")
    def test_get_coordinates_returns_first_match(self, get):
        get.return_value.json.return_value = {
            "results": [{"name": "Paris", "country": "France", "latitude": 48.85, "longitude": 2.35}]
        }

        result = weather_app.get_coordinates("Paris")

        self.assertEqual(result["name"], "Paris")
        get.return_value.raise_for_status.assert_called_once_with()
        self.assertEqual(get.call_args.kwargs["params"]["name"], "Paris")

    @patch("weather_app.requests.get")
    def test_get_coordinates_raises_when_city_is_not_found(self, get):
        get.return_value.json.return_value = {"results": []}

        with self.assertRaisesRegex(ValueError, "No location found"):
            weather_app.get_coordinates("Nowhere")

    @patch("weather_app.requests.get")
    def test_get_current_weather_requests_current_measurements(self, get):
        get.return_value.json.return_value = {"current": {"temperature_2m": 18}}

        result = weather_app.get_current_weather(48.85, 2.35)

        self.assertEqual(result["current"]["temperature_2m"], 18)
        self.assertEqual(get.call_args.args[0], weather_app.WEATHER_URL)
        self.assertEqual(get.call_args.kwargs["params"]["latitude"], 48.85)
        self.assertIn("relative_humidity_2m", get.call_args.kwargs["params"]["current"])

    def test_describe_weather_handles_known_and_unknown_codes(self):
        self.assertEqual(weather_app.describe_weather(0), "Clear sky")
        self.assertEqual(weather_app.describe_weather(-1), "Unknown conditions")

    def test_format_weather_includes_measurements_and_location(self):
        location = {"name": "Paris", "country": "France"}
        weather = {
            "current": {
                "time": "2025-01-01T12:00",
                "temperature_2m": 18.2,
                "apparent_temperature": 17.0,
                "relative_humidity_2m": 61,
                "weather_code": 2,
                "wind_speed_10m": 12.5,
            },
            "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"},
        }

        report = weather_app.format_weather(location, weather)

        self.assertIn("Paris, France", report)
        self.assertIn("Partly cloudy", report)
        self.assertIn("18.2°C", report)
        self.assertIn("Feels like: 17.0°C", report)
        self.assertIn("Humidity: 61%", report)
        self.assertIn("12.5 km/h", report)

    @patch("builtins.input", return_value="")
    @patch("builtins.print")
    def test_main_rejects_empty_city_without_network_call(self, print_output, _input):
        with patch("weather_app.requests.get") as get:
            weather_app.main()

        print_output.assert_called_once_with("Please enter a city name.")
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
