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
    """Build an enriched Potential Fishing Zone (PFZ) map artifact."""
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
            "pfz_status": fishery_data.get("pfz_status", fishery_data.get("status", "CALCULATED")),
            "candidates": fishery_data.get("candidates") or fishery_data.get("pfz_candidates", []),
            "thermal_fronts": fishery_data.get("thermal_fronts", []),
            "chlorophyll_features": fishery_data.get("chlorophyll_features", []),
            "bulletin": fishery_data.get("bulletin", {"source": "INCOIS", "status": "UNAVAILABLE"}),
            "provenance": fishery_data.get("provenance", []),
            "recommendation": fishery_data.get("recommendation", fishery_data.get("important", "")),
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
    daily = weather_data.get("daily", {}) if isinstance(weather_data, dict) else {}
    raw_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
    hourly_bounded = {
        k: v[:24] if isinstance(v, list) else v
        for k, v in raw_hourly.items()
    } if isinstance(raw_hourly, dict) else {}

    units = {
        "current": weather_data.get("current_units", {}) if isinstance(weather_data, dict) else {},
        "hourly": weather_data.get("hourly_units", {}) if isinstance(weather_data, dict) else {},
        "daily": weather_data.get("daily_units", {}) if isinstance(weather_data, dict) else {},
    }

    prov = weather_data.get("provenance", {
        "source": "Open-Meteo Weather API",
        "provider": "Open-Meteo",
        "data_class": "FORECAST",
    }) if isinstance(weather_data, dict) else {}

    return create_artifact(
        artifact_type="weather_card",
        artifact_id=f"wx_card_{lat}_{lon}",
        title=f"Weather Forecast — {name}",
        description=f"Temperature: {curr.get('temperature_2m')}°C | Wind: {curr.get('wind_speed_10m')} km/h",
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "current": curr,
            "daily": daily,
            "hourly": hourly_bounded,
            "units": units,
            "provenance": prov,
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


def create_ocean_conditions_artifact(location: dict[str, Any], ocean_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a dedicated ocean hydrodynamics card artifact (Copernicus Marine)."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    if not isinstance(ocean_data, dict) or ocean_data.get("status") in ("SKIPPED", "BLOCKED", "ERROR", None):
        return None

    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")

    obs = ocean_data.get("observations", {})
    temp_obs = obs.get("temperature", {})
    sal_obs = obs.get("salinity", {})
    curr_obs = obs.get("currents", {})
    prof_obs = obs.get("current_profile", {})
    wave_obs = obs.get("waves", {})

    temp_data = {
        "value": temp_obs.get("value"),
        "unit": temp_obs.get("unit", "°C"),
        "observation_time": temp_obs.get("observation_time"),
    } if temp_obs else {}

    sal_data = {
        "value": sal_obs.get("value"),
        "unit": sal_obs.get("unit", "psu"),
        "observation_time": sal_obs.get("observation_time"),
    } if sal_obs else {}

    currents_data = {
        "speed_ms": curr_obs.get("speed_ms"),
        "direction_deg": curr_obs.get("direction_deg"),
        "u_ms": curr_obs.get("u_ms"),
        "v_ms": curr_obs.get("v_ms"),
        "profile": prof_obs.get("profile", []) if prof_obs else [],
    } if (curr_obs or prof_obs) else {}

    waves_data = {
        "significant_wave_height_m": wave_obs.get("significant_wave_height_m"),
        "mean_wave_period_s": wave_obs.get("mean_wave_period_s"),
        "wave_direction_deg": wave_obs.get("wave_direction_deg"),
    } if wave_obs else {}

    provenance = ocean_data.get("provenance", [])
    retrieved_at = ocean_data.get("retrieved_at", "")

    return create_artifact(
        artifact_type="ocean_card",
        artifact_id=f"ocean_card_{lat}_{lon}",
        title=f"Ocean Hydrodynamics — {name}",
        description=f"SST: {temp_data.get('value')}°C | Salinity: {sal_data.get('value')} psu | Current: {currents_data.get('speed_ms')} m/s",
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "temperature": temp_data,
            "salinity": sal_data,
            "currents": currents_data,
            "waves": waves_data,
            "provenance": provenance,
            "retrieved_at": retrieved_at,
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


def create_tide_card_artifact(location: dict[str, Any], tide_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a tide forecast card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    if not isinstance(tide_data, dict) or tide_data.get("status") in ("SKIPPED", "BLOCKED", "ERROR", None):
        return None

    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    curr = tide_data.get("current", {})
    next_high = tide_data.get("next_high_tide") or {}
    next_low = tide_data.get("next_low_tide") or {}

    desc_parts = []
    if curr.get("sea_level_m") is not None:
        desc_parts.append(f"Sea Level: {curr.get('sea_level_m')}m")
    if curr.get("phase"):
        desc_parts.append(f"Phase: {curr.get('phase')}")
    if next_high.get("height_m") is not None:
        desc_parts.append(f"Next High: {next_high.get('height_m')}m")

    return create_artifact(
        artifact_type="tide_card",
        artifact_id=f"tide_card_{lat}_{lon}",
        title=f"Tide Dynamics — {name}",
        description=" | ".join(desc_parts) if desc_parts else f"Tide information for {name}",
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "status": tide_data.get("status", "AVAILABLE"),
            "current": curr,
            "extrema": tide_data.get("extrema", []),
            "next_high_tide": next_high,
            "next_low_tide": next_low,
            "hourly_timeseries": tide_data.get("hourly_timeseries", []),
            "tidal_range_m": tide_data.get("tidal_range_m"),
            "datum": tide_data.get("datum", "MSL_MODELLED"),
            "provenance": tide_data.get("provenance", {}),
            "disclaimer": tide_data.get("disclaimer", ""),
        },
    )


def create_hazard_alert_artifact(location: dict[str, Any], hazard_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build an official hazard alert card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    if not isinstance(hazard_data, dict):
        return None

    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    status = hazard_data.get("status", "UNAVAILABLE")
    alerts = hazard_data.get("alerts", [])

    if status == "ACTIVE" and alerts:
        first_alert = alerts[0] if isinstance(alerts[0], dict) else {}
        title = f"Official Warning: {first_alert.get('title', 'Marine Hazard')}"
        desc = f"Severity: {first_alert.get('severity', 'ADVISORY')} | Source: {first_alert.get('source', 'INCOIS')}"
    else:
        title = f"Official Hazard Feed — {name}"
        desc = "No active official hazard alerts reported for this location."

    return create_artifact(
        artifact_type="hazard_alert",
        artifact_id=f"hazard_alert_{lat}_{lon}",
        title=title,
        description=desc,
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "status": status,
            "alerts": alerts,
            "advice": hazard_data.get("advice", ""),
            "provenance": hazard_data.get("provenance", {}),
        },
    )


def create_geofence_alert_artifact(location: dict[str, Any], geofence_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a geofence / spatial boundary alert card artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    if not isinstance(geofence_data, dict):
        return None

    inside = geofence_data.get("inside_restricted_zone", False)
    proximity = geofence_data.get("proximity_warning", False)

    if not inside and not proximity:
        return None

    lat = location.get("latitude")
    lon = location.get("longitude")
    name = location.get("name", "Selected Region")
    matches = geofence_data.get("matched_zones") or geofence_data.get("matches") or []

    if inside:
        first_match = matches[0] if matches and isinstance(matches[0], dict) else {}
        z_name = first_match.get("name") or first_match.get("zone_name") or "Restricted Zone"
        title = f"Geofence Alert: Intersected {z_name}"
        desc = f"Coordinates ({lat}°N, {lon}°E) fall inside designated polygon: {z_name}."
    else:
        title = f"Boundary Proximity Warning — {name}"
        nearest = geofence_data.get("nearest_boundary") or {}
        dist = nearest.get("distance_km", "N/A")
        z_name = nearest.get("zone_name", "Spatial Boundary")
        desc = f"Location is within boundary proximity buffer ({dist} km from {z_name})."

    return create_artifact(
        artifact_type="geofence_alert",
        artifact_id=f"geofence_alert_{lat}_{lon}",
        title=title,
        description=desc,
        data={
            "location": {"name": name, "latitude": lat, "longitude": lon},
            "inside_restricted_zone": inside,
            "proximity_warning": proximity,
            "matched_zones": matches,
            "nearest_boundary": geofence_data.get("nearest_boundary", {}),
            "layers": geofence_data.get("layers", []),
            "provenance": geofence_data.get("provenance", {}),
        },
    )


def create_route_map_artifact(location: dict[str, Any], route_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build a deterministic marine route map UI artifact."""
    if not isinstance(location, dict) or location.get("status") != "FOUND":
        return None
    if not isinstance(route_data, dict):
        return None

    origin = route_data.get("origin") or {}
    dest = route_data.get("destination") or {}
    status = route_data.get("status", "UNAVAILABLE")

    o_name = origin.get("name", "Origin")
    d_name = dest.get("name", "Destination")
    dist_km = route_data.get("distance_km", 0.0)

    if status == "OK":
        title = f"Marine Route: {o_name} to {d_name}"
        desc = f"Calculated Distance: {dist_km} km | Route nodes: {len(route_data.get('waypoints', []))}"
    else:
        title = f"Marine Route Request: {o_name} to {d_name}"
        desc = "Route calculation unavailable or path blocked by spatial/environmental constraints."

    return create_artifact(
        artifact_type="route_map",
        artifact_id=f"route_map_{origin.get('latitude')}_{origin.get('longitude')}_to_{dest.get('latitude')}_{dest.get('longitude')}",
        title=title,
        description=desc,
        data={
            "status": status,
            "origin": origin,
            "destination": dest,
            "waypoints": route_data.get("waypoints", []),
            "segments": route_data.get("segments", []),
            "route_geometry": route_data.get("route_geometry", {"type": "LineString", "coordinates": []}),
            "distance_km": dist_km,
            "estimated_cost": route_data.get("estimated_cost", 0.0),
            "environmental_summary": route_data.get("environmental_summary", {}),
            "data_completeness": route_data.get("data_completeness", {}),
            "verification": route_data.get("verification", {
                "eez": "INFORMATIONAL",
                "mpa": "UNAVAILABLE",
                "naval": "UNAVAILABLE",
            }),
            "provenance": route_data.get("provenance", []),
            "warnings": route_data.get("warnings", []),
        },
    )
