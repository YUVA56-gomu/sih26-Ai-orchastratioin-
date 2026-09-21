"""
tests/test_geospatial.py
────────────────────────
Unit and integration tests for SAMUDRA AI Phase 2.5 GIS Spatial Engine,
point-in-polygon geometry, distance calculations, dataset provenance,
zone category semantics (EEZ vs restricted zones), naval fallback safety,
geofence risk evaluation, and artifact creation.
"""

from __future__ import annotations

import os
import pytest
from tools.gis_service import (
    DEFAULT_PROXIMITY_BUFFER_KM,
    GISFeature,
    GISLayer,
    GISService,
    bounding_box_contains,
    compute_bounding_box,
    distance_to_geometry_boundary_km,
    distance_to_segment_km,
    get_gis_service,
    haversine_distance_km,
    point_in_multipolygon,
    point_in_polygon,
)
from tools.geofence import check_geofence
from graph.nodes.data_geofence import geofence_data_node
from tools.marine_risk import calculate_marine_risk
from tools.artifact_factory import create_geofence_alert_artifact


# ── 1. Geometry Tests ────────────────────────────────────────────────────────

def test_point_in_polygon_inside():
    # Simple 1x1 degree square polygon
    poly = [[
        [10.0, 10.0],
        [20.0, 10.0],
        [20.0, 20.0],
        [10.0, 20.0],
        [10.0, 10.0]
    ]]
    # Point at lat 15, lon 15
    assert point_in_polygon(15.0, 15.0, poly) is True


def test_point_in_polygon_outside():
    poly = [[
        [10.0, 10.0],
        [20.0, 10.0],
        [20.0, 20.0],
        [10.0, 20.0],
        [10.0, 10.0]
    ]]
    # Point at lat 25, lon 25 (outside)
    assert point_in_polygon(25.0, 25.0, poly) is False
    assert point_in_polygon(5.0, 15.0, poly) is False


def test_point_in_polygon_with_hole():
    # Square with a hole in center
    exterior = [[10.0, 10.0], [20.0, 10.0], [20.0, 20.0], [10.0, 20.0], [10.0, 10.0]]
    hole = [[14.0, 14.0], [16.0, 14.0], [16.0, 16.0], [14.0, 16.0], [14.0, 14.0]]
    poly = [exterior, hole]

    # Inside exterior, outside hole
    assert point_in_polygon(12.0, 12.0, poly) is True
    # Inside hole
    assert point_in_polygon(15.0, 15.0, poly) is False


def test_point_in_multipolygon():
    poly1 = [[10.0, 10.0], [12.0, 10.0], [12.0, 12.0], [10.0, 12.0], [10.0, 10.0]]
    poly2 = [[20.0, 20.0], [22.0, 20.0], [22.0, 22.0], [20.0, 22.0], [20.0, 20.0]]
    multipoly = [[poly1], [poly2]]

    assert point_in_multipolygon(11.0, 11.0, multipoly) is True
    assert point_in_multipolygon(21.0, 21.0, multipoly) is True
    assert point_in_multipolygon(15.0, 15.0, multipoly) is False


def test_bounding_box_contains_and_compute():
    geom = {
        "type": "Polygon",
        "coordinates": [[[70.0, 10.0], [80.0, 10.0], [80.0, 20.0], [70.0, 20.0], [70.0, 10.0]]]
    }
    bbox = compute_bounding_box(geom)
    assert bbox == (10.0, 70.0, 20.0, 80.0)
    assert bounding_box_contains(15.0, 75.0, bbox) is True
    assert bounding_box_contains(25.0, 75.0, bbox) is False


# ── 2. Distance Tests ────────────────────────────────────────────────────────

def test_haversine_distance_km():
    # Distance between Mumbai (18.92, 72.83) and Goa (15.49, 73.82)
    dist = haversine_distance_km(18.92, 72.83, 15.49, 73.82)
    assert 380.0 < dist < 420.0


def test_distance_to_segment_km():
    # Point directly perpendicular to horizontal line segment
    dist = distance_to_segment_km(1.0, 5.0, 0.0, 0.0, 0.0, 10.0)
    # 1 degree lat is ~111 km
    assert 100.0 < dist < 120.0


def test_eez_semantics_separated_from_restricted_zone():
    """Verify that being inside an EEZ does NOT mean inside a restricted zone."""
    service = GISService()
    # Coordinates inside Indian EEZ (e.g. 15.0°N, 73.0°E near Karwar/Goa)
    res = service.check_geofence(15.0, 73.0, proximity_threshold_km=50.0)
    assert res["status"] == "OK"
    assert res["inside_eez"] is True
    assert res["inside_restricted_zone"] is False  # EEZ is NOT a restricted zone!
    assert res["proximity_buffer_km"] == 50.0
    assert len(res["matched_eez"]) >= 1
    assert len(res["matched_restrictions"]) == 0


# ── 3. Data & GeoJSON Loading Tests ──────────────────────────────────────────

