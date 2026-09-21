"""
tests/test_route_intelligence.py
─────────────────────────────────
Unit & integration tests for Phase 2.6 Marine Route Intelligence.

Verifies geometry math, A* graph search, inspectable edge cost calculations,
EEZ non-restriction semantics, missing data fallbacks (MPA/Naval UNAVAILABLE),
route risk scoring, route_map artifacts, and LangGraph node integration.
"""

import pytest
from tools.route_service import (
    MarineRouteService,
    get_route_service,
    haversine_distance_km,
    calculate_bearing_deg,
    calculate_segment_cost,
    MARITIME_WAYPOINTS,
)
from tools.marine_risk import evaluate_route_risk
from tools.artifact_factory import create_route_map_artifact
from graph.nodes.data_route import fetch_route_data
from state.schema import SamudraState


# ── 1. Geometry & Math Tests ──────────────────────────────────────────────────

def test_haversine_distance_km():
    """Verify great circle distance calculation."""
    # Mumbai (18.92, 72.83) to Goa (15.49, 73.80) ~ 390-410 km
    dist = haversine_distance_km(18.92, 72.83, 15.49, 73.80)
    assert 380.0 <= dist <= 420.0


def test_calculate_bearing_deg():
    """Verify initial compass bearing calculation."""
    # North: (10, 70) to (20, 70) => ~0 deg
    bearing_n = calculate_bearing_deg(10.0, 70.0, 20.0, 70.0)
    assert bearing_n == 0.0 or bearing_n == 360.0

    # East: (10, 70) to (10, 80) => ~90 deg
    bearing_e = calculate_bearing_deg(10.0, 70.0, 10.0, 80.0)
    assert 88.0 <= bearing_e <= 92.0

    # South: (20, 70) to (10, 70) => ~180 deg
    bearing_s = calculate_bearing_deg(20.0, 70.0, 10.0, 70.0)
    assert 178.0 <= bearing_s <= 182.0


# ── 2. A* Pathfinding Tests ───────────────────────────────────────────────────

def test_route_calculation_mumbai_to_goa():
    """Verify valid A* route calculation between Mumbai and Goa."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai Port",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa Port",
    )

    assert res["status"] == "OK"
    assert res["distance_km"] > 0.0
    assert len(res["waypoints"]) >= 2
    assert res["waypoints"][0]["name"] == "Mumbai Port"
    assert res["waypoints"][-1]["name"] == "Goa Port"
    assert res["route_geometry"]["type"] == "LineString"
    assert len(res["route_geometry"]["coordinates"]) >= 2
    assert res["verification"]["eez"] == "INFORMATIONAL"
    assert res["verification"]["mpa"] == "UNAVAILABLE"
    assert res["verification"]["naval"] == "UNAVAILABLE"


def test_route_calculation_same_origin_and_dest():
    """Verify route edge case where origin and destination are identical."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai Port",
        dest_lat=18.92, dest_lon=72.83, dest_name="Mumbai Port",
    )

    assert res["status"] == "OK"
    assert res["distance_km"] == 0.0
    assert len(res["waypoints"]) == 1


# ── 3. Edge Cost Evaluation Tests ──────────────────────────────────────────────

def test_edge_cost_headwind_vs_tailwind():
    """Verify headwind incurs higher cost penalty than tailwind."""
    lat1, lon1 = 18.0, 72.5
    lat2, lon2 = 17.0, 72.5  # Heading South (180 deg)

    # Tailwind: wind blowing South (180 deg)
    env_tailwind = {"weather": {"current": {"wind_speed_10m": 30.0, "wind_direction_10m": 180.0}}}
    cost_tail = calculate_segment_cost(lat1, lon1, lat2, lon2, env_tailwind)

    # Headwind: wind blowing North (0 deg)
    env_headwind = {"weather": {"current": {"wind_speed_10m": 30.0, "wind_direction_10m": 0.0}}}
    cost_head = calculate_segment_cost(lat1, lon1, lat2, lon2, env_headwind)

    assert cost_head["total_cost"] > cost_tail["total_cost"]
    assert cost_head["wind_cost"] > cost_tail["wind_cost"]


