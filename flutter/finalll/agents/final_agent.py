import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL_L5
from schemas import FinalLanguageOutput, UnifiedData

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_final(unified: UnifiedData) -> FinalLanguageOutput:
    payload = unified.model_dump()
    prompt = f"""
You are ORCA Level 5.

Use ONLY the validated JSON below.
Never browse, call tools, invent values, invent sources, invent alerts, or upgrade uncertainty into certainty.
Respond in language code: {unified.intent.language}

VALIDATED DATA:
{json.dumps(payload, ensure_ascii=False)}

Rules:
- `assessment.safety_assessment` is authoritative for safety wording.
- Explicitly mention missing critical data.
- Never claim that a location is safe for navigation; this is decision support only.
- For PFZ, distinguish official advisory information from exact geospatial coordinates.
- For productivity, distinguish environmental indicators from actual fish abundance.
- If an official warning is active, lead with it.
- Provide concise observations and practical next actions.
Return only JSON with: status, summary, observations, recommendations.
"""
    response = client.models.generate_content(
        model=GEMINI_MODEL_L5,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalLanguageOutput.model_json_schema(),
            temperature=0.2,
        ),
    )
    if not response.text:
        raise RuntimeError("Level 5 returned empty output")
    return FinalLanguageOutput.model_validate_json(response.text)
