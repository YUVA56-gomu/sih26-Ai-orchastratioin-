"""
graph/nodes/data_geofence.py
─────────────────────────────
Data Node — Geofence

Checks whether the location falls inside any restricted/protected zone.
Always runs (geofence check is cheap and safety-critical).
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.geofence import check_geofence


def geofence_data_node(state: SamudraState) -> SamudraState:
    """Check geofence / MPA / restricted zone for the location."""

    # If this is a recheck pass, only re-fetch if geofence was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "geofence" not in recheck_domains:
        return {"node_trace": ["geofence_data_collector(recheck_skipped)"]}

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "geofence_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "node_trace": ["geofence_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = check_geofence(lat, lon)
        return {
            "geofence_data": result,
            "node_trace": ["geofence_data_collector"],
        }

    except Exception as exc:
        return {
            "geofence_data": {"status": "ERROR", "error": str(exc)},
            "errors": [f"geofence_data_node: {exc}"],
            "node_trace": ["geofence_data_collector"],
        }
