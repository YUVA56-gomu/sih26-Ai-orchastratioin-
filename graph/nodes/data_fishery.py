"""
graph/nodes/data_fishery.py
────────────────────────────
Data Node — Fishery (PFZ heuristic / INCOIS)

Fetches PFZ candidates using the SST-heuristic service.
Skipped if "fishery" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.pfz_service import find_nearest_pfz


def fishery_data_node(state: SamudraState) -> SamudraState:
    """Collect PFZ heuristic data."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if fishery was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "fishery" not in recheck_domains:
        return {"node_trace": ["fishery_data_collector(recheck_skipped)"]}

    if "fishery" not in domains:
        return {
            "fishery_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "node_trace": ["fishery_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "fishery_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "node_trace": ["fishery_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = find_nearest_pfz(lat, lon)
        return {
            "fishery_data": result,
            "node_trace": ["fishery_data_collector"],
        }

    except Exception as exc:
        return {
            "fishery_data": {"status": "ERROR", "error": str(exc)},
            "errors": [f"fishery_data_node: {exc}"],
            "node_trace": ["fishery_data_collector"],
        }
