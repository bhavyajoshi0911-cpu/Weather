let weatherMap;
let weatherMarker;

function initializeMap() {
	if (!window.L || weatherMap) return;
	weatherMap = L.map('weather-map', { zoomControl: false }).setView([20, 0], 2);
	L.control.zoom({ position: 'bottomright' }).addTo(weatherMap);
	L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap &copy; CARTO' }).addTo(weatherMap);
}

function updateMap(weather) {
	initializeMap();
	if (!weatherMap || weather.latitude == null || weather.longitude == null) return;
	const point = [weather.latitude, weather.longitude];
	weatherMap.setView(point, 10);
	if (weatherMarker) weatherMarker.remove();
	weatherMarker = L.marker(point).addTo(weatherMap).bindPopup(`<b>${escapeHtml(weather.city)}</b><br>${escapeHtml(weather.description || '')}`).openPopup();
	setTimeout(() => weatherMap.invalidateSize(), 100);
}

function escapeHtml(value) {
	return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
}
