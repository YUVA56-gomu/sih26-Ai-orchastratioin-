"""
graph/nodes/data_tide_hazard.py
───────────────────────────────
Data Node — Tide Dynamics & Official Hazard Alert Feeds (Phase 2.4)

Fetches:
  1. Open-Meteo Marine hourly sea-level timeseries & computes extrema/phase (tide_service)
  2. Official hazard advisories & bulletins (hazard_service)
"""

from __future__ import annotations

from typing import Any
from state.schema import SamudraState
from tools.tide_service import get_tide_forecast
from tools.hazard_service import get_hazard_alerts


def tide_hazard_data_node(state: SamudraState) -> SamudraState:
    """Collect tide forecast and hazard alert data."""
    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "tide_data": {"status": "BLOCKED", "reason": f"Location unavailable: {location.get('status')}"},
            "hazard_data": {"status": "UNAVAILABLE", "alerts": [], "reason": f"Location unavailable: {location.get('status')}"},
            "node_trace": ["tide_hazard_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        tide_res = get_tide_forecast(lat, lon)
        hazard_res = get_hazard_alerts(lat, lon)

        return {
            "tide_data": tide_res,
            "hazard_data": hazard_res,
            "node_trace": ["tide_hazard_data_collector"],
        }
    except Exception as exc:
        return {
            "tide_data": {"status": "ERROR", "error": str(exc)},
            "hazard_data": {"status": "UNAVAILABLE", "alerts": [], "error": str(exc)},
            "errors": [f"tide_hazard_data_collector: {exc}"],
            "node_trace": ["tide_hazard_data_collector"],
        }
