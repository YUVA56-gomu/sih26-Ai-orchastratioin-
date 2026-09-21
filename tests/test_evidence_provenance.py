"""
tests/test_evidence_provenance.py
───────────────────────────────────
Phase 2.7 Unit & Integration Test Suite — Evidence & Provenance Layer
"""

from datetime import datetime, timedelta, timezone
import pytest

from state.schema import SamudraState
from tools.evidence_service import (
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    FreshnessStatus,
    SourceType,
    aggregate_evidence,
    calculate_freshness,
    create_evidence_record,
    utc_now_iso,
)
from graph.nodes.data_weather import weather_data_node
from graph.nodes.data_ocean import ocean_data_node
from graph.nodes.data_fishery import fishery_data_node
from graph.nodes.data_tide_hazard import tide_hazard_data_node
from graph.nodes.data_geofence import geofence_data_node
from graph.nodes.data_route import fetch_route_data
from graph.nodes.risk import risk_assessment_node


def test_evidence_record_creation():
    """Verify create_evidence_record returns a valid standardized dictionary."""
    ev = create_evidence_record(
        source_id="test_source",
        provider="Test Provider",
        dataset="Test Dataset",
        source_type=SourceType.API,
        authority_class=AuthorityClass.FORECAST,
        data_class=DataClass.FORECAST,
        status=EvidenceStatus.AVAILABLE,
        attribution="Test Attribution",
        license_type="CC BY 4.0",
        limitations=["Testing constraint"],
    )

    assert ev["source_id"] == "test_source"
    assert ev["provider"] == "Test Provider"
    assert ev["dataset"] == "Test Dataset"
    assert ev["source_type"] == "API"
    assert ev["authority_class"] == "FORECAST"
    assert ev["data_class"] == "FORECAST"
    assert ev["status"] == "AVAILABLE"
    assert "retrieved_at" in ev
    assert "freshness" in ev
    assert ev["freshness"]["freshness_status"] in ("FRESH", "RECENT")


def test_freshness_calculation():
    """Verify deterministic age calculation and freshness classification."""
    now = datetime.now(timezone.utc)

    # 1. Fresh (< 60 mins)
    fresh_time = (now - timedelta(minutes=15)).isoformat()
    f_res = calculate_freshness(retrieved_at=fresh_time)
    assert f_res["freshness_status"] == FreshnessStatus.FRESH.value
    assert f_res["age_minutes"] is not None and f_res["age_minutes"] < 60

    # 2. Recent (60..360 mins)
    recent_time = (now - timedelta(hours=3)).isoformat()
    r_res = calculate_freshness(retrieved_at=recent_time)
    assert r_res["freshness_status"] == FreshnessStatus.RECENT.value

    # 3. Stale (> 360 mins)
    stale_time = (now - timedelta(hours=10)).isoformat()
    s_res = calculate_freshness(retrieved_at=stale_time)
    assert s_res["freshness_status"] == FreshnessStatus.STALE.value

    # 4. Unknown / missing
    u_res = calculate_freshness(retrieved_at=None)
    assert u_res["freshness_status"] == FreshnessStatus.UNKNOWN.value


def test_evidence_aggregation():
    """Verify aggregate_evidence computes source breakdown and completeness score."""
    records = [
        create_evidence_record(
            source_id="s1", provider="P1", dataset="D1",
            source_type=SourceType.API, authority_class=AuthorityClass.FORECAST,
            data_class=DataClass.FORECAST, status=EvidenceStatus.AVAILABLE,
        ),
        create_evidence_record(
            source_id="s2", provider="P2", dataset="D2",
            source_type=SourceType.UNAVAILABLE, authority_class=AuthorityClass.RESEARCH_INSTITUTION,
            data_class=DataClass.UNAVAILABLE, status=EvidenceStatus.UNAVAILABLE,
        ),
        create_evidence_record(
            source_id="s3", provider="P3", dataset="D3",
            source_type=SourceType.UNAVAILABLE, authority_class=AuthorityClass.OFFICIAL_GOVERNMENT_REQUIRED,
            data_class=DataClass.UNAVAILABLE, status=EvidenceStatus.UNAVAILABLE,
        ),
    ]

    summary = aggregate_evidence(records)
    assert summary["total_sources"] == 3
    assert summary["available_count"] == 1
    assert summary["unavailable_count"] == 2
    assert summary["completeness_score"] == 33.3
    assert "s1" in summary["available_sources"]
    assert "s2" in summary["unavailable_sources"]
    assert "s3" in summary["unavailable_sources"]


