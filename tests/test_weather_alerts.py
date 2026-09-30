import unittest
from unittest.mock import patch

from services.weather_service import WeatherService


class WeatherServiceAlertSummaryTests(unittest.TestCase):
    @patch("services.weather_service.requests.get")
    def test_get_alerts_builds_summary_for_active_alerts(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "alerts": [
                {
                    "sender_name": "NWS",
                    "event": "Severe Thunderstorm Warning",
                    "start": 1700000000,
                    "end": 1700003600,
                    "description": "Large hail and damaging winds are possible.",
                }
            ]
        }

        alerts = WeatherService("test-key").get_alerts(40.7128, -74.0060)

        self.assertEqual(alerts["alert_count"], 1)
        self.assertEqual(alerts["highest_severity"], "high")
        self.assertIn("Severe Thunderstorm Warning", alerts["summary"])


if __name__ == "__main__":
    unittest.main()
