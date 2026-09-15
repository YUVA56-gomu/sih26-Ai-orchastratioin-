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
from prompts import WEATHER_REASONER


def weather_reasoning_node(state: SamudraState) -> SamudraState:
    """Interpret weather evidence for the user's query."""

    weather = state.get("weather_data", {})
    if weather.get("status") in ("SKIPPED", "BLOCKED"):
        return {
            "weather_reasoning": f"Weather data unavailable: {weather.get('reason', weather.get('status'))}",
            "node_trace": ["weather_reasoner"],
        }

    query = state.get("query_in_english") or state.get("user_query", "")

    # Trim hourly data to avoid token overflow — send current + first 24h
    weather_trimmed = {k: v for k, v in weather.items() if k != "hourly"}
    hourly = weather.get("hourly", {})
    weather_trimmed["hourly_24h"] = {
        k: v[:24] if isinstance(v, list) else v
        for k, v in hourly.items()
    }

    context = (
        f"USER QUERY: {query}\n\n"
        f"WEATHER DATA:\n{json.dumps(weather_trimmed, indent=2)[:1500]}"
    )

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=WEATHER_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "weather_reasoning": response.content.strip(),
            "node_trace": ["weather_reasoner"],
        }
    except Exception as exc:
        return {
            "weather_reasoning": f"Weather reasoning failed: {exc}",
            "errors": [f"weather_reasoning_node: {exc}"],
            "node_trace": ["weather_reasoner"],
        }
