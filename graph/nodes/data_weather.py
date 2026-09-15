"""
graph/nodes/data_weather.py
────────────────────────────
Data Node — Weather (Open-Meteo)

Fetches current conditions and forecast from Open-Meteo.
Skipped if "weather" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.weather_service import get_weather_conditions


def weather_data_node(state: SamudraState) -> SamudraState:
    """Collect weather observations and forecast from Open-Meteo."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if weather was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "weather" not in recheck_domains:
        return {"node_trace": ["weather_data_collector(recheck_skipped)"]}

    if "weather" not in domains:
        return {
            "weather_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "node_trace": ["weather_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "weather_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "node_trace": ["weather_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        forecast_days = int(plan.get("forecast_days", 1))
        result = get_weather_conditions(lat, lon, forecast_days)
        return {
            "weather_data": result,
            "node_trace": ["weather_data_collector"],
        }

    except Exception as exc:
        return {
            "weather_data": {"status": "ERROR", "error": str(exc)},
            "errors": [f"weather_data_node: {exc}"],
            "node_trace": ["weather_data_collector"],
        }
