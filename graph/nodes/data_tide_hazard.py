"""
graph/nodes/data_tide_hazard.py
───────────────────────────────
Data Node — Tide Dynamics & Official Hazard Alert Feeds (Phase 2.4)

Fetches:
  1. Open-Meteo Marine hourly sea-level timeseries & computes extrema/phase (tide_service)
  2. Official hazard advisories & bulletins (hazard_service)
"""

from __future__ import annotations

from typing import Any
from state.schema import SamudraState
from tools.tide_service import get_tide_forecast
from tools.hazard_service import get_hazard_alerts
from tools.evidence_service import (
    create_evidence_record,
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    SourceType,
)


def tide_hazard_data_node(state: SamudraState) -> SamudraState:
    """Collect tide forecast and hazard alert data."""
    location = state.get("location", {})

    if location.get("status") != "FOUND":
        ev_tide = create_evidence_record(
            source_id="tide_open_meteo_marine",
            provider="Open-Meteo Marine / Harmonic Tide Model",
            dataset="Hourly Tidal Water Level Extrema & Phase Engine",
            source_type=SourceType.HARMONIC_MODEL,
            authority_class=AuthorityClass.MODELLED,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        ev_hazard = create_evidence_record(
            source_id="hazard_incois_bulletins",
            provider="INCOIS Coastal Hazard Warning Centre",
            dataset="Coastal High Wave, Swell Surge & Tsunami Advisories",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.OFFICIAL_BULLETIN,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        return {
            "tide_data": {"status": "BLOCKED", "reason": f"Location unavailable: {location.get('status')}"},
            "hazard_data": {"status": "UNAVAILABLE", "alerts": [], "reason": f"Location unavailable: {location.get('status')}"},
            "evidence": [ev_tide, ev_hazard],
            "node_trace": ["tide_hazard_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        tide_res = get_tide_forecast(lat, lon)
        hazard_res = get_hazard_alerts(lat, lon)

        tide_ok = isinstance(tide_res, dict) and tide_res.get("status") in ("OK", "AVAILABLE")
        ev_tide = create_evidence_record(
            source_id="tide_open_meteo_marine",
            provider="Open-Meteo Marine / Harmonic Tide Model",
            dataset="Hourly Tidal Water Level Extrema & Phase Engine",
            source_type=SourceType.HARMONIC_MODEL,
            authority_class=AuthorityClass.MODELLED,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.AVAILABLE if tide_ok else EvidenceStatus.ERROR,
            retrieved_at=(tide_res.get("provenance") or {}).get("retrieved_at") if isinstance(tide_res, dict) else None,
            attribution="Open-Meteo Marine / Global Harmonic Tide Solution",
            license_type="CC BY 4.0",
            limitations=["Harmonic astronomical model prediction; local estuarine silting may shift high/low tide timing"],
            query_metadata={"latitude": lat, "longitude": lon},
        )

        hazard_ok = isinstance(hazard_res, dict) and hazard_res.get("status") in ("ACTIVE", "CLEAR", "OK", "AVAILABLE")
        ev_hazard = create_evidence_record(
            source_id="hazard_incois_bulletins",
            provider="INCOIS Coastal Hazard Warning Centre",
            dataset="Coastal High Wave, Swell Surge & Tsunami Advisories",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.OFFICIAL_BULLETIN,
            status=EvidenceStatus.AVAILABLE if hazard_ok else EvidenceStatus.UNAVAILABLE,
            retrieved_at=(hazard_res.get("provenance") or {}).get("retrieved_at") if isinstance(hazard_res, dict) else None,
            observation_time=(hazard_res.get("provenance") or {}).get("bulletin_date") if isinstance(hazard_res, dict) else None,
            attribution="INCOIS Ministry of Earth Sciences, Govt. of India",
            license_type="Open Government Data (OGD) India",
            limitations=["Official government bulletins apply to coastal regions and NAVAREA VIII zones"],
            query_metadata={"latitude": lat, "longitude": lon},
        )

        return {
            "tide_data": tide_res,
            "hazard_data": hazard_res,
            "evidence": [ev_tide, ev_hazard],
            "node_trace": ["tide_hazard_data_collector"],
        }
    except Exception as exc:
        ev_tide = create_evidence_record(
            source_id="tide_open_meteo_marine",
            provider="Open-Meteo Marine",
            dataset="Harmonic Tide Engine",
            source_type=SourceType.HARMONIC_MODEL,
            authority_class=AuthorityClass.MODELLED,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        ev_hazard = create_evidence_record(
            source_id="hazard_incois_bulletins",
            provider="INCOIS Coastal Hazard Centre",
            dataset="Coastal Hazard Bulletins",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.OFFICIAL_BULLETIN,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        return {
            "tide_data": {"status": "ERROR", "error": str(exc)},
            "hazard_data": {"status": "UNAVAILABLE", "alerts": [], "error": str(exc)},
            "evidence": [ev_tide, ev_hazard],
            "errors": [f"tide_hazard_data_collector: {exc}"],
            "node_trace": ["tide_hazard_data_collector"],
        }
