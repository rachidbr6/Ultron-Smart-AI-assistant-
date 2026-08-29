import unittest
from unittest.mock import MagicMock, patch

from ultron.integrations import weather


class WeatherConditionTests(unittest.TestCase):
    def test_known_code_maps_to_description(self):
        self.assertEqual(weather.weather_condition(0), "clear sky")
        self.assertEqual(weather.weather_condition(61), "light rain")

    def test_unknown_code_falls_back(self):
        self.assertEqual(weather.weather_condition(9999), "unusual conditions")


class ResolveLocationTests(unittest.TestCase):
    @patch("ultron.integrations.weather._geocode_city")
    def test_prefers_configured_city(self, mock_geocode):
        mock_geocode.return_value = (48.85, 2.35, "Paris, France")
        with patch.dict("os.environ", {"JARVIS_WEATHER_CITY": "Paris"}):
            result = weather.resolve_location()
        self.assertEqual(result, (48.85, 2.35, "Paris, France"))
        mock_geocode.assert_called_once_with("Paris")

    @patch("ultron.integrations.weather._locate_by_ip")
    def test_falls_back_to_ip_when_no_city_configured(self, mock_ip):
        mock_ip.return_value = (48.66, 6.15, "Nancy")
        with patch.dict("os.environ", {"JARVIS_WEATHER_CITY": ""}):
            result = weather.resolve_location()
        self.assertEqual(result, (48.66, 6.15, "Nancy"))
        mock_ip.assert_called_once()

    @patch("ultron.integrations.weather._locate_by_ip")
    @patch("ultron.integrations.weather._geocode_city")
    def test_falls_back_to_ip_when_geocoding_fails(self, mock_geocode, mock_ip):
        mock_geocode.return_value = None
        mock_ip.return_value = (48.66, 6.15, "Nancy")
        with patch.dict("os.environ", {"JARVIS_WEATHER_CITY": "Nonexistentville"}):
            result = weather.resolve_location()
        self.assertEqual(result, (48.66, 6.15, "Nancy"))


class FetchWeatherTests(unittest.TestCase):
    @patch("ultron.integrations.weather.resolve_location")
    def test_returns_none_when_location_unresolved(self, mock_resolve):
        mock_resolve.return_value = None
        self.assertIsNone(weather.fetch_current_weather())

    @patch("ultron.integrations.weather.requests.get")
    @patch("ultron.integrations.weather.resolve_location")
    def test_parses_successful_response(self, mock_resolve, mock_get):
        mock_resolve.return_value = (48.66, 6.15, "Nancy, France")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 22.8,
                "apparent_temperature": 21.3,
                "weather_code": 80,
                "wind_speed_10m": 15.7,
            },
            "daily": {"temperature_2m_max": [22.9], "temperature_2m_min": [14.9]},
        }
        mock_get.return_value = mock_response

        result = weather.fetch_current_weather()

        self.assertEqual(result["location"], "Nancy, France")
        self.assertEqual(result["temperature"], 23)
        self.assertEqual(result["condition"], "light rain showers")
        self.assertEqual(result["high"], 23)
        self.assertEqual(result["low"], 15)

    @patch("ultron.integrations.weather.requests.get")
    @patch("ultron.integrations.weather.resolve_location")
    def test_returns_none_on_malformed_response(self, mock_resolve, mock_get):
        mock_resolve.return_value = (48.66, 6.15, "Nancy")
        mock_response = MagicMock()
        mock_response.json.return_value = {"current": {}, "daily": {}}
        mock_get.return_value = mock_response

        self.assertIsNone(weather.fetch_current_weather())


class BuildWeatherSummaryTests(unittest.TestCase):
    @patch("ultron.integrations.weather.fetch_current_weather")
    def test_returns_none_when_fetch_fails(self, mock_fetch):
        mock_fetch.return_value = None
        self.assertIsNone(weather.build_weather_summary())

    @patch("ultron.integrations.weather.fetch_current_weather")
    def test_builds_readable_sentence(self, mock_fetch):
        mock_fetch.return_value = {
            "location": "Nancy, France",
            "temperature": 23,
            "feels_like": 21,
            "condition": "light rain showers",
            "wind_kph": 16,
            "high": 23,
            "low": 15,
        }

        summary = weather.build_weather_summary()

        self.assertIn("23 degrees in Nancy, France", summary)
        self.assertIn("light rain showers", summary)
        self.assertIn("high is 23, low is 15", summary)


if __name__ == "__main__":
    unittest.main()
