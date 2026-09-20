"""
graph/nodes/reason_fishery.py
──────────────────────────────
Specialist Reasoning — Fishery

Interprets PFZ / SST / fishery evidence for the user's query.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import FISHERY_REASONER


def fishery_reasoning_node(state: SamudraState) -> SamudraState:
    """Interpret fishery evidence for the user's query."""

    fishery = state.get("fishery_data", {})
    ocean = state.get("ocean_data", {})

    if fishery.get("status") in ("SKIPPED", "BLOCKED") and ocean.get("status") in ("SKIPPED", "BLOCKED", None):
        return {
            "fishery_reasoning": "Fishery data unavailable. No PFZ or ocean evidence to interpret.",
            "node_trace": ["fishery_reasoner"],
        }

    query = state.get("query_in_english") or state.get("user_query", "")
    context = (
        f"USER QUERY: {query}\n\n"
        f"FISHERY/PFZ DATA:\n{json.dumps(fishery, indent=2)[:800]}\n\n"
        f"OCEAN DATA (for SST context):\n{json.dumps(ocean, indent=2)[:600]}"
    )

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=FISHERY_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "fishery_reasoning": extract_text(response),
            "node_trace": ["fishery_reasoner"],
        }
    except Exception as exc:
        return {
            "fishery_reasoning": f"Fishery reasoning failed: {exc}",
            "errors": [f"fishery_reasoning_node: {exc}"],
            "node_trace": ["fishery_reasoner"],
        }
