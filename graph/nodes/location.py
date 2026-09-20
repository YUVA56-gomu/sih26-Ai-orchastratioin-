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
    active_ctx = dict(state.get("active_context") or {})

    # Helper to return location + updated active_context
    def _make_result(loc_dict: dict) -> SamudraState:
        if loc_dict.get("status") == "FOUND":
            active_ctx["location"] = loc_dict
            if plan.get("time_request"):
                active_ctx["time_request"] = plan.get("time_request")
            if plan.get("forecast_days"):
                active_ctx["forecast_days"] = plan.get("forecast_days")
        return {
            "location": loc_dict,
            "active_context": active_ctx,
            "node_trace": ["location_resolver"],
        }

    # If planner already provided coordinates, use them directly
    if plan.get("coordinates_provided") and plan.get("latitude") and plan.get("longitude"):
        loc_res = {
            "status": "FOUND",
            "name": plan.get("location_text", "User-provided coordinates"),
            "latitude": float(plan["latitude"]),
            "longitude": float(plan["longitude"]),
            "source": "User-provided",
        }
        return _make_result(loc_res)

    location_text = plan.get("location_text", "").strip()

    # Check for generic pronoun references ("there", "it", "here", "closest one")
    generic_references = {"there", "it", "here", "the spot", "closest one", "that area", "that location", "same place"}
    is_generic = location_text.lower() in generic_references

    # Fallback to active_context location if location_text is missing or generic
    if not location_text or is_generic:
        existing_loc = active_ctx.get("location")
        if isinstance(existing_loc, dict) and existing_loc.get("status") == "FOUND":
            return _make_result(existing_loc)

    if not location_text:
        return {
            "location": {
                "status": "NOT_PROVIDED",
                "reason": "No location found in query or active context.",
            },
            "errors": ["location_node: no location text in plan or active context"],
            "node_trace": ["location_resolver"],
        }

    try:
        result = resolve_location(location_text)
        if result.get("status") != "FOUND":
            # If geocoding failed on location_text (e.g. "there"), try active_context fallback
            existing_loc = active_ctx.get("location")
            if isinstance(existing_loc, dict) and existing_loc.get("status") == "FOUND":
                return _make_result(existing_loc)
        return _make_result(result)

    except Exception as exc:
        existing_loc = active_ctx.get("location")
        if isinstance(existing_loc, dict) and existing_loc.get("status") == "FOUND":
            return _make_result(existing_loc)
        return {
            "location": {
                "status": "ERROR",
                "place": location_text,
                "error": str(exc),
            },
            "errors": [f"location_node: {exc}"],
            "node_trace": ["location_resolver"],
        }
