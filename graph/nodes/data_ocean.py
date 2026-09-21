"""
graph/nodes/data_ocean.py
──────────────────────────
Data Node — Ocean (Copernicus Marine)

Fetches SST, waves, and currents from Copernicus Marine Service.
Skipped if "ocean" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.copernicus_service import get_copernicus_marine_snapshot
from tools.evidence_service import (
    create_evidence_record,
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    SourceType,
)


def ocean_data_node(state: SamudraState) -> SamudraState:
    """Collect ocean observations from Copernicus Marine."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if ocean was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "ocean" not in recheck_domains:
        return {"node_trace": ["ocean_data_collector(recheck_skipped)"]}

    if "ocean" not in domains:
        ev = create_evidence_record(
            source_id="ocean_copernicus_marine",
            provider="Copernicus Marine Service",
            dataset="Global Ocean Physics Reanalysis & Forecast",
            source_type=SourceType.API,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.SKIPPED,
            limitations=["Not requested for current query plan"],
        )
        return {
            "ocean_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "evidence": [ev],
            "node_trace": ["ocean_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        ev = create_evidence_record(
            source_id="ocean_copernicus_marine",
            provider="Copernicus Marine Service",
            dataset="Global Ocean Physics Reanalysis & Forecast",
            source_type=SourceType.API,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        return {
            "ocean_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "evidence": [ev],
            "node_trace": ["ocean_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = get_copernicus_marine_snapshot(lat, lon)

        is_ok = isinstance(result, dict) and result.get("status") in ("OK", "AVAILABLE", "SUCCESS")
        ev = create_evidence_record(
            source_id="ocean_copernicus_marine",
            provider="Copernicus Marine Service (E.U. Copernicus Programme)",
            dataset="Global Ocean Physics Analysis and Forecast",
            source_type=SourceType.API,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.AVAILABLE if is_ok else EvidenceStatus.PARTIAL,
            retrieved_at=result.get("retrieved_at") if isinstance(result, dict) else None,
            observation_time=result.get("observation_time") if isinstance(result, dict) else None,
            attribution="Copernicus Marine Service (E.U. Copernicus)",
            license_type="E.U. Open Data License",
            limitations=["Gridded oceanographic model output; localized sub-grid turbulence may vary"],
            query_metadata={"latitude": lat, "longitude": lon},
        )

        return {
            "ocean_data": result,
            "evidence": [ev],
            "node_trace": ["ocean_data_collector"],
        }

    except Exception as exc:
        ev = create_evidence_record(
            source_id="ocean_copernicus_marine",
            provider="Copernicus Marine Service",
            dataset="Global Ocean Physics Reanalysis & Forecast",
            source_type=SourceType.API,
            authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        return {
            "ocean_data": {"status": "ERROR", "error": str(exc)},
            "evidence": [ev],
            "errors": [f"ocean_data_node: {exc}"],
            "node_trace": ["ocean_data_collector"],
        }
