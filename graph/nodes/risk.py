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
from tools.evidence_service import aggregate_evidence


def risk_assessment_node(state: SamudraState) -> SamudraState:
    """Calculate deterministic marine risk score and aggregate evidence completeness."""

    ocean    = state.get("ocean_data", {})
    weather  = state.get("weather_data", {})
    geofence = state.get("geofence_data", {})
    marine   = state.get("marine_data", {})   # optional — may be None/empty
    tide     = state.get("tide_data", {})
    hazard   = state.get("hazard_data", {})

    evidence_records = list(state.get("evidence") or [])
    ev_summary = aggregate_evidence(evidence_records)

    try:
        result = calculate_marine_risk(
            ocean,
            weather,
            geofence,
            marine=marine or None,
            tide_data=tide or None,
            hazard_data=hazard or None,
        )
        return {
            "risk_assessment": result,
            "evidence_summary": ev_summary,
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
            "evidence_summary": ev_summary,
            "errors": [f"risk_node: {exc}"],
            "node_trace": ["risk_assessment"],
        }
