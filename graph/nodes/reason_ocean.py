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
from prompts import OCEAN_REASONER


def ocean_reasoning_node(state: SamudraState) -> SamudraState:
    """Interpret ocean evidence for the user's query."""

    ocean = state.get("ocean_data", {})
    if ocean.get("status") in ("SKIPPED", "BLOCKED"):
        return {
            "ocean_reasoning": f"Ocean data unavailable: {ocean.get('reason', ocean.get('status'))}",
            "node_trace": ["ocean_reasoner"],
        }

    query = state.get("query_in_english") or state.get("user_query", "")
    context = (
        f"USER QUERY: {query}\n\n"
        f"OCEAN DATA:\n{json.dumps(ocean, indent=2)[:1200]}"
    )

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=OCEAN_REASONER),
            HumanMessage(content=context),
        ]
        response = llm.invoke(messages)
        return {
            "ocean_reasoning": response.content.strip(),
            "node_trace": ["ocean_reasoner"],
        }
    except Exception as exc:
        return {
            "ocean_reasoning": f"Ocean reasoning failed: {exc}",
            "errors": [f"ocean_reasoning_node: {exc}"],
            "node_trace": ["ocean_reasoner"],
        }
