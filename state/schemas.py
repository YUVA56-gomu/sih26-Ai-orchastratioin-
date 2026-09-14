from __future__ import annotations

STATE_KEYS = {
    "plan": "orca_plan",
    "location": "orca_location",
    "ocean": "orca_ocean_data",
    "weather": "orca_weather_data",
    "geofence": "orca_geofence_data",
    "risk": "orca_risk_assessment",
    "ocean_reasoning": "orca_ocean_reasoning",
    "weather_reasoning": "orca_weather_reasoning",
    "fishery_reasoning": "orca_fishery_reasoning",
    "safety_reasoning": "orca_safety_reasoning",
    "peer_review": "orca_peer_review",
    "review": "orca_review",
    "final": "orca_final_response",
}


def key(name: str) -> str:
    return STATE_KEYS[name]
