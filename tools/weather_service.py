from __future__ import annotations

import httpx


WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


def get_weather_conditions(
    latitude: float,
    longitude: float,
    forecast_days: int = 3,
) -> dict:
    """
    Retrieve atmospheric conditions relevant to marine operations.
    """

    forecast_days = max(
        1,
        min(forecast_days, 7),
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "pressure_msl",
            "weather_code",
        ]),

        "hourly": ",".join([
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "visibility",
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

        return {
            "status": "OK",

            "source":
                "Open-Meteo Weather",

            "latitude":
                latitude,

            "longitude":
                longitude,

            "current":
                data.get(
                    "current",
                    {},
                ),

            "current_units":
                data.get(
                    "current_units",
                    {},
                ),

            "hourly":
                data.get(
                    "hourly",
                    {},
                ),

            "hourly_units":
                data.get(
                    "hourly_units",
                    {},
                ),

            "forecast_days":
                forecast_days,
        }

    except Exception as exc:

        return {
            "status": "ERROR",
            "source": "Open-Meteo Weather",
            "error": str(exc),
        }