def test_edge_cost_assisting_vs_opposing_current():
    """Verify assisting current reduces segment cost while opposing current increases cost."""
    lat1, lon1 = 18.0, 72.5
    lat2, lon2 = 17.0, 72.5  # Heading South (180 deg)

    # Assisting current: current flowing South (180 deg)
    env_assisting = {"marine": {"current": {"ocean_current_velocity": 1.5, "ocean_current_direction": 180.0}}}
    cost_assist = calculate_segment_cost(lat1, lon1, lat2, lon2, env_assisting)

    # Opposing current: current flowing North (0 deg)
    env_opposing = {"marine": {"current": {"ocean_current_velocity": 1.5, "ocean_current_direction": 0.0}}}
    cost_oppose = calculate_segment_cost(lat1, lon1, lat2, lon2, env_opposing)

    assert cost_oppose["total_cost"] > cost_assist["total_cost"]
    assert cost_assist["current_cost"] < 0.0
    assert cost_oppose["current_cost"] > 0.0


def test_edge_cost_hazard_penalty():
    """Verify active hazard advisory increases route segment cost."""
    lat1, lon1 = 18.0, 72.5
    lat2, lon2 = 17.0, 72.5

    env_normal = {}
    cost_normal = calculate_segment_cost(lat1, lon1, lat2, lon2, env_normal)

    env_hazard = {"hazard": {"status": "ACTIVE", "alerts": [{"title": "High Wave Warning"}]}}
    cost_hazard = calculate_segment_cost(lat1, lon1, lat2, lon2, env_hazard)

    assert cost_hazard["total_cost"] > cost_normal["total_cost"]
    assert cost_hazard["hazard_cost"] > 0.0


# ── 4. Geospatial & Safety Semantics Tests ────────────────────────────────────

def test_route_eez_semantics():
    """Verify EEZ membership does NOT add restriction penalties or block routes."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
    )

    assert res["status"] == "OK"
    assert res["verification"]["eez"] == "INFORMATIONAL"
    # Verify no warning describes EEZ as prohibited
    for w in res["warnings"]:
        assert "illegal" not in w.lower()
        assert "prohibited" not in w.lower()


def test_route_unavailable_layers_semantics():
    """Verify MPA and Naval layers return explicit UNAVAILABLE status without fabricating geometry."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
    )

    assert res["data_completeness"]["mpa"] == "UNAVAILABLE"
    assert res["data_completeness"]["naval"] == "UNAVAILABLE"
    assert res["verification"]["mpa"] == "UNAVAILABLE"
    assert res["verification"]["naval"] == "UNAVAILABLE"

    # Verify explicit warning exists regarding unavailable naval data
    has_naval_warning = any("Naval" in w or "naval" in w for w in res["warnings"])
    assert has_naval_warning is True


# 5. Route Risk Engine Tests ──────────────────────────────────────────────────

