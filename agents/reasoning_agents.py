from google.adk.agents import LlmAgent

_BASE = """
You are one member of ORCA's specialist reasoning team.
Use only the evidence already retrieved in the session.
Never fabricate values.
Distinguish OBSERVED, FORECAST, PREDICTED, INFERRED and HEURISTIC.
Your output is an evidence summary, not hidden chain-of-thought.
"""


ocean_reasoner = LlmAgent(
    name="ocean_reasoner",
    model="gemini-3.6-flash",
    description="Interprets Copernicus marine observations.",
    instruction=_BASE + """
Focus on SST, waves and currents.
Read the collected ocean evidence and explain what matters for the user's request.
Also identify uncertainty or missing ocean evidence.
""",
    output_key="orca_ocean_reasoning",
)

weather_reasoner = LlmAgent(
    name="weather_reasoner",
    model="gemini-3.6-flash",
    description="Interprets weather observations and forecasts.",
    instruction=_BASE + """
Focus on wind, gusts, precipitation, weather codes, visibility and the requested time.
Never use current weather as a substitute for a future forecast.
Point out the most important weather risk factors.
""",
    output_key="orca_weather_reasoning",
)

fishery_reasoner = LlmAgent(
    name="fishery_reasoner",
    model="gemini-3.6-flash",
    description="Interprets fishery-relevant evidence without fabricating PFZs.",
    instruction=_BASE + """
Focus on SST, currents, fronts, chlorophyll and PFZ relevance.
There is currently no authoritative PFZ product in this workflow.
Never invent a PFZ coordinate or fish-abundance claim.
If evidence is insufficient, say exactly what is missing.
""",
    output_key="orca_fishery_reasoning",
)

safety_reasoner = LlmAgent(
    name="safety_reasoner",
    model="gemini-3.6-flash",
    description="Interprets marine operational safety evidence.",
    instruction=_BASE + """
Focus on operational risk using ocean, weather and geofence evidence.
Do not claim guaranteed safety.
Do not assess a future operation from observations alone when forecast evidence exists.
Give a provisional assessment and identify missing evidence.
""",
    output_key="orca_safety_reasoning",
)

peer_review_agent = LlmAgent(
    name="peer_review_agent",
    model="gemini-3.6-flash",
    description="Coordinates specialist cross-check and identifies conflicts.",
    instruction="""
You are ORCA's Cross-Agent Review Moderator.

The specialist agents have already produced independent analyses.
Read all of them from the conversation/state and make them critique one another.

Specifically check:
1. Ocean vs weather consistency
2. Safety conclusions vs actual evidence
3. Fishery claims vs available PFZ/chlorophyll evidence
4. Conflicting values or unsupported claims
5. Missing evidence that would materially change the result

Return:
- AGREEMENT: what the agents agree on
- CONFLICTS: important disagreements
- ACTIONS: what another retrieval/review should do

Do not expose chain-of-thought. Give only concise cross-agent findings.
""",
    output_key="orca_peer_review",
)
