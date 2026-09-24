from schemas import DataQuality

PARAMETERS = [
    "sea_surface_temperature", "wave_height", "wave_period", "wave_direction",
    "current_speed", "current_direction", "sea_level", "wind_speed", "wind_direction",
    "pressure", "precipitation", "weather_code", "salinity", "chlorophyll", "mixed_layer_depth"
]


def risk_band(value, moderate, high):
    if value is None:
        return "unknown"
    if value >= high:
        return "high"
    if value >= moderate:
        return "moderate"
    return "low"


def fuse(intent, location, conditions, hazards, pfz, geofences, route, evidence, sources):
    available, missing = [], []
    for p in PARAMETERS:
        dp = getattr(conditions, p)
        if dp.value is None:
            dp.status = "unavailable"
            missing.append(p)
        else:
            available.append(p)

    quality = DataQuality(
        requested=len(intent.requested_parameters) or len(PARAMETERS),
        available=len(available),
        completeness_percent=round(100*len(available)/len(PARAMETERS), 1),
        missing=missing,
        source_count=len(sources) + len(evidence),
    )

    wave = risk_band(conditions.wave_height.value, 1.5, 3.0)
    wind = risk_band(conditions.wind_speed.value, 25, 45)
    current = risk_band(conditions.current_speed.value, 1.5, 3.0)

    hazard_high = any(h.severity == "high" for h in hazards)
    restricted = any((g.get("inside") if isinstance(g, dict) else getattr(g, "inside", False)) for g in geofences)

    if restricted or hazard_high:
        overall = "high"
    elif wave == "high" or wind == "high" or current == "high":
        overall = "high"
    elif "moderate" in {wave, wind, current}:
        overall = "moderate"
    elif quality.completeness_percent < 60:
        overall = "unknown"
    else:
        overall = "low"

    # Never call this a safe-to-navigate decision if critical evidence is missing.
    critical_missing = any(
        x in missing for x in ["wave_height", "wind_speed"]
    )
    safety = "insufficient_data_for_safety_assessment" if critical_missing else overall

    confidence_values = [getattr(conditions, p).confidence for p in available if getattr(conditions, p).confidence > 0]
    confidence = round(sum(confidence_values)/len(confidence_values), 2) if confidence_values else 0.0

    assessment = {
        "overall_status": overall,
        "safety_assessment": safety,
        "wave_risk": wave,
        "wind_risk": wind,
        "current_risk": current,
        "marine_health_status": "partial" if conditions.chlorophyll.value is not None else "not_assessed",
        "confidence": confidence,
    }
    return quality, assessment
