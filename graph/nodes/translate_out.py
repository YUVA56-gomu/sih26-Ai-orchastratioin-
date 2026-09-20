"""
graph/nodes/translate_out.py
─────────────────────────────
Output Translation Node

Translates the English response back to the user's detected language.
If the user's language is English, passes through directly.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from state.schema import SamudraState
from graph.llm import get_llm
from graph.nodes.utils import extract_text

_TRANSLATE_OUT_PROMPT = """
You are a translation assistant for SAMUDRA.AI, a marine intelligence system.

Translate the following English text into {target_language}.

Rules:
- Preserve all numerical values exactly as written.
- Preserve marine and technical terms accurately.
- Keep the same structure and paragraph breaks.
- If the text is already in {target_language}, return it unchanged.
- Return ONLY the translated text, no preamble or explanation.
"""


def translate_out_node(state: SamudraState) -> SamudraState:
    """Translate the final English response to the user's language."""

    response_english = state.get("final_response_english", "")
    lang = state.get("detected_language", "en")

    # No translation needed for English
    if lang == "en" or not lang:
        return {
            "final_response": response_english,
            "node_trace": ["translate_out"],
        }

    if not response_english:
        return {
            "final_response": "",
            "errors": ["translate_out_node: empty response to translate"],
            "node_trace": ["translate_out"],
        }

    # Map ISO code to language name for the prompt
    _LANG_NAMES = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "ml": "Malayalam",
        "kn": "Kannada",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "pa": "Punjabi",
        "or": "Odia",
        "ur": "Urdu",
    }
    lang_name = _LANG_NAMES.get(lang, lang.upper())

    try:
        llm = get_llm(temperature=0.1)
        prompt = _TRANSLATE_OUT_PROMPT.format(target_language=lang_name)
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=response_english),
        ]
        response = llm.invoke(messages)
        return {
            "final_response": extract_text(response),
            "node_trace": ["translate_out"],
        }
    except Exception as exc:
        # Fallback: return English if translation fails
        return {
            "final_response": response_english,
            "errors": [f"translate_out_node: {exc}"],
            "node_trace": ["translate_out"],
        }
