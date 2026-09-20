"""
graph/nodes/data_marine.py
───────────────────────────
Data Node — Open-Meteo Marine

Fetches wave conditions, swell, wind waves, ocean currents,
sea surface temperature, and modelled sea-level height from:
  https://marine-api.open-meteo.com/v1/marine

Follows the same conventions as data_weather.py and data_ocean.py:
- Reads location from state["location"]
- Writes result into state["marine_data"]
- Respects recheck_domains on gate RECHECK passes
- Never raises — always returns a structured result
- Records node trace using the existing project convention

All data from this node is MODELLED (not satellite observation).
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.marine_service import get_marine_conditions


def marine_data_node(state: SamudraState) -> SamudraState:
    """Collect modelled marine conditions from Open-Meteo Marine API."""

    # ── Recheck pass: skip if marine not flagged ──────────────────────────────
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "marine" not in recheck_domains:
        return {"node_trace": ["marine_data_collector(recheck_skipped)"]}

    # ── Location guard ────────────────────────────────────────────────────────
    location = state.get("location", {})

    if location.get("status") != "FOUND":
        return {
            "marine_data": {
                "status":    "BLOCKED",
                "source":    "Open-Meteo Marine",
                "data_type": "MODELLED",
                "reason":    f"Location unavailable: {location.get('status', 'UNKNOWN')}",
            },
            "node_trace": ["marine_data_collector"],
        }

    # ── Fetch ─────────────────────────────────────────────────────────────────
    try:
        lat  = float(location["latitude"])
        lon  = float(location["longitude"])

        plan = state.get("plan", {})
        forecast_days = int(plan.get("forecast_days", 7))

        result = get_marine_conditions(lat, lon, forecast_days)

        return {
            "marine_data": result,
            "node_trace":  ["marine_data_collector"],
        }

    except Exception as exc:
        return {
            "marine_data": {
                "status":    "ERROR",
                "source":    "Open-Meteo Marine",
                "data_type": "MODELLED",
                "error":     str(exc),
            },
            "errors":     [f"marine_data_node: {exc}"],
            "node_trace": ["marine_data_collector"],
        }
