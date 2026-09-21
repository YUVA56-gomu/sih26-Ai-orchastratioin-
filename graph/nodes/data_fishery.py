"""
graph/nodes/data_fishery.py
────────────────────────────
Data Node — Fishery (PFZ heuristic / INCOIS)

Fetches PFZ candidates using the SST-heuristic service.
Skipped if "fishery" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.pfz_service import find_nearest_pfz
from tools.evidence_service import (
    create_evidence_record,
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    SourceType,
)


def fishery_data_node(state: SamudraState) -> SamudraState:
    """Collect PFZ heuristic data."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if fishery was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "fishery" not in recheck_domains:
        return {"node_trace": ["fishery_data_collector(recheck_skipped)"]}

    if "fishery" not in domains:
        ev = create_evidence_record(
            source_id="pfz_incois_heuristic",
            provider="INCOIS / SAMUDRA.AI Thermal Engine",
            dataset="Potential Fishing Zone (PFZ) Advisories & SST/Chlorophyll Gradients",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.SKIPPED,
            limitations=["Not requested for current query plan"],
        )
        return {
            "fishery_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "evidence": [ev],
            "node_trace": ["fishery_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        ev = create_evidence_record(
            source_id="pfz_incois_heuristic",
            provider="INCOIS / SAMUDRA.AI Thermal Engine",
            dataset="Potential Fishing Zone (PFZ) Advisories & SST/Chlorophyll Gradients",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        return {
            "fishery_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "evidence": [ev],
            "node_trace": ["fishery_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        result = find_nearest_pfz(lat, lon)

        is_ok = isinstance(result, dict) and result.get("status") in ("OK", "Calculated", "HEURISTIC")
        ev = create_evidence_record(
            source_id="pfz_incois_heuristic",
            provider="INCOIS (Govt. of India) / Thermal Gradient Model",
            dataset="Potential Fishing Zone (PFZ) Advisory Engine",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.AVAILABLE if is_ok else EvidenceStatus.PARTIAL,
            retrieved_at=result.get("retrieved_at") if isinstance(result, dict) else None,
            observation_time=result.get("valid_from") if isinstance(result, dict) else None,
            valid_until=result.get("valid_until") if isinstance(result, dict) else None,
            attribution="INCOIS Ministry of Earth Sciences / SAMUDRA.AI Engine",
            license_type="Open Government Data (OGD) India",
            limitations=["PFZ advisories indicate oceanographic aggregation likelihood, not guaranteed catch volume"],
            query_metadata={"latitude": lat, "longitude": lon},
        )

        return {
            "fishery_data": result,
            "evidence": [ev],
            "node_trace": ["fishery_data_collector"],
        }

    except Exception as exc:
        ev = create_evidence_record(
            source_id="pfz_incois_heuristic",
            provider="INCOIS / SAMUDRA.AI Thermal Engine",
            dataset="Potential Fishing Zone (PFZ) Advisory Engine",
            source_type=SourceType.API,
            authority_class=AuthorityClass.OFFICIAL_BULLETIN,
            data_class=DataClass.MODELLED,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        return {
            "fishery_data": {"status": "ERROR", "error": str(exc)},
            "evidence": [ev],
            "errors": [f"fishery_data_node: {exc}"],
            "node_trace": ["fishery_data_collector"],
        }
