"""
graph/nodes/location.py
────────────────────────
Node 4 — Location Resolution

Resolves the location text from the plan into lat/lon coordinates.
If the planner already extracted coordinates, they pass through directly.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.location import resolve_location


def location_node(state: SamudraState) -> SamudraState:
    """Resolve location name → coordinates."""

    plan = state.get("plan", {})

    # If planner already provided coordinates, use them directly
    if plan.get("coordinates_provided") and plan.get("latitude") and plan.get("longitude"):
        return {
            "location": {
                "status": "FOUND",
                "name": plan.get("location_text", "User-provided coordinates"),
                "latitude": float(plan["latitude"]),
                "longitude": float(plan["longitude"]),
                "source": "User-provided",
            },
            "node_trace": ["location_resolver"],
        }

    location_text = plan.get("location_text", "").strip()

    if not location_text:
        return {
            "location": {
                "status": "NOT_PROVIDED",
                "reason": "No location found in query.",
            },
            "errors": ["location_node: no location text in plan"],
            "node_trace": ["location_resolver"],
        }

    try:
        result = resolve_location(location_text)
        return {
            "location": result,
            "node_trace": ["location_resolver"],
        }

    except Exception as exc:
        return {
            "location": {
                "status": "ERROR",
                "place": location_text,
                "error": str(exc),
            },
            "errors": [f"location_node: {exc}"],
            "node_trace": ["location_resolver"],
        }
