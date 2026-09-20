"""
tools/hazard_service.py
────────────────────────
Hazard Alert Feed Service & Bulletin Parser for SAMUDRA.AI.

Standardized data structures and parser for official marine warnings and advisories
(IMD, INCOIS, MOSDAC).

Supported Categories:
  - CYCLONE
  - HIGH_WAVE
  - SWELL_SURGE
  - TSUNAMI
  - GALE_WIND
  - COASTAL_FLOOD

Supported Severities:
  - ADVISORY
  - WATCH
  - WARNING
  - SEVERE_WARNING

IMPORTANT — Safety Rules:
  1. Never fabricate official IMD/INCOIS alerts.
  2. If no live feed is configured/available, return status: "UNAVAILABLE".
  3. Set data_class = "OFFICIAL_BULLETIN" ONLY for genuinely parsed official payloads.
"""

from __future__ import annotations

from typing import Any, Optional

ALLOWED_CATEGORIES = {
    "CYCLONE",
    "HIGH_WAVE",
    "SWELL_SURGE",
    "TSUNAMI",
    "GALE_WIND",
    "COASTAL_FLOOD",
}

ALLOWED_SEVERITIES = {
    "ADVISORY",
    "WATCH",
    "WARNING",
    "SEVERE_WARNING",
}


def get_default_hazard_status() -> dict[str, Any]:
    """Return safe default response when no live official hazard feed is active/configured."""
    return {
        "status": "UNAVAILABLE",
        "alerts": [],
        "advice": "No active official IMD/INCOIS live hazard feed connected.",
        "provenance": {
            "provider": "INCOIS / IMD",
            "source": "Official Marine Hazard Feed",
            "data_class": "UNAVAILABLE",
            "status": "UNAVAILABLE",
        },
    }


def parse_hazard_bulletin(payload: Optional[dict[str, Any]]) -> dict[str, Any]:
    """
    Parse and validate a structured official hazard bulletin payload.

    If payload is empty, invalid, or status is unavailable, returns default UNAVAILABLE state.
    If valid, returns status: "ACTIVE" with data_class: "OFFICIAL_BULLETIN".
    """
    if not isinstance(payload, dict):
        return get_default_hazard_status()

    raw_status = payload.get("status", "").upper()
    if raw_status in ("UNAVAILABLE", "INACTIVE", "OFFLINE"):
        return get_default_hazard_status()

    raw_alerts = payload.get("alerts", [])
    if not isinstance(raw_alerts, list):
        return get_default_hazard_status()

    parsed_alerts = []
    for idx, alert in enumerate(raw_alerts):
        if not isinstance(alert, dict):
            continue

        cat = str(alert.get("category", "HIGH_WAVE")).upper()
        if cat not in ALLOWED_CATEGORIES:
            cat = "HIGH_WAVE"

        sev = str(alert.get("severity", "ADVISORY")).upper()
        if sev not in ALLOWED_SEVERITIES:
            sev = "ADVISORY"

        parsed_alerts.append({
            "alert_id": alert.get("alert_id", f"HAZARD_{idx + 1}"),
            "source": alert.get("source", payload.get("source", "INCOIS")),
            "category": cat,
            "severity": sev,
            "title": alert.get("title", "Official Marine Hazard Warning"),
            "description": alert.get("description", ""),
            "issued_at": alert.get("issued_at"),
            "valid_from": alert.get("valid_from"),
            "valid_until": alert.get("valid_until"),
            "affected_regions": alert.get("affected_regions", []),
            "status": alert.get("status", "ACTIVE"),
            "provenance": {
                "provider": alert.get("source", payload.get("source", "INCOIS")),
                "data_class": "OFFICIAL_BULLETIN",
            },
        })

    if not parsed_alerts:
        return get_default_hazard_status()

    return {
        "status": "ACTIVE",
        "source": payload.get("source", "INCOIS"),
        "bulletin_id": payload.get("bulletin_id", "HAZARD_BULLETIN_LATEST"),
        "alerts": parsed_alerts,
        "advice": payload.get("advice", "Follow official IMD/INCOIS advisories."),
        "provenance": {
            "provider": payload.get("source", "INCOIS"),
            "source": "Official Marine Hazard Bulletin",
            "data_class": "OFFICIAL_BULLETIN",
        },
    }


def get_hazard_alerts(
    latitude: float,
    longitude: float,
    official_bulletin: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Retrieve or parse hazard alerts for target location.

    If an official_bulletin is passed, parses it.
    Otherwise, safely returns UNAVAILABLE status without fabricating alerts.
    """
    if official_bulletin:
        return parse_hazard_bulletin(official_bulletin)

    res = get_default_hazard_status()
    res["location"] = {"latitude": float(latitude), "longitude": float(longitude)}
    return res
