"""OpenWeatherMap integration and normalized dashboard data."""

from __future__ import annotations

from typing import Any

import requests


class WeatherServiceError(Exception):
	"""A user-safe error raised when the weather provider cannot respond."""


class WeatherService:
	"""Small adapter around OpenWeatherMap's current, forecast, and air APIs."""

	base_url = "https://api.openweathermap.org/data/2.5"

	def __init__(self, api_key: str, timeout: int = 12) -> None:
		self.api_key = api_key
		self.timeout = timeout

	def _request(self, endpoint: str, params: dict[str, Any], base_url: str | None = None) -> dict[str, Any]:
		if not self.api_key:
			raise WeatherServiceError("Weather API key is not configured on the server.")
		if self.api_key.startswith(("http://", "https://")):
			raise WeatherServiceError("Weather API key is misconfigured. Set WEATHER_API_KEY to an OpenWeather API key, not a URL.")
		request_params = {**params, "appid": self.api_key}
		try:
			response = requests.get(
				f"{base_url or self.base_url}/{endpoint}",
				params=request_params,
				timeout=self.timeout,
			)
		except requests.RequestException as error:
			raise WeatherServiceError("The weather provider is temporarily unavailable.") from error
		if response.status_code == 404:
			raise WeatherServiceError("City not found. Please check the spelling.")
		if response.status_code in (401, 403):
			raise WeatherServiceError(
				"OpenWeather rejected WEATHER_API_KEY. Check that it is an active OpenWeatherMap key, "
				"then restart Flask. New keys may take up to two hours to activate."
			)
		if response.status_code >= 400:
			raise WeatherServiceError("The weather provider returned an error.")
		try:
			return response.json()
		except ValueError as error:
			raise WeatherServiceError("The weather provider returned invalid data.") from error

	@staticmethod
	def _temperature(value: float) -> float:
		return round(value - 273.15, 1)

	@staticmethod
	def _wind_direction(degrees: float | None) -> str:
		if degrees is None:
			return "N/A"
		directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
		return directions[round(degrees / 45) % 8]

	def get_current_weather(self, city: str) -> dict[str, Any]:
		payload = self._request("weather", {"q": city, "units": "metric"})
		return self._normalize_current(payload)

	def get_weather_by_coordinates(self, latitude: float, longitude: float) -> dict[str, Any]:
		payload = self._request(
			"weather",
			{"lat": latitude, "lon": longitude, "units": "metric"},
		)
		return self._normalize_current(payload)

	def get_forecast(self, city: str) -> dict[str, Any]:
		payload = self._request("forecast", {"q": city, "units": "metric"})
		return self._normalize_forecast(payload)

	def get_forecast_by_coordinates(self, latitude: float, longitude: float) -> dict[str, Any]:
		payload = self._request(
			"forecast",
			{"lat": latitude, "lon": longitude, "units": "metric"},
		)
		return self._normalize_forecast(payload)

	def get_air_quality(self, latitude: float, longitude: float) -> dict[str, Any]:
		payload = self._request("air_pollution", {"lat": latitude, "lon": longitude})
		item = (payload.get("list") or [{}])[0]
		components = item.get("components", {})
		return {
			"aqi": item.get("main", {}).get("aqi"),
			"pm25": components.get("pm2_5"),
			"pm10": components.get("pm10"),
			"co": components.get("co"),
			"no2": components.get("no2"),
			"so2": components.get("so2"),
			"o3": components.get("o3"),
		}

	@staticmethod
	def _alert_severity(event_name: str) -> str:
		event = (event_name or "").lower()
		if any(keyword in event for keyword in ["severe", "warning", "storm", "heatwave", "blizzard", "tornado", "hurricane", "flood"]):
			return "high"
		if any(keyword in event for keyword in ["advisory", "watch", "wind", "rain", "cold", "snow"]):
			return "medium"
		return "low"

	def get_alerts(self, latitude: float, longitude: float) -> dict[str, Any]:
		payload = self._request(
			"onecall",
			{
				"lat": latitude,
				"lon": longitude,
				"exclude": "current,minutely,hourly,daily",
				"units": "metric",
			},
			base_url="https://api.openweathermap.org/data/3.0",
		)
		alerts = [
			{
				"sender": alert.get("sender_name", "Weather service"),
				"event": alert.get("event", "Weather alert"),
				"start": alert.get("start"),
				"end": alert.get("end"),
				"description": alert.get("description", ""),
			}
			for alert in payload.get("alerts", [])
		]
		alert_count = len(alerts)
		if not alert_count:
			return {
				"alerts": [],
				"alert_count": 0,
				"highest_severity": "low",
				"summary": "No active weather alerts in this area.",
			}
		severity_rank = {"low": 1, "medium": 2, "high": 3}
		highest_severity = max(
			(self._alert_severity(alert.get("event", "")) for alert in alerts),
			key=lambda value: severity_rank.get(value, 0),
		)
		summary_events = [alert.get("event", "Weather alert") for alert in alerts[:3]]
		summary = "Active weather alerts: " + "; ".join(summary_events)
		if alert_count > 3:
			summary += f" + {alert_count - 3} more"
		return {
			"alerts": alerts,
			"alert_count": alert_count,
			"highest_severity": highest_severity,
			"summary": summary,
		}

	def _normalize_current(self, payload: dict[str, Any]) -> dict[str, Any]:
		weather = (payload.get("weather") or [{}])[0]
		main = payload.get("main", {})
		wind = payload.get("wind", {})
		sys_data = payload.get("sys", {})
		return {
			"city": payload.get("name", "Unknown"),
			"country": sys_data.get("country", ""),
			"latitude": payload.get("coord", {}).get("lat"),
			"longitude": payload.get("coord", {}).get("lon"),
			"temperature": main.get("temp"),
			"feels_like": main.get("feels_like"),
			"temp_min": main.get("temp_min"),
			"temp_max": main.get("temp_max"),
			"humidity": main.get("humidity"),
			"pressure": main.get("pressure"),
			"visibility": round(payload.get("visibility", 0) / 1000, 1),
			"wind_speed": wind.get("speed"),
			"wind_direction": self._wind_direction(wind.get("deg")),
			"wind_degrees": wind.get("deg"),
			"cloud_cover": payload.get("clouds", {}).get("all"),
			"condition": weather.get("main", "Unknown"),
			"description": weather.get("description", ""),
			"icon": weather.get("icon", "01d"),
			"icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
			"sunrise": sys_data.get("sunrise"),
			"sunset": sys_data.get("sunset"),
			"timezone": payload.get("timezone", 0),
			"timestamp": payload.get("dt"),
		}

	def _normalize_forecast(self, payload: dict[str, Any]) -> dict[str, Any]:
		entries = []
		for item in payload.get("list", []):
			weather = (item.get("weather") or [{}])[0]
			entries.append(
				{
					"timestamp": item.get("dt"),
					"time": item.get("dt_txt"),
					"temperature": item.get("main", {}).get("temp"),
					"temp_min": item.get("main", {}).get("temp_min"),
					"temp_max": item.get("main", {}).get("temp_max"),
					"humidity": item.get("main", {}).get("humidity"),
					"rain_probability": round((item.get("pop", 0) or 0) * 100),
					"condition": weather.get("main", "Unknown"),
					"description": weather.get("description", ""),
					"icon": weather.get("icon", "01d"),
					"icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
				}
			)
		return {
			"city": payload.get("city", {}).get("name", "Unknown"),
			"country": payload.get("city", {}).get("country", ""),
			"latitude": payload.get("city", {}).get("coord", {}).get("lat"),
			"longitude": payload.get("city", {}).get("coord", {}).get("lon"),
			"timezone": payload.get("city", {}).get("timezone", 0),
			"entries": entries,
		}