def test_geofence_evidence_unmapped_layers():
    """Verify geofence_data_node emits EEZ, MPA UNAVAILABLE, and Naval UNAVAILABLE records."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 18.92, "longitude": 72.83, "name": "Mumbai Offshore"},
        "plan": {"domains_needed": ["geospatial", "safety"]},
    }

    res = geofence_data_node(state)
    assert "evidence" in res
    ev_list = res["evidence"]
    assert len(ev_list) == 3

    sources = {e["source_id"]: e for e in ev_list}
    assert "eez_marine_regions" in sources
    assert "mpa_gis_boundaries" in sources
    assert "naval_defence_gis_zones" in sources

    # Check classifications
    assert sources["eez_marine_regions"]["authority_class"] == "RESEARCH_INSTITUTION"
    assert sources["eez_marine_regions"]["data_class"] == "INFORMATIONAL_GIS"

    assert sources["mpa_gis_boundaries"]["status"] == "UNAVAILABLE"
    assert sources["mpa_gis_boundaries"]["data_class"] == "UNAVAILABLE"

    assert sources["naval_defence_gis_zones"]["status"] == "UNAVAILABLE"
    assert sources["naval_defence_gis_zones"]["authority_class"] == "OFFICIAL_GOVERNMENT_REQUIRED"


def test_weather_data_node_evidence():
    """Verify weather_data_node emits weather_open_meteo evidence record."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27, "name": "Chennai"},
        "plan": {"domains_needed": ["weather"]},
    }

    res = weather_data_node(state)
    assert "evidence" in res
    ev = res["evidence"][0]
    assert ev["source_id"] == "weather_open_meteo"
    assert ev["provider"] == "Open-Meteo"
    assert ev["data_class"] == "FORECAST"


def test_ocean_data_node_evidence():
    """Verify ocean_data_node emits ocean_copernicus_marine evidence record."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 9.93, "longitude": 76.26, "name": "Kochi"},
        "plan": {"domains_needed": ["ocean"]},
    }

    res = ocean_data_node(state)
    assert "evidence" in res
    ev = res["evidence"][0]
    assert ev["source_id"] == "ocean_copernicus_marine"
    assert ev["authority_class"] == "RESEARCH_INSTITUTION"
    assert ev["data_class"] == "MODELLED"


def test_fishery_data_node_evidence():
    """Verify fishery_data_node emits pfz_incois_heuristic evidence record."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 17.68, "longitude": 83.21, "name": "Visakhapatnam"},
        "plan": {"domains_needed": ["fishery"]},
    }

    res = fishery_data_node(state)
    assert "evidence" in res
    ev = res["evidence"][0]
    assert ev["source_id"] == "pfz_incois_heuristic"
    assert ev["authority_class"] == "OFFICIAL_BULLETIN"


def test_tide_hazard_data_node_evidence():
    """Verify tide_hazard_data_node emits tide and hazard evidence records."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 15.49, "longitude": 73.82, "name": "Goa"},
    }

    res = tide_hazard_data_node(state)
    assert "evidence" in res
    ev_list = res["evidence"]
    assert len(ev_list) == 2

    s_ids = [e["source_id"] for e in ev_list]
    assert "tide_open_meteo_marine" in s_ids
    assert "hazard_incois_bulletins" in s_ids


def test_route_data_node_evidence():
    """Verify fetch_route_data emits route_astar_engine evidence record."""
    state: SamudraState = {
        "location": {"status": "FOUND", "latitude": 18.92, "longitude": 72.83, "name": "Mumbai"},
        "user_query": "Find route from Mumbai to Goa",
    }

    res = fetch_route_data(state)
    assert "evidence" in res
    ev = res["evidence"][0]
    assert ev["source_id"] == "route_astar_engine"
    assert ev["data_class"] == "MODELLED"


def test_risk_node_evidence_summary():
    """Verify risk_assessment_node aggregates evidence list into evidence_summary."""
    ev1 = create_evidence_record(
        source_id="wx", provider="P", dataset="D",
        source_type=SourceType.API, authority_class=AuthorityClass.FORECAST,
        data_class=DataClass.FORECAST, status=EvidenceStatus.AVAILABLE,
    )
    ev2 = create_evidence_record(
        source_id="naval", provider="P", dataset="D",
        source_type=SourceType.UNAVAILABLE, authority_class=AuthorityClass.OFFICIAL_GOVERNMENT_REQUIRED,
        data_class=DataClass.UNAVAILABLE, status=EvidenceStatus.UNAVAILABLE,
    )

    state: SamudraState = {
        "weather_data": {"status": "OK"},
        "ocean_data": {"status": "OK"},
        "geofence_data": {"status": "OK"},
        "evidence": [ev1, ev2],
    }

    res = risk_assessment_node(state)
    assert "evidence_summary" in res
    summary = res["evidence_summary"]
    assert summary["total_sources"] == 2
    assert summary["available_count"] == 1
    assert summary["unavailable_count"] == 1
    assert summary["completeness_score"] == 50.0
