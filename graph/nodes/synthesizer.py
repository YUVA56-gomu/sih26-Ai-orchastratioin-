"""
graph/nodes/synthesizer.py
───────────────────────────
Final Synthesis Node

Combines all evidence, specialist reasoning, and risk assessment
into a single explainable response in English.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import SYNTHESIZER


def _build_synthesis_context(state: SamudraState) -> str:
    """Assemble all evidence and reasoning into a single context block."""

    query   = state.get("query_in_english") or state.get("user_query", "")
    plan    = state.get("plan", {})
    loc     = state.get("location", {})
    risk    = state.get("risk_assessment", {})
    gate    = state.get("gate_decision", "PASS")
    conf    = state.get("confidence_score", 1.0)

    ocean_r   = state.get("ocean_reasoning", "")
    weather_r = state.get("weather_reasoning", "")
    fishery_r = state.get("fishery_reasoning", "")
    safety_r  = state.get("safety_reasoning", "")

    geofence  = state.get("geofence_data", {})
    errors    = state.get("errors", [])

    parts = [
        f"USER QUERY: {query}",
        f"INTENT: {plan.get('intent', 'general')}",
        f"LOCATION: {json.dumps(loc)}",
        f"\nRISK ASSESSMENT: {risk.get('risk_level','UNKNOWN')} "
        f"(score {risk.get('risk_score','-')}/100)\n"
        f"Reasons: {risk.get('reasons',[])}",
        f"\nGEOFENCE: inside_restricted={geofence.get('inside_restricted_zone',False)}",
        f"\nEVIDENCE CONFIDENCE: {conf:.2f} (gate={gate})",
        f"\n--- OCEAN SPECIALIST ---\n{ocean_r}",
        f"\n--- WEATHER SPECIALIST ---\n{weather_r}",
        f"\n--- FISHERY SPECIALIST ---\n{fishery_r}",
        f"\n--- SAFETY SPECIALIST ---\n{safety_r}",
    ]

    if errors:
        parts.append(f"\nDATA ERRORS: {errors}")

    return "\n".join(parts)


def synthesizer_node(state: SamudraState) -> SamudraState:
    """Produce the final English response from all evidence."""

    context = _build_synthesis_context(state)

    try:
        llm = get_llm(temperature=0.2)
        messages = [
            SystemMessage(content=SYNTHESIZER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "final_response_english": extract_text(response),
            "node_trace": ["synthesizer"],
        }
    except Exception as exc:
        fallback = (
            "I was unable to generate a complete response due to a system error. "
            f"Error: {exc}. "
            "Please try again or contact support."
        )
        return {
            "final_response_english": fallback,
            "errors": [f"synthesizer_node: {exc}"],
            "node_trace": ["synthesizer"],
        }
