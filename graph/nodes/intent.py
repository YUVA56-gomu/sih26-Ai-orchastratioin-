"""
graph/nodes/intent.py
──────────────────────
Node 2 — Intent Router

Classifies the (English) query into one of the IntentType categories.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState, IntentType
from graph.llm import get_llm
from graph.nodes.utils import extract_text
from prompts import INTENT_ROUTER


def intent_router_node(state: SamudraState) -> SamudraState:
    """Classify user intent from the English query."""

    query = state.get("query_in_english") or state.get("user_query", "")

    if not query:
        return {
            "intent": IntentType.GENERAL,
            "errors": ["intent_node: empty query"],
            "node_trace": ["intent_router"],
        }

    try:
        llm = get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=INTENT_ROUTER),
            HumanMessage(content=query),
        ]
        response = llm.invoke(messages)
        raw = extract_text(response)

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        intent_str = data.get("intent", "general").lower()

        # Map to enum, fallback to GENERAL
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.GENERAL

        return {
            "intent": intent,
            "node_trace": ["intent_router"],
        }

    except Exception as exc:
        return {
            "intent": IntentType.GENERAL,
            "errors": [f"intent_node: {exc}"],
            "node_trace": ["intent_router"],
        }
