"""
graph/nodes/language.py
────────────────────────
Node 1 — Language Detection

Detects the language of the user's query using langdetect.
If not English, stores the original and a note for the planner.
Actual translation to English happens here using the LLM to keep
it simple and handle Indian regional scripts correctly.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm

_TRANSLATION_PROMPT = """
You are a translation assistant.

Detect the language of the input text and translate it to English.

Return ONLY a JSON object, no extra text:
{{
  "detected_language": "<ISO 639-1 code, e.g. en, hi, ta, te, bn, ml, kn, mr>",
  "language_name": "<English name of language>",
  "english_text": "<translated text, or original if already English>"
}}

If the text is already English, return detected_language as "en"
and english_text as the original text unchanged.
"""


def language_detection_node(state: SamudraState) -> SamudraState:
    """Detect language and translate query to English."""

    query = state.get("user_query", "").strip()

    if not query:
        return {
            "detected_language": "en",
            "query_in_english": "",
            "errors": ["language_node: empty user_query"],
            "node_trace": ["language_detection"],
        }

    try:
        llm = get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=_TRANSLATION_PROMPT),
            HumanMessage(content=query),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        return {
            "detected_language": data.get("detected_language", "en"),
            "query_in_english": data.get("english_text", query),
            "node_trace": ["language_detection"],
        }

    except Exception as exc:
        # Fallback: assume English
        return {
            "detected_language": "en",
            "query_in_english": query,
            "errors": [f"language_node: {exc}"],
            "node_trace": ["language_detection"],
        }
