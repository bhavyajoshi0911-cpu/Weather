# Real-Time Weather Intelligence Dashboard

A Flask-powered weather workspace with a responsive vanilla JavaScript dashboard, OpenWeather data, Leaflet mapping, Chart.js visualizations, MySQL persistence, and a server-side Gemini weather assistant.

## Features

- City search and browser geolocation
- Current conditions, hourly forecast, five-day forecast, daylight, and air quality
- Temperature and precipitation charts
- Interactive Leaflet map
- Favorites and recent search history
- Dark/light theme saved in local storage
- Gemini answers grounded in the current weather payload
- Safe API-key handling through server-side environment variables
- Graceful fallback to in-memory favorites/history while MySQL is unavailable

## Technology stack

- Python 3, Flask, Requests, python-dotenv
- MySQL with `mysql-connector-python`
- HTML5, CSS3, vanilla JavaScript
- Chart.js and Leaflet loaded from CDN
- OpenWeatherMap and Google Gemini APIs

## Project architecture

`app.py` owns Flask routes and response handling. `services/` contains external API adapters and normalizes provider responses for the browser. `database/db.py` contains persistence operations and uses a demo-user fallback if MySQL is not reachable. The browser uses only `/api/...` endpoints and never receives either API key.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

Create a `.env` file from the template below and set real values for the keys you use:

```env
WEATHER_API_KEY=your_openweathermap_key
GEMINI_API_KEY=your_google_ai_studio_key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=weather_dashboard
FLASK_DEBUG=False
```

Get a Gemini key from Google AI Studio and paste it into `GEMINI_API_KEY`. `.env` is ignored by Git. Never put secrets in `templates/` or `static/`.

## MySQL setup

Start MySQL and run `database/schema.sql` in MySQL Workbench or the MySQL client. The application uses user ID `1` as the demo user for the first version. If MySQL is not available, the dashboard still works and stores favorites/history in memory for that process.

## Run

```powershell
venv\Scripts\activate
python app.py
```

Open `http://127.0.0.1:5000`.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Dashboard page |
| GET | `/api/weather/current?city=London` | Current weather |
| GET | `/api/weather/forecast?city=London` | Forecast data |
| GET | `/api/weather/location?lat=...&lon=...` | Current weather by coordinates |
| GET | `/api/weather/air-quality?lat=...&lon=...` | Air quality |
| GET | `/api/weather/alerts?lat=...&lon=...` | Severe weather alerts from OpenWeather One Call |
| GET/POST | `/api/favorites` | List or save favorites |
| DELETE | `/api/favorites/<id>` | Remove a favorite |
| GET/POST | `/api/search-history` | List or save searches |
| POST | `/api/ai/weather-advice` | Ask Gemini using supplied weather context |

## Screenshots

Add screenshots here after configuring an API key and running the dashboard.

## Future improvements

- User authentication and per-user sessions
- Provider caching and rate-limit handling
- More detailed UV and pollution history
- Automated tests and deployment configuration
