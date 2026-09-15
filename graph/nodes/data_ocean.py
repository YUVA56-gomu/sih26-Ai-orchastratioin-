"""
graph/nodes/data_ocean.py
──────────────────────────
Data Node — Ocean (Copernicus Marine)

Fetches SST, waves, and currents from Copernicus Marine Service.
Skipped if "ocean" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.copernicus_service import get_copernicus_marine_snapshot


def ocean_data_node(state: SamudraState) -> SamudraState:
    """Collect ocean observations from Copernicus Marine."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if ocean was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "ocean" not in recheck_domains:
        return {"node_trace": ["ocean_data_collector(recheck_skipped)"]}

    if "ocean" not in domains:
        return {
            "ocean_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "node_trace": ["ocean_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "ocean_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "node_trace": ["ocean_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = get_copernicus_marine_snapshot(lat, lon)
        return {
            "ocean_data": result,
            "node_trace": ["ocean_data_collector"],
        }

    except Exception as exc:
        return {
            "ocean_data": {"status": "ERROR", "error": str(exc)},
            "errors": [f"ocean_data_node: {exc}"],
            "node_trace": ["ocean_data_collector"],
        }
