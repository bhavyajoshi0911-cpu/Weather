"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)


class Config:
	"""Centralized settings for the Flask application and external services."""

	WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
	GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
	GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
	MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
	MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
	MYSQL_USER = os.getenv("MYSQL_USER", "root")
	MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
	MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "weather_dashboard")
	DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
	WEATHER_TIMEOUT_SECONDS = int(os.getenv("WEATHER_TIMEOUT_SECONDS", "12"))
