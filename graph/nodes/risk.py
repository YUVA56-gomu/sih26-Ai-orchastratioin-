"""
graph/nodes/risk.py
────────────────────
Deterministic Risk Assessment Node

Calculates a marine risk score purely from the raw data
using rule-based logic (no LLM). Score is 0-100, level is
LOW / MODERATE / HIGH / VERY HIGH.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.marine_risk import calculate_marine_risk


def risk_assessment_node(state: SamudraState) -> SamudraState:
    """Calculate deterministic marine risk score."""

    ocean    = state.get("ocean_data", {})
    weather  = state.get("weather_data", {})
    geofence = state.get("geofence_data", {})
    marine   = state.get("marine_data", {})   # optional — may be None/empty

    try:
        result = calculate_marine_risk(ocean, weather, geofence, marine or None)
        return {
            "risk_assessment": result,
            "node_trace": ["risk_assessment"],
        }
    except Exception as exc:
        return {
            "risk_assessment": {
                "risk_level": "UNKNOWN",
                "risk_score": -1,
                "reasons": [f"Risk calculation error: {exc}"],
                "evaluated_parameters": {},
                "decision_support_only": True,
            },
            "errors": [f"risk_node: {exc}"],
            "node_trace": ["risk_assessment"],
        }
