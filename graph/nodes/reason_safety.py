"""
graph/nodes/reason_safety.py
─────────────────────────────
Specialist Reasoning — Safety

Synthesises all available evidence into a marine safety assessment.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import SAFETY_REASONER


def safety_reasoning_node(state: SamudraState) -> SamudraState:
    """Produce a marine safety assessment from all collected evidence."""

    query = state.get("query_in_english") or state.get("user_query", "")

    ocean   = state.get("ocean_data", {})
    weather = state.get("weather_data", {})
    geofence = state.get("geofence_data", {})
    risk     = state.get("risk_assessment", {})
    tide     = state.get("tide_data", {})
    hazard   = state.get("hazard_data", {})

    # Trim weather hourly to avoid token overflow
    weather_trimmed = {k: v for k, v in weather.items() if k != "hourly"}
    hourly = weather.get("hourly", {})
    weather_trimmed["hourly_24h"] = {
        k: v[:24] if isinstance(v, list) else v
        for k, v in hourly.items()
    }

    context = (
        f"USER QUERY: {query}\n\n"
        f"OCEAN DATA:\n{json.dumps(ocean, indent=2)[:700]}\n\n"
        f"WEATHER DATA:\n{json.dumps(weather_trimmed, indent=2)[:700]}\n\n"
        f"TIDE DYNAMICS (MODELLED):\n{json.dumps(tide, indent=2)[:600]}\n\n"
        f"OFFICIAL HAZARD ALERTS:\n{json.dumps(hazard, indent=2)[:600]}\n\n"
        f"GEOFENCE DATA:\n{json.dumps(geofence, indent=2)}\n\n"
        f"RISK ASSESSMENT:\n{json.dumps(risk, indent=2)}"
    )

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=SAFETY_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "safety_reasoning": extract_text(response),
            "node_trace": ["safety_reasoner"],
        }
    except Exception as exc:
        return {
            "safety_reasoning": f"Safety reasoning failed: {exc}",
            "errors": [f"safety_reasoning_node: {exc}"],
            "node_trace": ["safety_reasoner"],
        }
