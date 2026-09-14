from __future__ import annotations


def _num(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def calculate_marine_risk(ocean: dict, weather: dict, geofence: dict) -> dict:
    """Deterministic first-pass risk scoring from already retrieved evidence."""
    score = 0
    reasons = []

    observations = ocean.get("observations", {}) if isinstance(ocean, dict) else {}
    waves = observations.get("waves", {})
    weather_current = weather.get("current", {}) if isinstance(weather, dict) else {}

    wave_height = _num(waves.get("significant_wave_height_m"))
    wind_speed = _num(weather_current.get("wind_speed_10m"))
    wind_gust = _num(weather_current.get("wind_gusts_10m"))
    precipitation = _num(weather_current.get("precipitation"))
    weather_code = _num(weather_current.get("weather_code"))

    if wave_height is not None:
        if wave_height >= 2.5:
            score += 40
            reasons.append("Very high significant wave height.")
        elif wave_height >= 1.5:
            score += 25
            reasons.append("Elevated significant wave height.")
        elif wave_height >= 1.0:
            score += 10
            reasons.append("Moderate wave conditions.")

    if wind_speed is not None:
        if wind_speed >= 45:
            score += 35
            reasons.append("Strong wind conditions.")
        elif wind_speed >= 30:
            score += 20
            reasons.append("Elevated wind conditions.")
        elif wind_speed >= 20:
            score += 8
            reasons.append("Moderate wind conditions.")

    if wind_gust is not None and wind_gust >= 45:
        score += 15
        reasons.append("Strong wind gust signal.")

    if weather_code is not None and weather_code >= 80:
        score += 20
        reasons.append("Heavy-weather precipitation code detected.")

    if precipitation is not None and precipitation >= 10:
        score += 10
        reasons.append("Heavy precipitation signal.")

    if geofence.get("inside_restricted_zone"):
        score += 50
        reasons.append("Location intersects a configured restricted zone.")

    score = min(score, 100)
    if score < 25:
        level = "LOW"
    elif score < 55:
        level = "MODERATE"
    elif score < 80:
        level = "HIGH"
    else:
        level = "VERY HIGH"

    return {
        "risk_level": level,
        "risk_score": score,
        "reasons": reasons,
        "evaluated_parameters": {
            "wave_height_m": wave_height,
            "wind_speed": wind_speed,
            "wind_gust": wind_gust,
            "weather_code": weather_code,
            "precipitation_mm": precipitation,
        },
        "decision_support_only": True,
        "warning": "Heuristic decision support; official marine warnings take precedence.",
    }
