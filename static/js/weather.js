let currentWeather = null;
let currentForecast = null;

async function fetchJson(url, options = {}) {
	const response = await fetch(url, options);
	const data = await response.json();
	if (!response.ok) throw new Error(data.error || 'The request could not be completed.');
	return data;
}

async function loadCity(city) {
	const [weather, forecast] = await Promise.all([fetchJson(`/api/weather/current?city=${encodeURIComponent(city)}`), fetchJson(`/api/weather/forecast?city=${encodeURIComponent(city)}`)]);
	return applyWeatherData(weather, forecast);
}

async function loadCoordinates(latitude, longitude) {
	const weather = await fetchJson(`/api/weather/location?lat=${latitude}&lon=${longitude}`);
	let forecast = { entries: [] };
	try { forecast = await fetchJson(`/api/weather/forecast?city=${encodeURIComponent(weather.city)}`); } catch (error) { console.warn(error); }
	return applyWeatherData(weather, forecast);
}

async function applyWeatherData(weather, forecast) {
	currentWeather = weather;
	currentForecast = forecast;
	renderCurrentWeather(weather);
	renderHourly(forecast.entries || []);
	renderDaily(forecast.entries || []);
	renderCharts(forecast.entries || []);
	updateMap(weather);
	document.getElementById('assistant-location').textContent = `${weather.city}, ${weather.country}`;
	document.getElementById('updated-label').textContent = 'LIVE CONDITIONS';
	try { renderAirQuality(await fetchJson(`/api/weather/air-quality?lat=${weather.latitude}&lon=${weather.longitude}`)); } catch (error) { document.getElementById('air-card').hidden = true; }
	try { renderAlerts(await fetchJson(`/api/weather/alerts?lat=${weather.latitude}&lon=${weather.longitude}`)); } catch (error) { renderAlerts({ alerts: [], alert_count: 0, summary: 'No active weather alerts in this area.' }); }
	return weather;
}

function renderCurrentWeather(weather) {
	document.getElementById('location-name').textContent = weather.city;
	document.getElementById('location-meta').textContent = `${weather.country}  /  ${formatDate(weather.timestamp, weather.timezone)}`;
	document.getElementById('current-temperature').textContent = Math.round(weather.temperature ?? 0);
	document.getElementById('current-condition').textContent = weather.description || weather.condition;
	document.getElementById('feels-like').textContent = `Feels like ${Math.round(weather.feels_like ?? 0)}°`;
	document.getElementById('current-icon').src = weather.icon_url;
	document.getElementById('current-icon').alt = weather.description || weather.condition;
	document.getElementById('high-temperature').textContent = `${Math.round(weather.temp_max ?? 0)}°`;
	document.getElementById('low-temperature').textContent = `${Math.round(weather.temp_min ?? 0)}°`;
	document.getElementById('visibility-value').textContent = `${weather.visibility ?? '--'} km`;
	document.getElementById('local-time').textContent = `Local time ${formatTime(weather.timestamp, weather.timezone)}`;
	document.getElementById('sunrise-value').textContent = formatTime(weather.sunrise, weather.timezone);
	document.getElementById('sunset-value').textContent = formatTime(weather.sunset, weather.timezone);
	document.getElementById('day-length').textContent = weather.sunrise && weather.sunset ? `Day length ${formatDuration(weather.sunset - weather.sunrise)}` : 'Day length unavailable';
	document.getElementById('humidity-value').textContent = `${weather.humidity ?? '--'}%`;
	document.getElementById('humidity-note').textContent = weather.humidity > 70 ? 'High moisture' : 'Comfortable range';
	document.getElementById('wind-value').textContent = `${weather.wind_speed ?? '--'} m/s`;
	document.getElementById('wind-note').textContent = `Direction ${weather.wind_direction || '--'}`;
	document.getElementById('pressure-value').textContent = `${weather.pressure ?? '--'} hPa`;
	document.getElementById('cloud-value').textContent = `${weather.cloud_cover ?? '--'}%`;
	document.getElementById('coordinates').textContent = `Lat ${Number(weather.latitude).toFixed(3)} / Lon ${Number(weather.longitude).toFixed(3)}`;
	document.getElementById('header-date').textContent = formatDate(weather.timestamp, weather.timezone);
	document.getElementById('insight-title').textContent = `${weather.condition} conditions`;
	document.getElementById('insight-copy').textContent = buildInsight(weather);
	document.getElementById('insight-status').textContent = `Updated ${formatTime(weather.timestamp, weather.timezone)}`;
}

function renderHourly(entries) {
	const container = document.getElementById('hourly-list');
	if (!entries.length) { container.innerHTML = '<div class="empty-state">Hourly forecast unavailable.</div>'; return; }
	container.innerHTML = entries.slice(0, 12).map((item, index) => `<article class="hour-card"><time>${index === 0 ? 'Now' : formatHour(item.timestamp)}</time><img src="${item.icon_url}" alt="${item.description}"><strong>${Math.round(item.temperature)}°</strong><span class="rain-chance">${item.rain_probability}% rain</span></article>`).join('');
}

