"""
graph/nodes/data_route.py
─────────────────────────
LangGraph node for Phase 2.6 Marine Route Intelligence data collection.

Resolves origin & destination coordinates, gathers environmental context across
weather, ocean hydrodynamics, tides, hazards, and GIS geofences, and executes
the deterministic Marine Route Engine.
"""

from __future__ import annotations

import re
from typing import Any, Dict
from state.schema import SamudraState
from tools.route_service import get_route_service


# Standard route destination fallbacks for common origin locations
DEFAULT_DESTINATIONS: Dict[str, Dict[str, Any]] = {
    "mumbai": {"name": "Goa Port Outer", "latitude": 15.49, "longitude": 73.80},
    "goa": {"name": "Mangalore Port Outer", "latitude": 12.92, "longitude": 74.80},
    "kochi": {"name": "Kanyakumari Offshore", "latitude": 8.05, "longitude": 77.55},
    "chennai": {"name": "Visakhapatnam Port Outer", "latitude": 17.68, "longitude": 83.30},
    "visakhapatnam": {"name": "Paradeep Port Outer", "latitude": 20.25, "longitude": 86.68},
}


def _extract_destination_from_query(query: str, origin_name: str) -> Optional[Dict[str, Any]]:
    """Attempt simple regex extraction of destination from user query string."""
    if not query:
        return None

    # Matches patterns like "from A to B" or "route to B" or "path to B"
    match = re.search(r'\bto\s+([A-Za-z\s]+?)(?:\s+from|\s*\.|\s*$)', query, re.IGNORECASE)
    if match:
        target = match.group(1).strip().lower()
        for key, loc in DEFAULT_DESTINATIONS.items():
            if key in target:
                return loc

    # Check query words against default destination map
    q_lower = query.lower()
    for key, loc in DEFAULT_DESTINATIONS.items():
        if key in q_lower and key not in origin_name.lower():
            return loc

    return None


def fetch_route_data(state: SamudraState) -> Dict[str, Any]:
    """
    LangGraph node gathering route calculation evidence.

    Returns dictionary updating state["route_data"] and state["node_trace"].
    """
    location = state.get("location") or {}
    status = location.get("status")

    if status != "FOUND" or location.get("latitude") is None:
        return {
            "route_data": {
                "status": "UNAVAILABLE",
                "message": "Origin location context is unavailable or unverified.",
                "verification": {
                    "eez": "INFORMATIONAL",
                    "mpa": "UNAVAILABLE",
                    "naval": "UNAVAILABLE",
                },
            },
            "node_trace": ["data_route"],
        }

    origin_name = location.get("name", "Origin")
    origin_lat = float(location["latitude"])
    origin_lon = float(location["longitude"])

    # Resolve destination coordinate
    dest_info = None
    plan = state.get("plan") or {}

    # Check if plan or context specifies destination
    if isinstance(plan, dict) and plan.get("destination_latitude") is not None:
        dest_info = {
            "name": plan.get("destination_name", "Destination"),
            "latitude": float(plan["destination_latitude"]),
            "longitude": float(plan["destination_longitude"]),
        }

    if not dest_info:
        dest_info = _extract_destination_from_query(
            state.get("user_query", ""), origin_name
        )

    if not dest_info:
        # Default destination based on origin
        o_lower = origin_name.lower()
        if "mumbai" in o_lower:
            dest_info = DEFAULT_DESTINATIONS["mumbai"]
        elif "chennai" in o_lower:
            dest_info = DEFAULT_DESTINATIONS["chennai"]
        elif "kochi" in o_lower:
            dest_info = DEFAULT_DESTINATIONS["kochi"]
        elif "visakhapatnam" in o_lower or "vizag" in o_lower:
            dest_info = DEFAULT_DESTINATIONS["visakhapatnam"]
        else:
            # Shift 2 degrees south & 1 degree east as default offshore route endpoint
            dest_info = {
                "name": f"Offshore Destination near {origin_name}",
                "latitude": round(origin_lat - 2.0, 2),
                "longitude": round(origin_lon + 1.0, 2),
            }

    dest_name = dest_info["name"]
    dest_lat = float(dest_info["latitude"])
    dest_lon = float(dest_info["longitude"])

    # Environment context assembly
    env_context = {
        "weather": state.get("weather_data"),
        "marine": state.get("marine_data"),
        "ocean": state.get("ocean_data"),
        "tide": state.get("tide_data"),
        "hazard": state.get("hazard_data"),
        "geofence": state.get("geofence_data"),
    }

    # Execute deterministic Marine Route Service
    route_service = get_route_service()
    result = route_service.calculate_route(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        origin_name=origin_name,
        dest_name=dest_name,
        env_context=env_context,
    )

    return {
        "route_data": result,
        "node_trace": ["data_route"],
    }
