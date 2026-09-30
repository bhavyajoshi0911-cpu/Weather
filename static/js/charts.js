let temperatureChart;
let rainChart;

function renderCharts(entries) {
	if (!window.Chart || !entries?.length) return;
	const labels = entries.slice(0, 12).map((item) => formatHour(item.timestamp));
	const temperatures = entries.slice(0, 12).map((item) => item.temperature);
	const rain = entries.slice(0, 12).map((item) => item.rain_probability);
	const gridColor = getComputedStyle(document.body).getPropertyValue('--line').trim();
	const textColor = getComputedStyle(document.body).getPropertyValue('--muted').trim();
	const common = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: textColor, font: { size: 10 } } }, y: { grid: { color: gridColor }, ticks: { color: textColor, font: { size: 10 } }, border: { display: false } } } };
	temperatureChart?.destroy();
	rainChart?.destroy();
	temperatureChart = new Chart(document.getElementById('temperature-chart'), { type: 'line', data: { labels, datasets: [{ data: temperatures, borderColor: '#1d8b84', backgroundColor: 'rgba(29,139,132,.10)', fill: true, tension: .4, pointRadius: 3, pointBackgroundColor: '#1d8b84' }] }, options: common });
	rainChart = new Chart(document.getElementById('rain-chart'), { type: 'bar', data: { labels, datasets: [{ data: rain, backgroundColor: '#e47d68', borderRadius: 4, maxBarThickness: 13 }] }, options: { ...common, scales: { ...common.scales, y: { ...common.scales.y, beginAtZero: true, max: 100 } } } });
}

function formatHour(timestamp) {
	return new Date(timestamp * 1000).toLocaleTimeString([], { hour: 'numeric' });
}
