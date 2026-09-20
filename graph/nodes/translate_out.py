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

    from tools.artifact_factory import (
        create_location_card_artifact,
        create_pfz_map_artifact,
        create_weather_card_artifact,
        create_ocean_conditions_artifact,
        create_risk_summary_artifact,
    )

    existing_artifacts = list(state.get("artifacts") or [])
    active_ctx = dict(state.get("active_context") or {})

    if state.get("route_path") == "DEEP":
        loc = state.get("location", {})
        fish = state.get("fishery_data", {})
        risk = state.get("risk_assessment", {})
        wx = state.get("weather_data", {})
        oc = state.get("ocean_data", {})

        if fish and (fish.get("status") in ("OK", "Calculated", "HEURISTIC") or fish.get("candidates") or fish.get("pfz_candidates")):
            pfz_art = create_pfz_map_artifact(loc, fish)
            if pfz_art and not any(a.get("type") == "pfz_map" for a in existing_artifacts):
                existing_artifacts.append(pfz_art)

        if risk and risk.get("risk_level"):
            risk_art = create_risk_summary_artifact(loc, risk)
            if risk_art and not any(a.get("type") == "risk_summary" for a in existing_artifacts):
                existing_artifacts.append(risk_art)

        if wx and wx.get("current"):
            wx_art = create_weather_card_artifact(loc, wx)
            if wx_art and not any(a.get("type") == "weather_card" for a in existing_artifacts):
                existing_artifacts.append(wx_art)

        if oc and oc.get("observations"):
            oc_art = create_ocean_conditions_artifact(loc, oc)
            if oc_art and not any(a.get("type") == "ocean_card" for a in existing_artifacts):
                existing_artifacts.append(oc_art)

        if loc.get("status") == "FOUND" and not existing_artifacts:
            loc_art = create_location_card_artifact(loc)
            if loc_art:
                existing_artifacts.append(loc_art)

    if existing_artifacts:
        active_ctx["active_artifacts"] = existing_artifacts
        active_ctx["selected_artifact"] = existing_artifacts[0]

    def _make_response_payload(final_resp: str, err: str | None = None) -> SamudraState:
        user_query = state.get("user_query", "")
        user_msg = {"role": "user", "content": user_query}
        assistant_msg = {"role": "assistant", "content": final_resp}

        res: SamudraState = {
            "final_response": final_resp,
            "messages": [user_msg, assistant_msg],
            "conversation_history": [user_msg, assistant_msg],
            "artifacts": existing_artifacts,
            "active_context": active_ctx,
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
