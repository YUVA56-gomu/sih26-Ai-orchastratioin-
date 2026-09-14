from __future__ import annotations

from tools.copernicus_service import get_copernicus_marine_snapshot
from tools.geofence import check_geofence
from tools.location import resolve_location
from tools.marine_risk import calculate_marine_risk
from tools.weather_service import get_weather_conditions


def collect_marine_safety_evidence(
    place: str,
    forecast_days: int = 1,
) -> dict:
    """Collect the evidence needed for a marine safety assessment."""

    location = resolve_location(place)

    if location.get("status") != "FOUND":
        return {
            "status": "ERROR",
            "stage": "location",
            "location": location,
        }

    latitude = location["latitude"]
    longitude = location["longitude"]

    ocean = get_copernicus_marine_snapshot(
        latitude=latitude,
        longitude=longitude,
    )
    weather = get_weather_conditions(
        latitude=latitude,
        longitude=longitude,
        forecast_days=forecast_days,
    )
    geofence = check_geofence(
        latitude=latitude,
        longitude=longitude,
    )
    risk = calculate_marine_risk(
        ocean=ocean,
        weather=weather,
        geofence=geofence,
    )

    return {
        "status": "OK",
        "location": location,
        "ocean": ocean,
        "weather": weather,
        "geofence": geofence,
        "risk": risk,
    }