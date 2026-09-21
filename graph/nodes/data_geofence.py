"""
graph/nodes/data_geofence.py
─────────────────────────────
Data Node — Geofence

Checks whether the location falls inside any restricted/protected zone.
Always runs (geofence check is cheap and safety-critical).
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.geofence import check_geofence
from tools.evidence_service import (
    create_evidence_record,
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    SourceType,
)


def geofence_data_node(state: SamudraState) -> SamudraState:
    """Check geofence / MPA / restricted zone for the location."""

    # If this is a recheck pass, only re-fetch if geofence was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "geofence" not in recheck_domains:
        return {"node_trace": ["geofence_data_collector(recheck_skipped)"]}

    location = state.get("location", {})

    ev_mpa = create_evidence_record(
        source_id="mpa_gis_boundaries",
        provider="Ministry of Environment, Forest and Climate Change (MoEFCC)",
        dataset="Marine Protected Areas (MPA) Vector Layer",
        source_type=SourceType.UNAVAILABLE,
        authority_class=AuthorityClass.RESEARCH_INSTITUTION,
        data_class=DataClass.UNAVAILABLE,
        status=EvidenceStatus.UNAVAILABLE,
        limitations=["Official MPA vector GIS polygon dataset is unmapped / not loaded in open environment"],
    )

    ev_naval = create_evidence_record(
        source_id="naval_defence_gis_zones",
        provider="Indian Navy / Ministry of Defence",
        dataset="Military Firing Ranges & Naval Defense Restriction Zones",
        source_type=SourceType.UNAVAILABLE,
        authority_class=AuthorityClass.OFFICIAL_GOVERNMENT_REQUIRED,
        data_class=DataClass.UNAVAILABLE,
        status=EvidenceStatus.UNAVAILABLE,
        limitations=["Defence restriction geometries are non-public classified data; check NHO NAVAREA VIII notices"],
    )

    if location.get("status") != "FOUND":
        ev_eez = create_evidence_record(
            source_id="eez_marine_regions",
            provider="Marine Regions / Flanders Marine Institute (VLIZ)",
            dataset="Indian EEZ Maritime Boundary Polygons v11",
            source_type=SourceType.EMBEDDED_GEOJSON,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.INFORMATIONAL_GIS,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        return {
            "geofence_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "evidence": [ev_eez, ev_mpa, ev_naval],
            "node_trace": ["geofence_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = check_geofence(lat, lon)

        is_ok = isinstance(result, dict) and result.get("status") in ("OK", "IN_EEZ", "OUTSIDE_EEZ", "CALCULATED")
        ev_eez = create_evidence_record(
            source_id="eez_marine_regions",
            provider="Marine Regions / VLIZ (Flanders Marine Institute)",
            dataset="World Maritime Boundaries Database (Indian EEZ v11)",
            source_type=SourceType.EMBEDDED_GEOJSON,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.INFORMATIONAL_GIS,
            status=EvidenceStatus.AVAILABLE if is_ok else EvidenceStatus.ERROR,
            retrieved_at=(result.get("provenance") or {}).get("timestamp") if isinstance(result, dict) else None,
            attribution="Flanders Marine Institute (VLIZ) Marine Regions (2023)",
            license_type="CC BY 4.0",
            limitations=["Informational academic maritime boundary layer; NOT authoritative for official navigation or legal enforcement"],
            query_metadata={"latitude": lat, "longitude": lon},
        )

        return {
            "geofence_data": result,
            "evidence": [ev_eez, ev_mpa, ev_naval],
            "node_trace": ["geofence_data_collector"],
        }

    except Exception as exc:
        ev_eez = create_evidence_record(
            source_id="eez_marine_regions",
            provider="Marine Regions / VLIZ",
            dataset="Indian EEZ Maritime Boundary Polygons",
            source_type=SourceType.EMBEDDED_GEOJSON,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.INFORMATIONAL_GIS,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        return {
            "geofence_data": {"status": "ERROR", "error": str(exc)},
            "evidence": [ev_eez, ev_mpa, ev_naval],
            "errors": [f"geofence_data_node: {exc}"],
            "node_trace": ["geofence_data_collector"],
        }
