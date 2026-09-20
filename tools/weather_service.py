from __future__ import annotations

from datetime import datetime, timezone
import httpx


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_conditions(
    latitude: float,
    longitude: float,
    forecast_days: int = 3,
) -> dict:

    forecast_days = max(
        1,
        min(
            int(forecast_days),
            7,
        ),
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "surface_pressure",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "pressure_msl",
            "surface_pressure",
            "cloud_cover",
            "visibility",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "uv_index",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "rain_sum",
            "precipitation_hours",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "uv_index_max",
        ]),
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }

    try:
        response = httpx.get(
            WEATHER_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()
        retrieved_at = datetime.now(timezone.utc).isoformat()

        return {
            "status": "OK",
            "source": "Open-Meteo Weather",
            "latitude": latitude,
            "longitude": longitude,
            "current": data.get("current", {}),
            "current_units": data.get("current_units", {}),
            "hourly": data.get("hourly", {}),
            "hourly_units": data.get("hourly_units", {}),
            "daily": data.get("daily", {}),
            "daily_units": data.get("daily_units", {}),
            "forecast_days": forecast_days,
            "provenance": {
                "source": "Open-Meteo Weather API",
                "provider": "Open-Meteo",
                "data_class": "FORECAST",
                "retrieved_at": retrieved_at,
            },
            "data_status": "FORECAST_AVAILABLE",
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "source": "Open-Meteo Weather",
            "error": str(exc),
            "data_status": "UNAVAILABLE",
        }