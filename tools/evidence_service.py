"""
tools/evidence_service.py
─────────────────────────
SAMUDRA AI — Deterministic Evidence & Data Provenance Engine

Provides standardized evidence records, provenance metadata tracking,
freshness calculations, source authority classification, and completeness
aggregation across all marine data services.

Anti-hallucination rule:
All evidence metadata MUST be generated deterministically by application code.
LLMs are strictly prohibited from inventing provider names, dataset IDs,
timestamps, or escalating authority classifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enumerations ──────────────────────────────────────────────────────────────

class AuthorityClass(str, Enum):
    OFFICIAL_GOVERNMENT          = "OFFICIAL_GOVERNMENT"
    OFFICIAL_GOVERNMENT_REQUIRED = "OFFICIAL_GOVERNMENT_REQUIRED"
    RESEARCH_INSTITUTION         = "RESEARCH_INSTITUTION"
    MODELLED                     = "MODELLED"
    FORECAST                     = "FORECAST"
    OFFICIAL_BULLETIN            = "OFFICIAL_BULLETIN"
    INFORMATIONAL_GIS            = "INFORMATIONAL_GIS"
    UNAVAILABLE                  = "UNAVAILABLE"


class DataClass(str, Enum):
    FORECAST          = "FORECAST"
    MODELLED          = "MODELLED"
    OBSERVATION       = "OBSERVATION"
    INFORMATIONAL_GIS = "INFORMATIONAL_GIS"
    OFFICIAL_BULLETIN = "OFFICIAL_BULLETIN"
    UNAVAILABLE       = "UNAVAILABLE"


class EvidenceStatus(str, Enum):
    AVAILABLE   = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE       = "STALE"
    ERROR       = "ERROR"
    PARTIAL     = "PARTIAL"
    SKIPPED     = "SKIPPED"


class FreshnessStatus(str, Enum):
    FRESH       = "FRESH"
    RECENT      = "RECENT"
    STALE       = "STALE"
    UNKNOWN     = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


class SourceType(str, Enum):
    API              = "API"
    EMBEDDED_GEOJSON = "EMBEDDED_GEOJSON"
    HARMONIC_MODEL   = "HARMONIC_MODEL"
    DYNAMIC_GRAPH    = "DYNAMIC_GRAPH"
    UNAVAILABLE      = "UNAVAILABLE"


# ── Core Helpers ──────────────────────────────────────────────────────────────

def utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def calculate_freshness(
    retrieved_at: Optional[str] = None,
    data_timestamp: Optional[str] = None,
    fresh_threshold_mins: int = 60,
    stale_threshold_mins: int = 360,
) -> Dict[str, Any]:
    """
    Calculate deterministic data age and freshness status.

    Thresholds:
    - age < 60 mins -> FRESH
    - 60 mins <= age <= 360 mins (6h) -> RECENT
    - age > 360 mins -> STALE
    - missing timestamp -> UNKNOWN
    """
    ref_time_str = data_timestamp or retrieved_at
    if not ref_time_str:
        return {
            "age_minutes": None,
            "freshness_status": FreshnessStatus.UNKNOWN.value,
            "ref_timestamp": None,
        }

    try:
        # Parse ISO string
        if ref_time_str.endswith("Z"):
            ref_time_str = ref_time_str[:-1] + "+00:00"
        ref_dt = datetime.fromisoformat(ref_time_str)
        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=timezone.utc)

        now_dt = datetime.now(timezone.utc)
        age_seconds = (now_dt - ref_dt).total_seconds()
        age_minutes = max(0.0, round(age_seconds / 60.0, 1))

        if age_minutes < fresh_threshold_mins:
            status = FreshnessStatus.FRESH.value
        elif age_minutes <= stale_threshold_mins:
            status = FreshnessStatus.RECENT.value
        else:
            status = FreshnessStatus.STALE.value

        return {
            "age_minutes": age_minutes,
            "freshness_status": status,
            "ref_timestamp": ref_dt.isoformat(),
        }

    except Exception:
        return {
            "age_minutes": None,
            "freshness_status": FreshnessStatus.UNKNOWN.value,
            "ref_timestamp": ref_time_str,
        }


def create_evidence_record(
    *,
    source_id: str,
    provider: str,
    dataset: str,
    source_type: SourceType | str,
    authority_class: AuthorityClass | str,
    data_class: DataClass | str,
    status: EvidenceStatus | str,
    retrieved_at: Optional[str] = None,
    observation_time: Optional[str] = None,
    forecast_time: Optional[str] = None,
    valid_until: Optional[str] = None,
    attribution: Optional[str] = None,
    license_type: Optional[str] = None,
    limitations: Optional[List[str]] = None,
    query_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized evidence record with deterministic metadata and freshness.
    """
    retrieved_iso = retrieved_at or utc_now_iso()

    # Calculate freshness if available
    status_str = status.value if isinstance(status, Enum) else str(status)
    if status_str == EvidenceStatus.UNAVAILABLE.value:
        freshness = {
            "age_minutes": None,
            "freshness_status": FreshnessStatus.UNAVAILABLE.value,
            "ref_timestamp": None,
        }
    else:
        freshness = calculate_freshness(
            retrieved_at=retrieved_iso,
            data_timestamp=observation_time or forecast_time,
        )

    auth_str = authority_class.value if isinstance(authority_class, Enum) else str(authority_class)
    data_str = data_class.value if isinstance(data_class, Enum) else str(data_class)
    src_type_str = source_type.value if isinstance(source_type, Enum) else str(source_type)

    return {
        "source_id": source_id,
        "provider": provider,
        "dataset": dataset,
        "source_type": src_type_str,
        "authority_class": auth_str,
        "data_class": data_str,
        "status": status_str,
        "retrieved_at": retrieved_iso,
        "observation_time": observation_time,
        "forecast_time": forecast_time,
        "valid_until": valid_until,
        "freshness": freshness,
        "attribution": attribution or provider,
        "license_type": license_type or "Public Domain / Open Data",
        "limitations": limitations or [],
        "query_metadata": query_metadata or {},
    }


def aggregate_evidence(evidence_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate a list of evidence records into a summary report.

    Computes data completeness score, available/unavailable source breakdown,
    stale dataset list, and active unavailable domains.
    """
    if not evidence_records or not isinstance(evidence_records, list):
        return {
            "total_sources": 0,
            "available_count": 0,
            "unavailable_count": 0,
            "stale_count": 0,
            "completeness_score": 0.0,
            "available_sources": [],
            "unavailable_sources": [],
            "stale_sources": [],
            "decision_support_only": True,
        }

    available_sources = []
    unavailable_sources = []
    stale_sources = []

    for record in evidence_records:
        if not isinstance(record, dict):
            continue
        sid = record.get("source_id", "unknown")
        status = record.get("status", EvidenceStatus.UNAVAILABLE.value)
        freshness_status = (record.get("freshness") or {}).get("freshness_status")

        if status == EvidenceStatus.AVAILABLE.value:
            available_sources.append(sid)
            if freshness_status == FreshnessStatus.STALE.value:
                stale_sources.append(sid)
        else:
            unavailable_sources.append(sid)

    total = len(evidence_records)
    avail = len(available_sources)
    unavail = len(unavailable_sources)
    stale = len(stale_sources)

    score = round((avail / max(1, total)) * 100.0, 1)

    return {
        "total_sources": total,
        "available_count": avail,
        "unavailable_count": unavail,
        "stale_count": stale,
        "completeness_score": score,
        "available_sources": available_sources,
        "unavailable_sources": unavailable_sources,
        "stale_sources": stale_sources,
        "decision_support_only": True,
    }
