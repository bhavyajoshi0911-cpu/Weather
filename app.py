"""Flask application entry point for the Weather Intelligence Dashboard."""

from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, render_template, request

from config import Config
from database.db import Database
from services.gemini_service import GeminiService, GeminiServiceError
from services.weather_service import WeatherService, WeatherServiceError


def create_app(config_class: type[Config] = Config) -> Flask:
	app = Flask(__name__)
	app.config.from_object(config_class)
	weather_service = WeatherService(config_class.WEATHER_API_KEY, config_class.WEATHER_TIMEOUT_SECONDS)
	gemini_service = GeminiService(config_class.GEMINI_API_KEY, config_class.GEMINI_MODEL)
	database = Database(config_class)

	@app.get("/")
	def index():
		return render_template("index.html")

	@app.get("/api/weather/current")
	def current_weather():
		city = request.args.get("city", "").strip()
		if not city:
			return _error("A city is required.", 400)
		try:
			weather = weather_service.get_current_weather(city)
			database.add_search(weather)
			return jsonify(weather)
		except WeatherServiceError as error:
			return _error(str(error), 502)

	@app.get("/api/weather/forecast")
	def forecast():
		city = request.args.get("city", "").strip()
		if not city:
			return _error("A city is required.", 400)
		try:
			return jsonify(weather_service.get_forecast(city))
		except WeatherServiceError as error:
			return _error(str(error), 502)

	@app.get("/api/weather/location")
	def location_weather():
		coordinates = _coordinates_from_request()
		if not _is_coordinates(coordinates):
			return coordinates
		latitude, longitude = coordinates
		try:
			weather = weather_service.get_weather_by_coordinates(latitude, longitude)
			database.add_search(weather)
			return jsonify(weather)
		except WeatherServiceError as error:
			return _error(str(error), 502)

	@app.get("/api/weather/air-quality")
	def air_quality():
		coordinates = _coordinates_from_request()
		if not _is_coordinates(coordinates):
			return coordinates
		try:
			return jsonify(weather_service.get_air_quality(*coordinates))
		except WeatherServiceError as error:
			return _error(str(error), 502)

	@app.get("/api/weather/alerts")
	def weather_alerts():
		coordinates = _coordinates_from_request()
		if not _is_coordinates(coordinates):
			return coordinates
		try:
			return jsonify(weather_service.get_alerts(*coordinates))
		except WeatherServiceError as error:
			return _error(str(error), 502)

	@app.get("/api/favorites")
	def favorites():
		return jsonify(database.list_favorites())

	@app.post("/api/favorites")
	def add_favorite():
		payload = request.get_json(silent=True) or {}
		if not payload.get("city"):
			return _error("Favorite city is required.", 400)
		return jsonify(database.add_favorite(payload)), 201

	@app.delete("/api/favorites/<int:favorite_id>")
	def remove_favorite(favorite_id: int):
		if not database.delete_favorite(favorite_id):
			return _error("Favorite city was not found.", 404)
		return jsonify({"message": "Favorite removed."})

	@app.get("/api/search-history")
	def search_history():
		return jsonify(database.list_searches())

	@app.post("/api/search-history")
	def save_search():
		payload = request.get_json(silent=True) or {}
		if not payload.get("city"):
			return _error("Search city is required.", 400)
		database.add_search(payload)
		return jsonify({"message": "Search saved."}), 201

	@app.post("/api/ai/weather-advice")
	def weather_advice():
		payload = request.get_json(silent=True) or {}
		question = str(payload.get("question", "")).strip()
		weather = payload.get("weather") or {}
		if not question:
			return _error("A question is required.", 400)
		if not isinstance(weather, dict):
			return _error("Weather context must be an object.", 400)
		try:
			return jsonify({"answer": gemini_service.answer_weather_question(question, weather)})
		except GeminiServiceError as error:
			return _error(str(error), 502)
		except Exception as error:
			return _error(f"The AI assistant could not answer right now. {error}", 502)

	@app.errorhandler(404)
	def not_found(error):
		if request.path.startswith("/api/"):
			return _error("Endpoint not found.", 404)
		return error

	return app


def _coordinates_from_request() -> tuple[float, float] | Any:
	try:
		latitude = float(request.args.get("lat", ""))
		longitude = float(request.args.get("lon", ""))
	except ValueError:
		return _error("Valid latitude and longitude are required.", 400)
	if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
		return _error("Coordinates are outside the valid range.", 400)
	return latitude, longitude


def _is_coordinates(value: Any) -> bool:
	return isinstance(value, tuple) and len(value) == 2 and all(isinstance(item, float) for item in value)


def _error(message: str, status: int):
	return jsonify({"error": message}), status


app = create_app()

if __name__ == "__main__":
	app.run(debug=Config.DEBUG)
