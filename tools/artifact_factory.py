"""
tools/artifact_factory.py
───────────────────────────
Factory helper functions to produce standardized Artifact dictionaries
for SAMUDRA's Response & Artifact Protocol.

Artifacts represent structured UI payloads (maps, PFZ points, weather cards,
risk summaries, location cards) that frontends (Web, Flutter, etc.) can render.
"""

from __future__ import annotations
import uuid
from typing import Any, Optional


def create_artifact(
    artifact_type: str,
    title: str,
    data: dict[str, Any],
    description: Optional[str] = None,
    artifact_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Base helper to construct a valid Artifact dictionary."""
    return {
        "id": artifact_id or f"{artifact_type}_{uuid.uuid4().hex[:8]}",
        "type": artifact_type,
        "title": title,
        "description": description or "",
        "data": data,
        "metadata": metadata or {},
    }


def create_location_card_artifact(location: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a location overview card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    name = location.get("name", "Target Location")
    lat = location.get("latitude")
    lon = location.get("longitude")
    return create_artifact(
        artifact_type="location_card",
        artifact_id=f"loc_{lat}_{lon}",
        title=f"Location: {name}",
        description=f"Coordinates: {lat}°N, {lon}°E",
        data={
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "country": location.get("country"),
            "admin1": location.get("admin1"),
        },
    )


def create_pfz_map_artifact(location: dict[str, Any], fishery_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a Potential Fishing Zone (PFZ) map artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    return create_artifact(
        artifact_type="pfz_map",
        artifact_id=f"pfz_map_{lat}_{lon}",
        title=f"PFZ Candidates near {name}",
        description="Pelagic fish aggregation candidates based on thermal fronts and chlorophyll gradients.",
        data={
            "location": {
                "name": name,
                "latitude": lat,
                "longitude": lon,
            },
            "pfz_status": fishery_data.get("pfz_status", fishery_data.get("status", "Calculated")),
            "candidates": fishery_data.get("candidates") or fishery_data.get("pfz_candidates", []),
            "recommendation": fishery_data.get("recommendation", ""),
        },
    )


def create_weather_card_artifact(location: dict[str, Any], weather_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a weather forecast card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    curr = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}
    return create_artifact(
        artifact_type="weather_card",
        artifact_id=f"wx_card_{lat}_{lon}",
        title=f"Weather Forecast — {name}",
        description=f"Temperature: {curr.get('temperature_2m')}°C | Wind: {curr.get('wind_speed_10m')} km/h",
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "current": curr,
            "daily": weather_data.get("daily", {}) if isinstance(weather_data, dict) else {},
        },
    )


def create_marine_conditions_artifact(location: dict[str, Any], marine_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a marine wave dynamics card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    curr = marine_data.get("current", {}) if isinstance(marine_data, dict) else {}
    return create_artifact(
        artifact_type="marine_conditions",
        artifact_id=f"marine_card_{lat}_{lon}",
        title=f"Marine Dynamics — {name}",
        description=f"Wave Height: {curr.get('wave_height')} m | Swell Period: {curr.get('swell_wave_period')} s",
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "current": curr,
        },
    )


def create_risk_summary_artifact(location: dict[str, Any], risk_assessment: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a safety risk summary artifact."""
    if not isinstance(risk_assessment, dict) or not risk_assessment.get("risk_level"):
        return None
    name = location.get("name", "Maritime Zone") if isinstance(location, dict) else "Maritime Zone"
    level = risk_assessment.get("risk_level", "UNKNOWN")
    score = risk_assessment.get("risk_score", -1)
    return create_artifact(
        artifact_type="risk_summary",
        artifact_id=f"risk_summary_{level.lower()}_{score}",
        title=f"Marine Safety Level: {level}",
        description=f"Calculated Risk Score: {score}/100 for {name}",
        data={
            "risk_level": level,
            "risk_score": score,
            "reasons": risk_assessment.get("reasons", []),
            "evaluated_parameters": risk_assessment.get("evaluated_parameters", {}),
        },
    )