def test_load_geojson_eez_file():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gis")
    eez_file = os.path.join(data_dir, "eez_india.geojson")
    assert os.path.exists(eez_file)

    service = GISService(data_dir=data_dir)
    assert "eez_india" in service.layers

    layer = service.layers["eez_india"]
    assert layer.category == "EEZ"
    assert layer.data_class == "INFORMATIONAL_GIS"
    assert layer.authority_class == "RESEARCH_INSTITUTION"
    assert layer.provider == "Flanders Marine Institute (VLIZ)"
    assert len(layer.features) >= 1


def test_missing_geojson_file_fallback():
    service = GISService(data_dir="/tmp/non_existent_gis_dir")
    assert "eez_india" in service.layers  # Embedded fallback initialized


# ── 4. Provenance & Policy Tests ─────────────────────────────────────────────

def test_geofence_provenance_metadata():
    res = check_geofence(15.0, 73.0)
    assert res["status"] == "OK"

    prov = res.get("provenance", {})
    assert prov.get("source_type") == "RESEARCH_INSTITUTION"
    assert prov.get("authority") == "INFORMATIONAL_GIS"
    assert "disclaimer" in prov


def test_naval_restricted_unavailable_fallback():
    """Verify naval/military restricted zones return explicit UNAVAILABLE status without false risk or fake alerts."""
    res = check_geofence(15.0, 73.0)
    layers = res.get("layers", [])

    naval_layer = next((l for l in layers if l.get("category") == "NAVAL_RESTRICTED"), None)
    assert naval_layer is not None
    assert naval_layer.get("status") == "UNAVAILABLE"
    assert naval_layer.get("data_class") == "UNAVAILABLE"
    assert naval_layer.get("authority_class") == "OFFICIAL_GOVERNMENT_REQUIRED"
    assert "message" in naval_layer

    # Verify UNAVAILABLE naval data does NOT generate fake alerts or false inside status
    assert res["inside_restricted_zone"] is False
    loc = {"status": "FOUND", "name": "Karwar", "latitude": 15.0, "longitude": 73.0}
    art = create_geofence_alert_artifact(loc, res)
    assert art is None  # No fake alert for unavailable dataset


def test_eez_only_does_not_add_restriction_risk_score():
    """Verify that being inside EEZ alone adds 0 restriction penalty points to marine risk."""
    geofence_eez_only = {
        "inside_eez": True,
        "inside_restricted_zone": False,
        "proximity_warning": False,
        "matched_zones": [{"category": "EEZ", "name": "Indian EEZ"}],
    }
    risk = calculate_marine_risk({}, {}, geofence_eez_only)
    assert risk["risk_score"] == 0  # EEZ context produces 0 penalty points
    assert not any("restricted zone" in r for r in risk["reasons"])


def test_mpa_and_restricted_zone_scoring():
    geofence_mpa = {
        "inside_eez": True,
        "inside_restricted_zone": True,
        "proximity_warning": False,
        "matched_zones": [{"category": "MPA", "name": "Marine Sanctuary"}],
    }
    risk_mpa = calculate_marine_risk({}, {}, geofence_mpa)
    assert risk_mpa["risk_score"] >= 50
    assert any("Marine Protected Area" in r for r in risk_mpa["reasons"])

    geofence_proximity = {
        "inside_eez": True,
        "inside_restricted_zone": False,
        "proximity_warning": True,
        "matched_zones": [],
    }
    risk_prox = calculate_marine_risk({}, {}, geofence_proximity)
    assert risk_prox["risk_score"] >= 15
    assert any("proximity buffer" in r for r in risk_prox["reasons"])


def test_geofence_alert_artifact_creation():
    loc = {"status": "FOUND", "name": "Gulf of Mannar", "latitude": 9.0, "longitude": 79.0}
    geofence_data = {
        "inside_eez": True,
        "inside_restricted_zone": True,
        "proximity_warning": False,
        "matched_zones": [{"name": "Gulf of Mannar Marine National Park", "category": "MPA"}],
        "nearest_boundary": {"zone_name": "Gulf of Mannar Marine National Park", "distance_km": 0.0},
        "layers": [{"category": "MPA", "status": "AVAILABLE"}],
        "provenance": {"source_type": "RESEARCH_INSTITUTION", "authority": "INFORMATIONAL_GIS"},
    }

    art = create_geofence_alert_artifact(loc, geofence_data)
    assert art is not None
    assert art["type"] == "geofence_alert"
    assert "Geofence Alert" in art["title"]
    assert art["data"]["inside_restricted_zone"] is True
    assert art["data"]["provenance"]["source_type"] == "RESEARCH_INSTITUTION"


# ── 6. Graph Data Collector Integration Test ──────────────────────────────────

def test_geofence_data_node_execution():
    state = {
        "location": {
            "status": "FOUND",
            "name": "Karwar",
            "latitude": 14.81,
            "longitude": 74.13,
        }
    }
    res = geofence_data_node(state)
    assert "geofence_data" in res
    assert res["geofence_data"]["status"] == "OK"
    assert "geofence_data_collector" in res["node_trace"]
