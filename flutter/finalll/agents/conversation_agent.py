import json
import re
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL_L1
from schemas import Intent

client = genai.Client(api_key=GEMINI_API_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# Offline greeting / small-talk detector.
#
# Runs BEFORE the (slow, paid) Level-1 Gemini call so common greetings like
# "hi", "hello", "thank you" are answered instantly and never fail on a missing
# location. Returns a friendly reply string, or None if the message is a real
# data query that should go through the full pipeline.
# ─────────────────────────────────────────────────────────────────────────────

_GREETING_PHRASES = {
    "hi", "hii", "hiii", "hello", "hellooo", "hey", "heyy", "hola",
    "namaste", "namaskar", "namaskaram", "vanakkam", "yo", "hiya",
    "greetings", "howdy", "good morning", "good afternoon", "good evening",
    "good day", "good night",
    "how are you", "how are you doing", "whats up", "what's up",
    "who are you", "what are you", "what can you do",
    "what can you help me with", "what can i ask you", "tell me about yourself",
    "thank you", "thanks", "thank u", "thx", "thankyou", "ty",
    "help", "help me", "help me please", "help please", "need help",
}

# Words that open a short social message: "hi there", "hello samudra", ...
_GREETING_FIRST_WORDS = {
    "hi", "hii", "hiii", "hello", "hey", "heyy", "hola", "namaste", "hiya", "yo",
}


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)  # punctuation -> space
    t = re.sub(r"\s+", " ", t)      # collapse whitespace
    return t.strip()


def detect_greeting(message: str):
    n = _normalize(message)
    if not n:
        return None
    if n in _GREETING_PHRASES:
        return _greeting_reply()
    tokens = n.split()
    # A very short message that opens with a greeting word ("hi there",
    # "hello samudra", "hey") is treated as a greeting, not a data request.
    if len(tokens) <= 3 and any(t in _GREETING_FIRST_WORDS for t in tokens):
        return _greeting_reply()
    return None


def detect_language(message: str) -> str:
    for ch in message:
        if "\u0900" <= ch <= "\u097f":
            return "hi"   # Devanagari (Hindi)
        if "\u0c00" <= ch <= "\u0c7f":
            return "te"   # Telugu
        if "\u0b80" <= ch <= "\u0bff":
            return "ta"   # Tamil
        if "\u0c80" <= ch <= "\u0cff":
            return "kn"   # Kannada
        if "\u0d00" <= ch <= "\u0d7f":
            return "ml"   # Malayalam
        if "\u0980" <= ch <= "\u09ff":
            return "bn"   # Bengali
    return "en"


def _greeting_reply() -> str:
    return (
        "Namaste! I'm Samudra AI, your ocean intelligence assistant. "
        "I can fetch live marine conditions (waves, currents, sea temperature), "
        "weather, hazards and fishing advisories for any coastal location. "
        "Try asking me something like \"What are the ocean conditions near "
        "Kochi?\" or just tell me where you are and I'll show the current "
        "conditions."
    )


def parse_user_query(query: str, supplied_location=None) -> Intent:
    prompt = f"""
You are ORCA Level 1, the conversational intent agent.
Convert the user request to JSON for downstream tools.

USER: {query}
SUPPLIED LOCATION: {supplied_location or 'none'}

Detect the language and set `language` to an ISO-like language code (en, hi, te, ta, kn, ml, bn, mr, or another suitable code).

Treat these broad requests as specific parameter groups:
- sea conditions => SST, wave height, wave period, wave direction, current speed/direction, sea level
- weather => wind speed/direction, pressure, precipitation, weather code
- fishing productivity => SST, chlorophyll, currents, relevant historical indicators
- safe venture / safe fishing => marine + weather + hazard + tide/sea level
- PFZ => nearest PFZ / fishing advisory
- route => safe route optimization
- alerts => cyclone, lightning, severe weather, wave/wind hazards

Do not invent coordinates. If the user supplied a location name but not coordinates, leave lat/lon null.
Return ONLY JSON.
"""
    response = client.models.generate_content(
        model=GEMINI_MODEL_L1,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Intent.model_json_schema(),
            temperature=0,
        ),
    )
    if not response.text:
        raise RuntimeError("Level 1 returned empty output")
    obj = json.loads(response.text)
    if supplied_location:
        obj["location"] = {
            **obj.get("location", {}),
            **supplied_location.model_dump(exclude_none=True),
        }
    # Expand broad language that models sometimes leave unchanged.
    if obj.get("requested_parameters") == ["sea conditions"]:
        obj["requested_parameters"] = [
            "sea_surface_temperature", "wave_height", "wave_period",
            "wave_direction", "current_speed", "current_direction",
            "sea_level", "wind_speed", "wind_direction", "pressure",
            "precipitation", "weather_code",
        ]
    return Intent.model_validate(obj)
