"""
tools/tide_service.py
──────────────────────
Tide dynamics service for SAMUDRA.AI.

Retrieves Open-Meteo Marine hourly sea-level timeseries and computes:
  - Local High and Low tide extrema (peak/trough detection)
  - Current sea level, trend (RISING/FALLING), and phase (FLOODING/EBBING)
  - Tidal range and next high/low tide predictions
  - Data classification metadata (MODELLED) and model disclaimers

IMPORTANT — data classification:
  sea_level_height_msl is a MODELLED ocean sea-level value referenced to global MSL.
  It is NOT authoritative tide-gauge data and must NOT be claimed as chart datum.
"""

from __future__ import annotations

from typing import Any, Optional
import httpx

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"


def extract_tide_extrema(hourly_timeseries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Detect local HIGH and LOW extrema from an hourly sea-level timeseries.

    Each element of hourly_timeseries should contain:
      {"time_iso": str, "height_m": float | None}

    Returns chronologically ordered extrema:
      [{"type": "HIGH" | "LOW", "time_iso": str, "height_m": float}, ...]
    """
    if not hourly_timeseries or len(hourly_timeseries) < 3:
        return []

    valid_points = []
    for item in hourly_timeseries:
        if not isinstance(item, dict):
            continue
        t = item.get("time_iso") or item.get("time")
        h = item.get("height_m")
        if h is None:
            h = item.get("sea_level_height_msl")
        if t is not None and h is not None:
            try:
                valid_points.append({"time_iso": str(t), "height_m": float(h)})
            except (ValueError, TypeError):
                continue

    if len(valid_points) < 3:
        return []

    extrema = []
    n = len(valid_points)

    for i in range(1, n - 1):
        prev_h = valid_points[i - 1]["height_m"]
        curr_h = valid_points[i]["height_m"]
        next_h = valid_points[i + 1]["height_m"]

        if (curr_h > prev_h and curr_h >= next_h) or (curr_h >= prev_h and curr_h > next_h):
            extrema.append({
                "type": "HIGH",
                "time_iso": valid_points[i]["time_iso"],
                "height_m": round(curr_h, 3),
            })
        elif (curr_h < prev_h and curr_h <= next_h) or (curr_h <= prev_h and curr_h < next_h):
            extrema.append({
                "type": "LOW",
                "time_iso": valid_points[i]["time_iso"],
                "height_m": round(curr_h, 3),
            })

    deduped = []
    for e in extrema:
        if not deduped:
            deduped.append(e)
        elif deduped[-1]["type"] != e["type"]:
            deduped.append(e)
        else:
            if e["type"] == "HIGH" and e["height_m"] > deduped[-1]["height_m"]:
                deduped[-1] = e
            elif e["type"] == "LOW" and e["height_m"] < deduped[-1]["height_m"]:
                deduped[-1] = e

    return deduped


def get_tide_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Fetch hourly sea-level timeseries from Open-Meteo Marine and compute
    tidal extrema, phase, trend, and range.
    """
    lat = float(latitude)
    lon = float(longitude)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["sea_level_height_msl"],
        "forecast_days": 2,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(MARINE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        hourly_raw = data.get("hourly", {})
        times = hourly_raw.get("time", [])
        heights = hourly_raw.get("sea_level_height_msl", [])

        timeseries = []
        for t, h in zip(times, heights):
            if h is not None:
                timeseries.append({"time_iso": str(t), "height_m": float(h)})

        extrema = extract_tide_extrema(timeseries)

        curr_height = timeseries[0]["height_m"] if timeseries else 0.0
        trend = "STATIONARY"
        phase = "EBBING"
        if len(timeseries) >= 2:
            h0 = timeseries[0]["height_m"]
            h1 = timeseries[1]["height_m"]
            if h1 > h0:
                trend = "RISING"
                phase = "FLOODING"
            elif h1 < h0:
                trend = "FALLING"
                phase = "EBBING"

        next_high = next((e for e in extrema if e["type"] == "HIGH"), None)
        next_low = next((e for e in extrema if e["type"] == "LOW"), None)

        high_vals = [e["height_m"] for e in extrema if e["type"] == "HIGH"]
        low_vals = [e["height_m"] for e in extrema if e["type"] == "LOW"]
        tidal_range = round(max(high_vals) - min(low_vals), 3) if (high_vals and low_vals) else 0.0

        return {
            "status": "AVAILABLE",
            "location": {"latitude": lat, "longitude": lon},
            "current": {
                "sea_level_m": curr_height,
                "phase": phase,
                "trend": trend,
            },
            "extrema": extrema,
            "next_high_tide": next_high,
            "next_low_tide": next_low,
            "hourly_timeseries": timeseries[:24],
            "tidal_range_m": tidal_range,
            "datum": "MSL_MODELLED",
            "provenance": {
                "provider": "Open-Meteo",
                "source": "Open-Meteo Marine hourly sea level",
                "data_class": "MODELLED",
                "method": "numerical_extrema_detection",
            },
            "disclaimer": (
                "sea_level_height_msl is a MODELLED value combining global ocean models "
                "and surge estimates. It is referenced to global mean sea level (MSL), "
                "NOT lowest astronomical tide (LAT) or local chart datum. This is NOT "
                "authoritative tide-gauge data."
            ),
        }
    except Exception as exc:
        return {
            "status": "UNAVAILABLE",
            "location": {"latitude": lat, "longitude": lon},
            "error": str(exc),
            "current": {"sea_level_m": None, "phase": "UNKNOWN", "trend": "UNKNOWN"},
            "extrema": [],
            "next_high_tide": None,
            "next_low_tide": None,
            "hourly_timeseries": [],
            "tidal_range_m": 0.0,
            "datum": "MSL_MODELLED",
            "provenance": {
                "provider": "Open-Meteo",
                "source": "Open-Meteo Marine hourly sea level",
                "data_class": "UNAVAILABLE",
            },
            "disclaimer": "Tide data unavailable.",
        }
