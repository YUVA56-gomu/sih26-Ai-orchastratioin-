"""
graph/nodes/summarizer.py
───────────────────────────
Node — Conversational Context Summarizer 🧠

Compresses older conversation turns into a rolling context_summary when the total
message count exceeds SUMMARY_THRESHOLD_MESSAGES, leaving a bounded window of recent
raw messages (RECENT_MESSAGES_WINDOW) intact.

Does NOT replace or overwrite active_context (which remains the deterministic source
of truth for location, coordinates, time_request, topic, and artifacts).
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text

# Configurable history threshold and window constants
SUMMARY_THRESHOLD_MESSAGES = 6  # Trigger summarization after 6 messages (3 turns)
RECENT_MESSAGES_WINDOW = 4      # Keep last 4 messages (2 turns) as raw unsummarized turns

_SUMMARIZER_PROMPT = """
You are SAMUDRA.AI's Conversational Memory Summarizer.

Summarize the key information, requested locations, user preferences, vessel types, and ongoing topics from the older turns of this conversation into a concise, high-density summary (max 3-4 bullet points).

Rules:
- Focus on retaining critical context, user intent, requested locations, and preferences.
- Incorporate the existing summary (if provided below) with the older turns to produce a unified rolling summary.
- Do NOT fabricate facts, coordinates, or locations not present in the conversation.
- Return ONLY the updated summary text.
"""


def summarizer_node(state: SamudraState) -> SamudraState:
    """Conditionally summarize older conversation turns into state['context_summary']."""

    msgs = state.get("messages") or state.get("conversation_history") or []
    if len(msgs) <= SUMMARY_THRESHOLD_MESSAGES:
        return {}

    existing_summary = state.get("context_summary") or ""
    older_messages = msgs[:-RECENT_MESSAGES_WINDOW]

    # Format older messages for summarization prompt
    older_formatted = []
    for m in older_messages:
        if isinstance(m, dict):
            role = m.get("role", "user").capitalize()
            content = m.get("content") or m.get("text") or ""
        else:
            role_raw = getattr(m, "type", "user").lower()
            role = "User" if role_raw in ("human", "user") else ("Assistant" if role_raw in ("ai", "assistant") else role_raw.capitalize())
            content = getattr(m, "content", str(m))
        if content:
            older_formatted.append(f"{role}: {content}")

    if not older_formatted:
        return {}

    prompt_parts = []
    if existing_summary:
        prompt_parts.append(f"EXISTING SUMMARY:\n{existing_summary}")
    prompt_parts.append("OLDER CONVERSATION TURNS TO SUMMARIZE:\n" + "\n".join(older_formatted))

    prompt_text = "\n\n".join(prompt_parts)

    try:
        llm = get_llm(temperature=0.2)
        messages = [
            SystemMessage(content=_SUMMARIZER_PROMPT),
            HumanMessage(content=prompt_text),
        ]
        response = llm.invoke(messages)
        new_summary = extract_text(response)
        if not new_summary:
            new_summary = existing_summary
    except Exception as exc:
        new_summary = existing_summary

    return {
        "context_summary": new_summary,
        "node_trace": ["summarizer"],
    }
