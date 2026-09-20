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

    def _make_response_payload(final_resp: str, err: str | None = None) -> SamudraState:
        user_query = state.get("user_query", "")
        user_msg = {"role": "user", "content": user_query}
        assistant_msg = {"role": "assistant", "content": final_resp}

        res: SamudraState = {
            "final_response": final_resp,
            "messages": [user_msg, assistant_msg],
            "conversation_history": [user_msg, assistant_msg],
            "node_trace": ["translate_out"],
        }
        if err:
            res["errors"] = [err]
        return res

    # No translation needed for English
    if lang == "en" or not lang:
        return _make_response_payload(response_english)

    if not response_english:
        return _make_response_payload("", "translate_out_node: empty response to translate")

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
        return _make_response_payload(extract_text(response))
    except Exception as exc:
        # Fallback: return English if translation fails
        return _make_response_payload(response_english, f"translate_out_node: {exc}")
