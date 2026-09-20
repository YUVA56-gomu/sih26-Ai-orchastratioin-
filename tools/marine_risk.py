from __future__ import annotations


def _number(
    value,
):
    try:

        if value is None:
            return None

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None


def calculate_marine_risk(
    ocean: dict,
    weather: dict,
    geofence: dict,
    marine: dict | None = None,
) -> dict:

    score = 0

    reasons = []

    observations = (
        ocean.get(
            "observations",
            {},
        )
    )

    waves = (
        observations.get(
            "waves",
            {},
        )
    )

    current = (
        observations.get(
            "currents",
            {},
        )
    )

    weather_current = (
        weather.get(
            "current",
            {},
        )
    )

    wave_height = _number(
        waves.get(
            "significant_wave_height_m"
        )
    )

    # ── Fallback: use Open-Meteo Marine wave_height if Copernicus unavailable ─
    if wave_height is None and marine:
        marine_current = marine.get("current", {})
        wave_height = _number(
            marine_current.get("wave_height")
        )

    wind_speed = _number(
        weather_current.get(
            "wind_speed_10m"
        )
    )

    wind_gusts = _number(
        weather_current.get(
            "wind_gusts_10m"
        )
    )
    if wind_gusts is None:
        hourly_gusts = (weather.get("hourly") or {}).get("wind_gusts_10m", [])
        if isinstance(hourly_gusts, list) and hourly_gusts:
            valid_gusts = [float(g) for g in hourly_gusts if _number(g) is not None]
            if valid_gusts:
                wind_gusts = max(valid_gusts[:24])
        if wind_gusts is None:
            daily_gusts = (weather.get("daily") or {}).get("wind_gusts_10m_max", [])
            if isinstance(daily_gusts, list) and daily_gusts:
                valid_daily = [float(g) for g in daily_gusts if _number(g) is not None]
                if valid_daily:
                    wind_gusts = valid_daily[0]

    weather_code = _number(
        weather_current.get(
            "weather_code"
        )
    )

    precipitation = _number(
        weather_current.get(
            "precipitation"
        )
    )

    # ---------------------------------------------------------
    # WAVES
    # ---------------------------------------------------------

    if wave_height is not None:

        if wave_height >= 2.5:

            score += 40

            reasons.append(
                "Very high significant wave height."
            )

        elif wave_height >= 1.5:

            score += 25

            reasons.append(
                "Elevated significant wave height."
            )

        elif wave_height >= 1.0:

            score += 10

            reasons.append(
                "Moderate wave conditions."
            )

    # ---------------------------------------------------------
    # WIND & GUSTS
    # ---------------------------------------------------------

    if wind_speed is not None:

        if wind_speed >= 45:

            score += 35

            reasons.append(
                "Strong wind conditions."
            )

        elif wind_speed >= 30:

            score += 20

            reasons.append(
                "Elevated wind conditions."
            )

        elif wind_speed >= 20:

            score += 8

            reasons.append(
                "Moderate wind conditions."
            )

    if wind_gusts is not None:

        if wind_gusts >= 55:

            score += 25

            reasons.append(
                "Severe peak wind gusts detected."
            )

        elif wind_gusts >= 40:

            score += 15

            reasons.append(
                "Elevated wind gust potential."
            )

        elif wind_gusts >= 28:

            score += 8

            reasons.append(
                "Moderate wind gust activity."
            )

    # ---------------------------------------------------------
    # WEATHER
    # ---------------------------------------------------------

    if weather_code is not None:

        if weather_code >= 80:

            score += 20

            reasons.append(
                "Heavy-weather precipitation code detected."
            )

    if precipitation is not None:

        if precipitation >= 10:

            score += 10

            reasons.append(
                "Heavy precipitation signal."
            )

    # ---------------------------------------------------------
    # GEOFENCE
    # ---------------------------------------------------------

    if geofence.get(
        "inside_restricted_zone"
    ):

        score += 50

        reasons.append(
            "Location intersects a configured restricted zone."
        )

    score = min(
        score,
        100,
    )

    if score < 25:

        level = "LOW"

    elif score < 55:

        level = "MODERATE"

    elif score < 80:

        level = "HIGH"

    else:

        level = "VERY HIGH"

    return {

        "risk_level":
            level,

        "risk_score":
            score,

        "reasons":
            reasons,

        "evaluated_parameters": {

            "wave_height_m":
                wave_height,

            "wind_speed_kmh":
                wind_speed,

            "wind_gusts_kmh":
                wind_gusts,

            "weather_code":
                weather_code,

            "precipitation_mm":
                precipitation,

            # From Open-Meteo Marine (MODELLED) — informational only
            "ocean_current_velocity_kmh": _number(
                (marine or {}).get("current", {}).get("ocean_current_velocity")
            ),

            "marine_sst_c": _number(
                (marine or {}).get("current", {}).get("sea_surface_temperature")
            ),

        },

        "decision_support_only":
            True,

        "warning":
            (
                "This risk calculation is an ORCA "
                "decision-support heuristic and does "
                "not replace official marine warnings."
            ),
    }