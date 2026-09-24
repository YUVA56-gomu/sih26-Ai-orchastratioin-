"""
graph/nodes/reason_weather.py
──────────────────────────────
Specialist Reasoning — Weather

Interprets Open-Meteo weather data for the user's query.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import WEATHER_REASONER


def weather_reasoning_node(state: SamudraState) -> SamudraState:
    """Interpret weather evidence for the user's query."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed")
    weather = state.get("weather_data", {})

    if (domains is not None and "weather" not in domains) or weather.get("status") in ("SKIPPED", "BLOCKED"):
        return {
            "weather_reasoning": f"Weather reasoning skipped: {weather.get('reason', 'Domain not required')}",
            "node_trace": ["weather_reasoner"],
        }

    query = state.get("query_in_english") or state.get("user_query", "")

    weather_trimmed = {k: v for k, v in weather.items() if k != "hourly"}
    hourly = weather.get("hourly", {})
    weather_trimmed["hourly_24h"] = {
        k: v[:24] if isinstance(v, list) else v
        for k, v in hourly.items()
    }

    prov = weather.get("provenance", {})

    context = (
        f"USER QUERY: {query}\n\n"
        f"DATA PROVENANCE: {json.dumps(prov)}\n\n"
        f"ATMOSPHERIC OBSERVATIONS & FORECAST DATA:\n{json.dumps(weather_trimmed, indent=2)[:2000]}"
    )

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=WEATHER_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "weather_reasoning": extract_text(response),
            "node_trace": ["weather_reasoner"],
        }
    except Exception as exc:
        return {
            "weather_reasoning": f"Weather reasoning failed: {exc}",
            "errors": [f"weather_reasoning_node: {exc}"],
            "node_trace": ["weather_reasoner"],
        }
