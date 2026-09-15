"""
graph/nodes/gate.py
────────────────────
Anti-Hallucination Gate

Reviews all collected evidence for consistency, completeness,
and fabricated values. Returns PASS / RECHECK / BLOCKED.

This is the conditional edge target — the graph router reads
gate_decision to decide whether to continue or loop back for
a re-fetch of specific domains.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from prompts import ANTI_HALLUCINATION_GATE

_MAX_RECHECK = 2


def _summarise_evidence(state: SamudraState) -> str:
    """Build a compact evidence summary to send to the gate LLM."""
    parts = []

    plan = state.get("plan", {})
    parts.append(f"PLAN:\n{json.dumps(plan, indent=2)}")

    loc = state.get("location", {})
    parts.append(f"LOCATION:\n{json.dumps(loc, indent=2)}")

    ocean = state.get("ocean_data", {})
    parts.append(f"OCEAN DATA (status={ocean.get('status','?')}):\n{json.dumps(ocean, indent=2)[:800]}")

    weather = state.get("weather_data", {})
    parts.append(f"WEATHER DATA (status={weather.get('status','?')}):\n{json.dumps(weather, indent=2)[:800]}")

    fishery = state.get("fishery_data", {})
    parts.append(f"FISHERY DATA (status={fishery.get('status','?')}):\n{json.dumps(fishery, indent=2)[:400]}")

    geofence = state.get("geofence_data", {})
    parts.append(f"GEOFENCE DATA:\n{json.dumps(geofence, indent=2)}")

    errors = state.get("errors", [])
    if errors:
        parts.append(f"ERRORS SO FAR:\n{errors}")

    return "\n\n---\n\n".join(parts)


def anti_hallucination_gate_node(state: SamudraState) -> SamudraState:
    """
    Cross-validate evidence. Set gate_decision to PASS / RECHECK / BLOCKED.
    If recheck count exceeds _MAX_RECHECK, force PASS to avoid infinite loops.
    """

    recheck_count = state.get("recheck_count", 0)

    # Hard cap: avoid infinite re-fetch loops
    if recheck_count >= _MAX_RECHECK:
        return {
            "gate_decision": "PASS",
            "confidence_score": 0.5,
            "gate_reasons": ["Max recheck limit reached; proceeding with available evidence."],
            "recheck_domains": [],
            "node_trace": ["anti_hallucination_gate"],
        }

    evidence_summary = _summarise_evidence(state)

    try:
        llm = get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=ANTI_HALLUCINATION_GATE),
            HumanMessage(content=evidence_summary),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        decision = data.get("decision", "PASS").upper()

        if decision not in ("PASS", "RECHECK", "BLOCKED"):
            decision = "PASS"

        new_recheck_count = recheck_count + 1 if decision == "RECHECK" else recheck_count

        return {
            "gate_decision": decision,
            "confidence_score": float(data.get("confidence_score", 0.7)),
            "gate_reasons": data.get("reasons", []),
            "recheck_domains": data.get("recheck_domains", []),
            "recheck_count": new_recheck_count,
            "node_trace": ["anti_hallucination_gate"],
        }

    except Exception as exc:
        # On gate failure, default to PASS to avoid blocking the pipeline
        return {
            "gate_decision": "PASS",
            "confidence_score": 0.6,
            "gate_reasons": [f"Gate evaluation failed: {exc}"],
            "recheck_domains": [],
            "errors": [f"gate_node: {exc}"],
            "node_trace": ["anti_hallucination_gate"],
        }
