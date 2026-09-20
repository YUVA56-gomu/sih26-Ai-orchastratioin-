"""
graph/nodes/fast_responder.py
───────────────────────────────
Node — Fast Path Responder ⚡

Executes simple, low-cost queries (greetings, general definitions,
single-tool factual lookups) directly without invoking the full multi-agent
planning, 5-collector fanout, anti-hallucination gate, risk engine,
or specialist reasoners.

Preserves conversation context and updates active_context identically.
"""

from __future__ import annotations

import json
import re
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text, format_recent_history, format_active_context
from tools.location import resolve_location
from tools.copernicus_service import get_copernicus_marine_snapshot
from tools.weather_service import get_weather_conditions
from tools.marine_service import get_marine_conditions

_FAST_PROMPT = """
You are SAMUDRA.AI, an expert AI Marine Intelligence Assistant.

Provide a clear, helpful, accurate, and concise response to the user's query.

Rules:
- Be direct, professional, and friendly.
- If marine/weather data is provided below, incorporate the numbers accurately into your answer.
- Keep the response short, clear, and structured.
"""


def fast_responder_node(state: SamudraState) -> SamudraState:
    """Execute simple queries via Fast Path ⚡."""

    raw_query = state.get("user_query", "")
    query = state.get("query_in_english") or raw_query
    active_ctx = dict(state.get("active_context") or {})
    hist_text = format_recent_history(state)
    ctx_text = format_active_context(state)

    resolved_loc = None
    tool_evidence = None

    # Check if query asks for a location-specific single-tool datum (SST, weather, waves)
    lower_q = query.lower()
    needs_loc = any(kw in lower_q for kw in ["near", "at", "off", "in", "for", "around", "where"]) or bool(active_ctx.get("location"))

    # Attempt location extraction if location keyword or active_context exists
    if needs_loc:
        loc_text = ""
        # Generic references
        generic_refs = {"there", "it", "here", "the spot", "closest one", "that area", "that location", "same place"}
        words = set(re.findall(r'\b[a-z]+\b', lower_q))
        
        # Look for explicit place name in query
        loc_match = re.search(r'\b(?:near|at|off|in|for|about|to|around)\b\s+([A-Za-z]+)', query, re.IGNORECASE)
        if loc_match:
            candidate = loc_match.group(1).strip()
            if candidate.lower() not in generic_refs and candidate.lower() not in {"the", "a", "an", "what", "which", "how", "waves", "weather", "sst", "wind"}:
                loc_text = candidate

        # Fallback to active_context if generic or missing
        if not loc_text or loc_text.lower() in generic_refs:
            existing = active_ctx.get("location")
            if isinstance(existing, dict) and existing.get("status") == "FOUND":
                resolved_loc = existing
        else:
            try:
                res = resolve_location(loc_text)
                if res.get("status") == "FOUND":
                    resolved_loc = res
                else:
                    existing = active_ctx.get("location")
                    if isinstance(existing, dict) and existing.get("status") == "FOUND":
                        resolved_loc = existing
            except Exception:
                existing = active_ctx.get("location")
                if isinstance(existing, dict) and existing.get("status") == "FOUND":
                    resolved_loc = existing

        # If location resolved, fetch single data source based on query topic
        if resolved_loc and resolved_loc.get("status") == "FOUND":
            lat = resolved_loc["latitude"]
            lon = resolved_loc["longitude"]
            active_ctx["location"] = resolved_loc

            try:
                if any(w in lower_q for w in ["sst", "temperature", "sea surface", "current"]):
                    tool_evidence = {"source": "Copernicus Ocean", "data": get_copernicus_marine_snapshot(lat, lon)}
                    active_ctx["topic"] = "ocean"
                elif any(w in lower_q for w in ["wave", "swell", "sea state"]):
                    tool_evidence = {"source": "Open-Meteo Marine Waves", "data": get_marine_conditions(lat, lon)}
                    active_ctx["topic"] = "ocean"
                elif any(w in lower_q for w in ["weather", "wind", "rain", "temperature"]):
                    tool_evidence = {"source": "Open-Meteo Weather", "data": get_weather_conditions(lat, lon)}
                    active_ctx["topic"] = "weather"
            except Exception as exc:
                tool_evidence = {"error": f"Tool execution failed: {exc}"}

    # Build context for Fast LLM prompt
    prompt_parts = []
    if hist_text:
        prompt_parts.append(hist_text)
    if ctx_text:
        prompt_parts.append(ctx_text)
    prompt_parts.append(f"CURRENT QUERY: {query}")

    if resolved_loc:
        prompt_parts.append(f"TARGET LOCATION: {resolved_loc.get('name')} (Lat: {resolved_loc.get('latitude')}, Lon: {resolved_loc.get('longitude')})")
    if tool_evidence:
        prompt_parts.append(f"FETCHED DATA EVIDENCE:\n{json.dumps(tool_evidence, indent=2)[:1000]}")

    prompt_text = "\n\n".join(prompt_parts)

    try:
        llm = get_llm(temperature=0.3)
        messages = [
            SystemMessage(content=_FAST_PROMPT),
            HumanMessage(content=prompt_text),
        ]
        response = llm.invoke(messages)
        final_text = extract_text(response)
    except Exception as exc:
        final_text = f"Hello! I am SAMUDRA.AI. How can I assist you with marine intelligence today?"

    from tools.artifact_factory import (
        create_location_card_artifact,
        create_weather_card_artifact,
        create_marine_conditions_artifact,
    )

    artifacts_list = []
    if resolved_loc:
        loc_card = create_location_card_artifact(resolved_loc)
        if loc_card:
            artifacts_list.append(loc_card)

    if tool_evidence and isinstance(tool_evidence, dict) and "data" in tool_evidence:
        source = tool_evidence.get("source", "")
        data = tool_evidence["data"]
        if "Weather" in source:
            wx_card = create_weather_card_artifact(resolved_loc, data)
            if wx_card:
                artifacts_list.append(wx_card)
        elif "Marine" in source:
            marine_card = create_marine_conditions_artifact(resolved_loc, data)
            if marine_card:
                artifacts_list.append(marine_card)

    if artifacts_list:
        active_ctx["active_artifacts"] = artifacts_list
        active_ctx["selected_artifact"] = artifacts_list[0]

    result: SamudraState = {
        "final_response_english": final_text,
        "route_path": "FAST",
        "active_context": active_ctx,
        "artifacts": artifacts_list,
        "node_trace": ["fast_responder"],
    }
    if resolved_loc:
        result["location"] = resolved_loc

    return result
