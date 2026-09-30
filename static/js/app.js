document.addEventListener('DOMContentLoaded', () => {
	initializeMap();
	setTheme(localStorage.getItem('weather-theme') || 'light');
	bindEvents();
	loadSidebarData();
});

function bindEvents() {
	document.getElementById('search-form').addEventListener('submit', async (event) => { event.preventDefault(); const city = document.getElementById('city-search').value.trim(); if (city) await runWeatherTask(() => loadCity(city)); });
	document.querySelectorAll('.quick-city').forEach((button) => button.addEventListener('click', () => runWeatherTask(() => loadCity(button.dataset.city))));
	document.getElementById('location-button').addEventListener('click', () => { if (!navigator.geolocation) return showAlert('Location is not supported by this browser.'); navigator.geolocation.getCurrentPosition((position) => runWeatherTask(() => loadCoordinates(position.coords.latitude, position.coords.longitude)), () => showAlert('Location access was unavailable. Please search for a city instead.')); });
	document.getElementById('theme-toggle').addEventListener('click', toggleTheme); document.getElementById('sidebar-theme').addEventListener('click', toggleTheme);
	document.getElementById('favorite-button').addEventListener('click', saveFavorite);
	document.getElementById('ai-form').addEventListener('submit', async (event) => { event.preventDefault(); const input = document.getElementById('ai-question'); const question = input.value.trim(); if (!question) return; const answer = document.getElementById('ai-answer'); answer.textContent = 'Thinking about the conditions...'; try { answer.textContent = await askWeatherAssistant(question); input.value = ''; } catch (error) { answer.textContent = error.message; } });
	document.querySelectorAll('.suggestion').forEach((button) => button.addEventListener('click', () => { document.getElementById('ai-question').value = button.textContent; document.getElementById('ai-question').focus(); }));
}

async function runWeatherTask(task) { setLoading(true); hideAlert(); try { const weather = await task(); document.getElementById('city-search').value = weather.city; await loadSidebarData(); } catch (error) { showAlert(error.message); } finally { setLoading(false); } }
async function loadSidebarData() { try { renderFavorites(await fetchJson('/api/favorites')); renderHistory(await fetchJson('/api/search-history')); } catch (error) { console.warn(error); } }
function renderFavorites(items) { document.getElementById('favorite-count').textContent = items.length; document.getElementById('favorites-list').innerHTML = items.length ? items.map((item) => `<div class="city-row" data-city="${escapeText(item.city)}"><div class="city-row-main"><span class="city-pin">&#9733;</span><div><strong>${escapeText(item.city)}</strong><small>${escapeText(item.country || 'Saved place')}</small></div></div><button class="delete-city" data-delete="${item.id}" aria-label="Remove ${escapeText(item.city)}">&#10005;</button></div>`).join('') : '<div class="empty-state">Save a city with the star above.</div>'; document.querySelectorAll('#favorites-list .city-row').forEach((row) => row.addEventListener('click', (event) => { if (!event.target.dataset.delete) runWeatherTask(() => loadCity(row.dataset.city)); })); document.querySelectorAll('[data-delete]').forEach((button) => button.addEventListener('click', (event) => { event.stopPropagation(); deleteFavorite(button.dataset.delete); })); }
function renderHistory(items) { document.getElementById('history-list').innerHTML = items.length ? items.map((item) => `<div class="city-row" data-city="${escapeText(item.city)}"><div class="city-row-main"><span class="city-pin">&#9906;</span><div><strong>${escapeText(item.city)}</strong><small>${escapeText(item.country || 'Recent search')}</small></div></div><span class="muted">&#8594;</span></div>`).join('') : '<div class="empty-state">Your recent searches will appear here.</div>'; document.querySelectorAll('#history-list .city-row').forEach((row) => row.addEventListener('click', () => runWeatherTask(() => loadCity(row.dataset.city)))); }
async function saveFavorite() { if (!currentWeather) return showAlert('Search for a city before saving it.'); try { await fetchJson('/api/favorites', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(currentWeather) }); document.getElementById('favorite-button').classList.add('saved'); document.getElementById('favorite-button').innerHTML = '&#9733;'; await loadSidebarData(); } catch (error) { showAlert(error.message); } }
async function deleteFavorite(id) { try { await fetchJson(`/api/favorites/${id}`, { method: 'DELETE' }); await loadSidebarData(); } catch (error) { showAlert(error.message); } }
function setTheme(theme) { document.body.classList.toggle('dark', theme === 'dark'); localStorage.setItem('weather-theme', theme); document.getElementById('theme-toggle').innerHTML = theme === 'dark' ? '&#9790;' : '&#9788;'; if (currentForecast) renderCharts(currentForecast.entries); }
function toggleTheme() { setTheme(document.body.classList.contains('dark') ? 'light' : 'dark'); }
function setLoading(isLoading) { document.getElementById('loading-state').hidden = !isLoading; }
function showAlert(message) { const alert = document.getElementById('app-alert'); alert.textContent = message; alert.hidden = false; }
function hideAlert() { document.getElementById('app-alert').hidden = true; }
function escapeText(value) { return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]); }
