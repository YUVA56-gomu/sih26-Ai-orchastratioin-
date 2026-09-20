"""
graph/nodes/reason_ocean.py
────────────────────────────
Specialist Reasoning — Ocean

Interprets Copernicus ocean evidence in context of the user's query.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import OCEAN_REASONER


def ocean_reasoning_node(state: SamudraState) -> SamudraState:
    """Interpret ocean evidence for the user's query."""

    ocean  = state.get("ocean_data", {})
    marine = state.get("marine_data", {})

    # Skip only when BOTH sources are unavailable
    ocean_blocked  = ocean.get("status") in ("SKIPPED", "BLOCKED")
    marine_blocked = marine.get("status") in ("SKIPPED", "BLOCKED", "ERROR", None)

    if ocean_blocked and marine_blocked:
        return {
            "ocean_reasoning": "Ocean data unavailable: both Copernicus and Open-Meteo Marine are blocked.",
            "node_trace": ["ocean_reasoner"],
        }

    query = state.get("query_in_english") or state.get("user_query", "")

    # Build context — label each source clearly so the LLM never conflates them
    context_parts = [f"USER QUERY: {query}"]

    if not ocean_blocked:
        context_parts.append(
            f"COPERNICUS MARINE DATA (source=satellite/model observation):\n"
            f"{json.dumps(ocean, indent=2)[:2500]}"
        )
    else:
        context_parts.append("COPERNICUS MARINE DATA: unavailable.")

    if not marine_blocked:
        context_parts.append(
            f"OPEN-METEO MARINE DATA (source=MODELLED — NOT observation):\n"
            f"{json.dumps(marine, indent=2)[:700]}"
        )
    else:
        context_parts.append("OPEN-METEO MARINE DATA: unavailable.")

    context = "\n\n".join(context_parts)

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=OCEAN_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "ocean_reasoning": extract_text(response),
            "node_trace": ["ocean_reasoner"],
        }
    except Exception as exc:
        return {
            "ocean_reasoning": f"Ocean reasoning failed: {exc}",
            "errors": [f"ocean_reasoning_node: {exc}"],
            "node_trace": ["ocean_reasoner"],
        }
