"""Server-side Gemini weather assistant integration."""

from __future__ import annotations

import time
from typing import Any

import requests


class GeminiServiceError(Exception):
	"""A user-safe error raised when Gemini cannot answer."""


class GeminiService:
	PLACEHOLDER_KEYS = {
		"",
		"your_gemini_key",
		"your_api_key",
		"gemini_api_key",
		"placeholder",
		"changeme",
	}
	MODEL_CANDIDATES = (
		"gemini-3.6-flash",
		"gemini-2.5-flash",
		"gemini-2.5-flash-lite",
	)

	def __init__(self, api_key: str, model: str = "gemini-2.5-flash", timeout: int = 20) -> None:
		self.api_key = api_key
		self.model = model
		self.timeout = timeout

	def answer_weather_question(self, question: str, weather: dict[str, Any]) -> str:
		normalized_key = (self.api_key or "").strip()
		if not normalized_key or normalized_key.lower() in {key.lower() for key in self.PLACEHOLDER_KEYS}:
			raise GeminiServiceError(
				"Gemini API key is not configured on the server. Add a valid Google AI Studio key to .env and restart Flask."
			)
		prompt = (
			"You are a concise weather assistant. Use only the supplied weather information. "
			"If information is unavailable, clearly say that it is unavailable. Do not fabricate "
			"forecasts. Answer in plain language in no more than 3 short paragraphs.\n\n"
			f"Supplied weather information:\n{weather}\n\nUser question: {question}"
		)
		model_names = []
		seen = set()
		for model_name in (self.model, *self.MODEL_CANDIDATES):
			if model_name and model_name not in seen:
				model_names.append(model_name)
				seen.add(model_name)
		last_error = ""
		for model_name in model_names:
			url = (
				"https://generativelanguage.googleapis.com/v1beta/models/"
				f"{model_name}:generateContent"
			)
			for attempt in range(2):
				try:
					response = requests.post(
						url,
						params={"key": self.api_key},
						json={"contents": [{"parts": [{"text": prompt}]}]},
						timeout=self.timeout,
					)
				except requests.RequestException as error:
					raise GeminiServiceError("The AI assistant is temporarily unavailable.") from error
				try:
					payload = response.json()
				except (ValueError, TypeError):
					payload = {}
				if response.status_code < 400:
					try:
						candidates = payload.get("candidates", [])
						answer = candidates[0]["content"]["parts"][0]["text"]
					except (KeyError, IndexError, TypeError, ValueError) as error:
						raise GeminiServiceError("The AI assistant returned an empty response.") from error
					return answer.strip()
				if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
					time.sleep(1)
					continue
				details = payload.get("error", {}).get("message", "") if isinstance(payload, dict) else ""
				last_error = details or f"HTTP {response.status_code}"
				if any(marker in details.lower() for marker in (
					"no longer available",
					"not available",
					"not found",
					"unsupported",
				)):
					break
				break
			if last_error:
				break
		if last_error:
			raise GeminiServiceError(f"The AI assistant could not answer right now. Gemini reported: {last_error}")
		raise GeminiServiceError("The AI assistant could not answer right now. Please try again in a moment.")
