"""
tools/incois_bulletin.py
────────────────────────
Standardized data structures and parser for official INCOIS / MOSDAC
Potential Fishing Zone (PFZ) Bulletins.

Handles official bulletin schema validation and graceful fallback
when live INCOIS bulletin feeds are unavailable.
"""

from __future__ import annotations

from typing import Any, Optional


def get_default_incois_status() -> dict[str, Any]:
    """Return default structured status when live INCOIS feed is unconfigured/unavailable."""
    return {
        "source": "INCOIS",
        "status": "UNAVAILABLE",
        "bulletin_id": None,
        "issued_at": None,
        "valid_until": None,
        "region": None,
        "bulletin_candidates": [],
        "advice": "No active official INCOIS live feed connected. Operating on Copernicus satellite analysis.",
        "provenance": {
            "provider": "INCOIS / ESSO",
            "data_class": "OFFICIAL_BULLETIN",
            "status": "UNAVAILABLE",
        },
    }


def parse_incois_bulletin(payload: Optional[dict[str, Any]]) -> dict[str, Any]:
    """
    Parse and validate a structured INCOIS bulletin payload.
    Distinguishes official bulletin data from model heuristics.
    """
    if not isinstance(payload, dict) or not payload:
        return get_default_incois_status()

    status = payload.get("status", "ACTIVE")
    if status != "ACTIVE":
        return get_default_incois_status()

    raw_candidates = payload.get("bulletin_candidates") or payload.get("candidates") or []
    validated_candidates = []

    for c in raw_candidates:
        if isinstance(c, dict):
            lat = c.get("latitude") or c.get("lat")
            lon = c.get("longitude") or c.get("lon")
            if lat is not None and lon is not None:
                validated_candidates.append({
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "bearing_deg": c.get("bearing_deg") or c.get("bearing"),
                    "distance_km": c.get("distance_km"),
                    "depth_m": c.get("depth_m") or c.get("depth"),
                    "advice": c.get("advice", "Official INCOIS candidate zone"),
                    "validation_status": c.get("validation_status", "VALIDATED"),
                })

    return {
        "source": "INCOIS",
        "status": "ACTIVE" if validated_candidates else "UNAVAILABLE",
        "bulletin_id": payload.get("bulletin_id", "INCOIS_PFZ_LATEST"),
        "issued_at": payload.get("issued_at"),
        "valid_until": payload.get("valid_until"),
        "region": payload.get("region", "Indian Ocean Coastal"),
        "bulletin_candidates": validated_candidates,
        "advice": payload.get("advice", "Follow official INCOIS marine safety guidelines."),
        "provenance": {
            "provider": "INCOIS / ESSO",
            "data_class": "OFFICIAL_BULLETIN",
            "status": "ACTIVE" if validated_candidates else "UNAVAILABLE",
        },
    }