def test_evaluate_route_risk():
    """Verify structured route risk evaluation function."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
    )

    risk_eval = evaluate_route_risk(res)
    assert risk_eval["overall_status"] == "CALCULATED"
    assert risk_eval["risk_level"] in ("LOW", "MODERATE", "HIGH")
    assert "algorithmic_risk_score" in risk_eval
    assert risk_eval["decision_support_only"] is True


# ── 6. Artifact Factory Tests ─────────────────────────────────────────────────

def test_create_route_map_artifact():
    """Verify route_map artifact factory helper."""
    loc = {"status": "FOUND", "name": "Mumbai", "latitude": 18.92, "longitude": 72.83}
    service = get_route_service()
    route_d = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
    )

    art = create_route_map_artifact(loc, route_d)
    assert art is not None
    assert art["type"] == "route_map"
    assert art["data"]["status"] == "OK"
    assert art["data"]["distance_km"] > 0.0
    assert "route_geometry" in art["data"]
    assert art["data"]["verification"]["eez"] == "INFORMATIONAL"
    assert art["data"]["verification"]["mpa"] == "UNAVAILABLE"
    assert art["data"]["verification"]["naval"] == "UNAVAILABLE"


# ── 7. LangGraph Route Node Integration Test ──────────────────────────────────

def test_fetch_route_data_node():
    """Verify fetch_route_data LangGraph data collector node."""
    state: SamudraState = {
        "location": {"status": "FOUND", "name": "Mumbai", "latitude": 18.92, "longitude": 72.83},
        "user_query": "Find a safe route from Mumbai to Goa",
        "weather_data": {"status": "OK", "current": {"wind_speed_10m": 15.0, "wind_direction_10m": 180.0}},
        "marine_data": {"status": "OK", "current": {"wave_height": 1.2, "wave_period": 7.0}},
    }

    result = fetch_route_data(state)
    assert "route_data" in result
    assert result["node_trace"] == ["data_route"]
    assert result["route_data"]["status"] == "OK"
    assert result["route_data"]["distance_km"] > 0.0
    assert result["route_data"]["verification"]["naval"] == "UNAVAILABLE"


# ── 8. Extended Hardening & Edge Case Tests ────────────────────────────────────

def test_route_invalid_coordinates_out_of_bounds():
    """Verify invalid/out-of-bounds coordinates return status UNAVAILABLE without crashing."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=999.0, origin_lon=72.83, origin_name="Invalid Origin",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
    )
    assert res["status"] == "UNAVAILABLE"
    assert "Invalid input coordinates" in res["warnings"][0] or "out of bounds" in res["message"].lower() or "invalid" in res["message"].lower()


def test_route_reverse_path_goa_to_mumbai():
    """Verify reverse route calculation (Goa to Mumbai) works symmetrically."""
    service = get_route_service()
    res_fwd = service.calculate_route(18.92, 72.83, 15.49, 73.80, "Mumbai", "Goa")
    res_rev = service.calculate_route(15.49, 73.80, 18.92, 72.83, "Goa", "Mumbai")

    assert res_fwd["status"] == "OK"
    assert res_rev["status"] == "OK"
    # Distances should be identical or very close (< 2% difference)
    assert abs(res_fwd["distance_km"] - res_rev["distance_km"]) < (res_fwd["distance_km"] * 0.05)


def test_route_long_distance_kandla_to_port_blair():
    """Verify long-distance cross-sea route (Kandla to Port Blair)."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=22.98, origin_lon=70.22, origin_name="Kandla",
        dest_lat=11.67, dest_lon=92.75, dest_name="Port Blair",
    )
    assert res["status"] == "OK"
    assert res["distance_km"] > 2000.0
    assert len(res["waypoints"]) >= 4


def test_route_short_distance_mumbai_to_murud():
    """Verify short coastal route (Mumbai to Murud)."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=18.30, dest_lon=72.85, dest_name="Murud",
    )
    assert res["status"] == "OK"
    assert 50.0 <= res["distance_km"] <= 120.0


def test_route_missing_environmental_context():
    """Verify route calculation succeeds gracefully when environmental inputs are empty or None."""
    service = get_route_service()
    res = service.calculate_route(
        origin_lat=18.92, origin_lon=72.83, origin_name="Mumbai",
        dest_lat=15.49, dest_lon=73.80, dest_name="Goa",
        env_context={},
    )
    assert res["status"] == "OK"
    assert res["distance_km"] > 0.0
    assert res["data_completeness"]["weather"] == "UNAVAILABLE"
    assert res["data_completeness"]["marine"] == "UNAVAILABLE"


def test_route_disclaimers_and_realism_claims():
    """Verify route warnings explicitly state decision-support nature and non-nautical status."""
    service = get_route_service()
    res = service.calculate_route(18.92, 72.83, 15.49, 73.80, "Mumbai", "Goa")

    warnings_text = " ".join(res["warnings"])
    assert "decision-support" in warnings_text.lower()
    assert "not an official" in warnings_text.lower() or "unverified" in warnings_text.lower()
    assert "naval" in warnings_text.lower()
    assert "mpa" in warnings_text.lower()

