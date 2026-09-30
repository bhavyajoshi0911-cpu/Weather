async function askWeatherAssistant(question) {
	if (!currentWeather) throw new Error('Search for a city before asking for weather advice.');
	const data = await fetchJson('/api/ai/weather-advice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, weather: currentWeather }) });
	return data.answer;
}
