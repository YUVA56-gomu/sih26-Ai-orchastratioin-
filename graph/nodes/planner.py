"""
graph/nodes/planner.py
───────────────────────
Node 3 — Planner

Decomposes the user query into a structured execution plan:
which domains to fetch, what time window, location text, etc.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import PLANNER

# Default plan used if LLM fails
_FALLBACK_PLAN = {
    "intent": "general",
    "location_text": "",
    "coordinates_provided": False,
    "latitude": None,
    "longitude": None,
    "time_request": "now",
    "forecast_days": 1,
    "domains_needed": ["ocean", "weather", "geofence"],
    "needs_safety": True,
    "needs_fishery": False,
    "needs_navigation": False,
}


def planner_node(state: SamudraState) -> SamudraState:
    """Produce a structured execution plan for the query."""

    query = state.get("query_in_english") or state.get("user_query", "")
    intent = state.get("intent", "general")

    if not query:
        return {
            "plan": _FALLBACK_PLAN,
            "errors": ["planner_node: empty query"],
            "node_trace": ["planner"],
        }

    from graph.nodes.utils import format_recent_history, format_active_context

    hist_text = format_recent_history(state)
    ctx_text = format_active_context(state)

    context_blocks = [f"Intent already classified as: {intent}"]
    if hist_text:
        context_blocks.append(hist_text)
    if ctx_text:
        context_blocks.append(ctx_text)
    context_blocks.append(f"Current User query: {query}")

    context = "\n\n".join(context_blocks)

    try:
        llm = get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=PLANNER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        raw = extract_text(response)

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        plan = json.loads(raw)

        # Ensure required keys exist with safe defaults
        plan.setdefault("domains_needed", ["ocean", "weather", "geofence"])
        plan.setdefault("forecast_days", 1)
        plan.setdefault("needs_safety", False)
        plan.setdefault("needs_fishery", False)
        plan.setdefault("needs_navigation", False)
        plan.setdefault("coordinates_provided", False)
        plan.setdefault("latitude", None)
        plan.setdefault("longitude", None)
        plan.setdefault("time_request", "now")
        plan.setdefault("location_text", "")

        return {
            "plan": plan,
            "node_trace": ["planner"],
        }

    except Exception as exc:
        return {
            "plan": _FALLBACK_PLAN,
            "errors": [f"planner_node: {exc}"],
            "node_trace": ["planner"],
        }