function renderDaily(entries) {
	const grouped = new Map();
	entries.forEach((item) => {
		const date = new Date(item.timestamp * 1000);
		const dayKey = date.toLocaleDateString([], { weekday: 'short' });
		const dateLabel = date.toLocaleDateString([], { month: 'short', day: 'numeric' });
		if (!grouped.has(dayKey)) grouped.set(dayKey, []);
		grouped.get(dayKey).push({ ...item, dateLabel });
	});
	const days = [...grouped.entries()].slice(0, 5);
	document.getElementById('daily-list').innerHTML = days.length ? days.map(([day, items]) => { const representative = items[Math.floor(items.length / 2)]; const low = Math.min(...items.map((item) => item.temp_min)); const high = Math.max(...items.map((item) => item.temp_max)); const rain = Math.max(...items.map((item) => item.rain_probability)); const dateText = `${day}, ${items[0].dateLabel}`; return `<article class="daily-card"><span class="day">${dateText}</span><br><img src="${representative.icon_url}" alt="${representative.description}"><p>${representative.description}</p><div class="daily-temps"><span>${Math.round(high)}°</span><span>${Math.round(low)}°</span></div><div class="daily-rain">${rain}% rain</div></article>`; }).join('') : '<div class="empty-state">Extended forecast unavailable.</div>';
}

function renderAirQuality(data) {
	document.getElementById('air-card').hidden = false;
	const labels = { 1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very poor' };
	document.getElementById('aqi-value').textContent = data.aqi ?? '--'; document.getElementById('aqi-badge').textContent = labels[data.aqi] || 'Unavailable'; document.getElementById('pm25-value').textContent = data.pm25 ?? '--'; document.getElementById('pm10-value').textContent = data.pm10 ?? '--'; document.getElementById('aqi-note').textContent = labels[data.aqi] ? `${labels[data.aqi]} air quality for outdoor plans` : 'Air quality unavailable';
}

function renderAlerts(data = { alerts: [], alert_count: 0, summary: 'No active weather alerts in this area.' }) {
	const card = document.getElementById('alert-card');
	const list = document.getElementById('alerts-list');
	const badge = document.getElementById('alerts-badge');
	const summary = document.getElementById('alert-summary');
	const alerts = Array.isArray(data.alerts) ? data.alerts : [];
	if (!alerts.length) {
		card.hidden = true;
		badge.textContent = 'No alerts';
		summary.textContent = data.summary || 'No active weather alerts in this area.';
		list.innerHTML = '';
		return;
	}
	card.hidden = false;
	badge.textContent = `${data.alert_count || alerts.length} active`;
	badge.classList.toggle('priority-high', (data.highest_severity || 'low') === 'high');
	badge.classList.toggle('priority-medium', (data.highest_severity || 'low') === 'medium');
	summary.textContent = data.summary || 'Active weather alerts.';
	list.innerHTML = alerts.slice(0, 3).map((alert) => {
		const severity = /severe|warning|storm|flood|heat|hurricane|tornado|blizzard/i.test(alert.event || '') ? 'high' : /advisory|watch|wind|rain|cold|snow/i.test(alert.event || '') ? 'medium' : 'low';
		return `<div class="alert-item alert-${severity}"><div class="alert-item-header"><strong>${alert.event || 'Weather alert'}</strong><span>${severity.toUpperCase()}</span></div><p>${(alert.description || 'Weather conditions may affect your travel or outdoor plans.').slice(0, 180)}${((alert.description || '').length > 180) ? '...' : ''}</p><small>${formatAlertTime(alert.start)}${alert.end ? ` → ${formatAlertTime(alert.end)}` : ''}</small></div>`;
	}).join('');
}

function formatDate(timestamp, timezone = 0) { if (!timestamp) return '--'; return new Intl.DateTimeFormat([], { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' }).format(new Date((timestamp + timezone) * 1000)); }
function formatTime(timestamp, timezone = 0) { if (!timestamp) return '--'; return new Intl.DateTimeFormat([], { hour: 'numeric', minute: '2-digit', timeZone: 'UTC' }).format(new Date((timestamp + timezone) * 1000)); }
function formatDuration(seconds) { const hours = Math.floor(seconds / 3600); const minutes = Math.floor((seconds % 3600) / 60); return `${hours}h ${minutes}m`; }
function formatHour(timestamp) { return new Intl.DateTimeFormat([], { hour: 'numeric', timeZone: 'UTC' }).format(new Date(timestamp * 1000)); }
function formatAlertTime(timestamp) { return timestamp ? new Intl.DateTimeFormat([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(timestamp * 1000)) : '--'; }
function buildInsight(weather) { if (weather.temperature - weather.feels_like < -3) return 'The air feels cooler than the actual temperature. A light layer may be useful.'; if (weather.temperature - weather.feels_like > 3) return 'Humidity is making the air feel warmer than the thermometer suggests. Stay hydrated.'; if (weather.wind_speed > 8) return 'It is a breezy day. Secure lightweight items and expect conditions to feel cooler outside.'; return 'Conditions look fairly close to the measured temperature. A comfortable day is ahead.'; }
