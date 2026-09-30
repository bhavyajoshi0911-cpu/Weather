"""Persistence helpers with a MySQL backend and local demo fallback."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
	import mysql.connector
except ImportError:  # pragma: no cover - dependency is installed in production setup
	mysql = None
else:
	mysql = mysql.connector


class Database:
	"""Store favorites and searches, falling back to memory for local UI work."""

	def __init__(self, config: Any) -> None:
		self.config = config
		self.memory_favorites: list[dict[str, Any]] = []
		self.memory_searches: list[dict[str, Any]] = []

	def _connect(self):
		if mysql is None:
			return None
		try:
			return mysql.connect(
				host=self.config.MYSQL_HOST,
				port=self.config.MYSQL_PORT,
				user=self.config.MYSQL_USER,
				password=self.config.MYSQL_PASSWORD,
				database=self.config.MYSQL_DATABASE,
				connection_timeout=3,
			)
		except mysql.Error:
			return None

	def list_favorites(self) -> list[dict[str, Any]]:
		connection = self._connect()
		if connection is None:
			return list(reversed(self.memory_favorites))
		try:
			cursor = connection.cursor(dictionary=True)
			cursor.execute("SELECT id, city, country, latitude, longitude FROM favorites WHERE user_id = 1 ORDER BY created_at DESC")
			return cursor.fetchall()
		finally:
			connection.close()

	def add_favorite(self, favorite: dict[str, Any]) -> dict[str, Any]:
		connection = self._connect()
		record = {
			"id": None,
			"city": favorite["city"],
			"country": favorite.get("country", ""),
			"latitude": favorite.get("latitude"),
			"longitude": favorite.get("longitude"),
		}
		if connection is None:
			existing = next((item for item in self.memory_favorites if item["city"].lower() == record["city"].lower()), None)
			if existing:
				return existing
			record["id"] = len(self.memory_favorites) + 1
			self.memory_favorites.append(record)
			return record
		try:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO favorites (user_id, city, country, latitude, longitude) VALUES (1, %s, %s, %s, %s)",
				(record["city"], record["country"], record["latitude"], record["longitude"]),
			)
			connection.commit()
			record["id"] = cursor.lastrowid
			return record
		finally:
			connection.close()

	def delete_favorite(self, favorite_id: int) -> bool:
		connection = self._connect()
		if connection is None:
			before = len(self.memory_favorites)
			self.memory_favorites = [item for item in self.memory_favorites if item["id"] != favorite_id]
			return len(self.memory_favorites) < before
		try:
			cursor = connection.cursor()
			cursor.execute("DELETE FROM favorites WHERE id = %s AND user_id = 1", (favorite_id,))
			connection.commit()
			return cursor.rowcount > 0
		finally:
			connection.close()

	def add_search(self, search: dict[str, Any]) -> None:
		record = {
			"city": search["city"],
			"country": search.get("country", ""),
			"searched_at": datetime.now(timezone.utc).isoformat(),
		}
		connection = self._connect()
		if connection is None:
			self.memory_searches = [item for item in self.memory_searches if item["city"].lower() != record["city"].lower()]
			self.memory_searches.append(record)
			self.memory_searches = self.memory_searches[-10:]
			return
		try:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO search_history (user_id, city, country) VALUES (1, %s, %s)",
				(record["city"], record["country"]),
			)
			connection.commit()
		finally:
			connection.close()

	def list_searches(self) -> list[dict[str, Any]]:
		connection = self._connect()
		if connection is None:
			return list(reversed(self.memory_searches))
		try:
			cursor = connection.cursor(dictionary=True)
			cursor.execute("SELECT id, city, country, searched_at FROM search_history WHERE user_id = 1 ORDER BY searched_at DESC LIMIT 10")
			return cursor.fetchall()
		finally:
			connection.close()
