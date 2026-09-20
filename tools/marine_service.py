"""
tools/marine_service.py
────────────────────────
Open-Meteo Marine API client for SAMUDRA.AI.

Endpoint: https://marine-api.open-meteo.com/v1/marine

Returns wave conditions, swell, wind waves, ocean currents,
sea surface temperature, and modelled sea-level height.

IMPORTANT — data classification:
  All values from this service are MODELLED, not observed.
  sea_level_height_msl is a modelled tidal/sea-level value.
  It is NOT authoritative nautical tide-gauge data and must
  NOT be used for coastal navigation decisions.

Variable names are taken verbatim from the Open-Meteo Marine
API documentation. No names are invented.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

# ── Confirmed current variables (Open-Meteo Marine API docs) ─────────────────
# Every name here is verified against the official variable list.
_CURRENT_VARS: list[str] = [
    "wave_height",
    "wave_direction",
    "wave_period",
    "wave_peak_period",
    "wind_wave_height",
    "wind_wave_direction",
    "wind_wave_period",
    "wind_wave_peak_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "swell_wave_peak_period",
    "ocean_current_velocity",
    "ocean_current_direction",
    "sea_surface_temperature",
    "sea_level_height_msl",
]

# ── Confirmed hourly variables (same set — every current var is hourly too) ───
_HOURLY_VARS: list[str] = _CURRENT_VARS


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_current(raw_current: dict, units: dict) -> dict[str, Any]:
    """
    Extract current values safely. Missing keys return None — never fabricated.
    """
    return {
        # Primary wave
        "wave_height":              raw_current.get("wave_height"),
        "wave_direction":           raw_current.get("wave_direction"),
        "wave_period":              raw_current.get("wave_period"),
        "wave_peak_period":         raw_current.get("wave_peak_period"),
        # Wind wave
        "wind_wave_height":         raw_current.get("wind_wave_height"),
        "wind_wave_direction":      raw_current.get("wind_wave_direction"),
        "wind_wave_period":         raw_current.get("wind_wave_period"),
        "wind_wave_peak_period":    raw_current.get("wind_wave_peak_period"),
        # Swell
        "swell_wave_height":        raw_current.get("swell_wave_height"),
        "swell_wave_direction":     raw_current.get("swell_wave_direction"),
        "swell_wave_period":        raw_current.get("swell_wave_period"),
        "swell_wave_peak_period":   raw_current.get("swell_wave_peak_period"),
        # Currents
        "ocean_current_velocity":   raw_current.get("ocean_current_velocity"),
        "ocean_current_direction":  raw_current.get("ocean_current_direction"),
        # SST & sea level
        "sea_surface_temperature":  raw_current.get("sea_surface_temperature"),
        "sea_level_height_msl":     raw_current.get("sea_level_height_msl"),
    }


def get_marine_conditions(
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
) -> dict[str, Any]:
    """
    Fetch marine conditions from Open-Meteo Marine API.

    Parameters
    ----------
    latitude, longitude : float
        WGS84 coordinates.
    forecast_days : int
        1–8. Default 7. Clamped to [1, 8].

    Returns
    -------
    dict with keys:
        status          "OK" | "PARTIAL" | "NO_DATA" | "ERROR"
        source          "Open-Meteo Marine"
        data_type       "MODELLED"  ← always; never claim OBSERVED
        latitude        float
        longitude       float
        current         dict of current values (None if unavailable)
        current_units   dict of unit strings from the API
        hourly          dict of hourly arrays + "time" list
        hourly_units    dict of unit strings from the API
        forecast_days   int
        warnings        list[str]  — populated when variables are missing
        retrieved_at    ISO-8601 UTC timestamp
        sea_level_note  str — disclaimer about sea_level_height_msl
    """

    forecast_days = max(1, min(int(forecast_days), 8))

    params: dict[str, Any] = {
        "latitude":     latitude,
        "longitude":    longitude,
        "current":      ",".join(_CURRENT_VARS),
        "hourly":       ",".join(_HOURLY_VARS),
        "forecast_days": forecast_days,
        "timezone":     "UTC",
        # Prefer sea grid-cell selection (coastal queries)
        "cell_selection": "sea",
    }

    warnings: list[str] = []
    retrieved_at = _utc_now_iso()

    try:
        response = httpx.get(MARINE_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        return {
            "status":       "ERROR",
            "source":       "Open-Meteo Marine",
            "data_type":    "MODELLED",
            "latitude":     latitude,
            "longitude":    longitude,
            "error":        f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            "warnings":     warnings,
            "retrieved_at": retrieved_at,
        }
    except Exception as exc:
        return {
            "status":       "ERROR",
            "source":       "Open-Meteo Marine",
            "data_type":    "MODELLED",
            "latitude":     latitude,
            "longitude":    longitude,
            "error":        str(exc),
            "warnings":     warnings,
            "retrieved_at": retrieved_at,
        }

    # ── Extract current ───────────────────────────────────────────────────────
    raw_current  = data.get("current", {})
    current_units = data.get("current_units", {})
    current = _safe_current(raw_current, current_units)

    # ── Check for missing variables and record warnings ───────────────────────
    for var in _CURRENT_VARS:
        if var not in raw_current:
            warnings.append(
                f"Variable '{var}' not present in API current response."
            )

    # ── Extract hourly ────────────────────────────────────────────────────────
    hourly       = data.get("hourly", {})
    hourly_units = data.get("hourly_units", {})

    for var in _HOURLY_VARS:
        if var not in hourly:
            warnings.append(
                f"Variable '{var}' not present in API hourly response."
            )

    # ── Determine status ──────────────────────────────────────────────────────
    non_null_current = sum(
        1 for v in current.values() if v is not None
    )

    if non_null_current == len(_CURRENT_VARS):
        status = "OK"
    elif non_null_current > 0:
        status = "PARTIAL"
    else:
        status = "NO_DATA"

    return {
        "status":       status,
        "source":       "Open-Meteo Marine",
        "data_type":    "MODELLED",
        "latitude":     data.get("latitude", latitude),
        "longitude":    data.get("longitude", longitude),
        "current":      current,
        "current_units": current_units,
        "hourly":       hourly,
        "hourly_units": hourly_units,
        "forecast_days": forecast_days,
        "warnings":     warnings,
        "retrieved_at": retrieved_at,
        # Explicit disclaimer — required per specification
        "sea_level_note": (
            "sea_level_height_msl is a MODELLED value combining tidal models, "
            "inverted barometer effect, and sea surface height anomalies. "
            "It is referenced to global mean sea level, NOT lowest astronomical tide. "
            "This is NOT authoritative tide-gauge data and must NOT be used for "
            "coastal navigation or nautical almanac purposes."
        ),
    }
