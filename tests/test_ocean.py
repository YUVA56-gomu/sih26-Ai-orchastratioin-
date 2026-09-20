"""
tests/test_ocean.py
───────────────────
Unit tests for Phase 2.2 Ocean Hydrodynamics implementation.

All Copernicus API calls are 100% mocked — zero live network requests.

Test cases:
  1. test_get_salinity
  2. test_get_current_profile
  3. test_snapshot_contains_all_ocean_observations
  4. test_ocean_provenance
  5. test_ocean_artifact
  6. test_strong_current_risk
  7. test_short_period_high_wave_risk
  8. test_missing_ocean_data_does_not_crash
  9. test_existing_surface_current_compatibility
 10. test_ocean_node_integration
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Environment & Dependency Stubs for Test Runner ───────────────────────────
def _stub_dependencies():
    def _mod(name):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)
        return sys.modules[name]

    # Stub langgraph if not present
    try:
        import langgraph.graph
    except ImportError:
        lg = _mod("langgraph")
        lg_graph = _mod("langgraph.graph")
        lg_graph.StateGraph = MagicMock
        lg_graph.START = "__start__"
        lg_graph.END = "__end__"
        _mod("langgraph.checkpoint")
        _mod("langgraph.checkpoint.memory").MemorySaver = MagicMock

    # Stub langchain_core if not present
    try:
        import langchain_core.messages
    except ImportError:
        _mod("langchain_core")
        lc_msgs = _mod("langchain_core.messages")
        lc_msgs.HumanMessage = MagicMock
        lc_msgs.SystemMessage = MagicMock

    # Stub copernicusmarine
    cm = _mod("copernicusmarine")
    if not hasattr(cm, "open_dataset"):
        cm.open_dataset = MagicMock()


_stub_dependencies()

import numpy as np
from tools.copernicus_service import (
    SALINITY_DATASET,
    CURRENT_DATASET,
    TEMPERATURE_DATASET,
    WAVE_DATASET,
    _cache,
    get_salinity,
    get_current_profile,
    get_currents,
    get_temperature,
    get_waves,
    get_copernicus_marine_snapshot,
)
from tools.artifact_factory import (
    create_ocean_conditions_artifact,
)
from tools.marine_risk import (
    calculate_marine_risk,
)
from graph.nodes.data_ocean import ocean_data_node


@pytest.fixture(autouse=True)
def clear_copernicus_cache():
    """Clear Copernicus in-memory cache before every test."""
    _cache.clear()


# ── Mock Data Helper ──────────────────────────────────────────────────────────
class _MockCoord:
    def __init__(self, val):
        self.values = np.array(val)


class _MockDataVar:
    def __init__(self, val, depth_val: float = 0.49):
        self.val = val
        self.dims = ["time", "latitude", "longitude", "depth"]
        self.coords = {
            "time": _MockCoord("2026-09-20T12:00:00"),
            "latitude": _MockCoord(13.08),
            "longitude": _MockCoord(80.27),
            "depth": _MockCoord(depth_val),
        }
        self.values = np.array(val)

    def sel(self, **kwargs):
        return self

    def sortby(self, *args, **kwargs):
        return self

    def isel(self, *args, **kwargs):
        return self

    def squeeze(self, *args, **kwargs):
        return self


class _MockDataset:
    def __init__(self, var_map: dict, depth_val: float = 0.49):
        self.var_map = {k: _MockDataVar(v, depth_val) for k, v in var_map.items()}
        self.data_vars = list(self.var_map.keys())

    def __getitem__(self, key):
        if key not in self.var_map:
            raise KeyError(key)
        return self.var_map[key]

    def __contains__(self, key):
        return key in self.var_map


# ── 1. test_get_salinity ──────────────────────────────────────────────────────
@patch("copernicusmarine.open_dataset")
def test_get_salinity(mock_open):
    mock_ds = _MockDataset({"so": 35.2})
    mock_open.return_value = mock_ds

    res = get_salinity(13.08, 80.27)

    assert res["parameter"] == "sea_water_salinity"
    assert res["variable"] == "so"
    assert res["value"] == 35.2
    assert res["unit"] == "psu"
    assert res["status"] == "OBSERVED"
    assert res["dataset_id"] == SALINITY_DATASET
    assert res["latitude"] == 13.08
    assert res["longitude"] == 80.27
    assert res["observation_time"] == "2026-09-20T12:00:00"


# ── 2. test_get_current_profile ───────────────────────────────────────────────
@patch("copernicusmarine.open_dataset")
def test_get_current_profile(mock_open):
    # Mock return for uo=0.6, vo=0.8 at various depths
    mock_ds = _MockDataset({"uo": 0.6, "vo": 0.8}, depth_val=0.49)
    mock_open.return_value = mock_ds

    res = get_current_profile(13.08, 80.27, target_depths=[0.49, 9.57, 21.6, 51.9])

    assert res["parameter"] == "ocean_current_profile"
    assert res["dataset_id"] == CURRENT_DATASET
    assert len(res["profile"]) == 4

    level0 = res["profile"][0]
    assert level0["requested_depth_m"] == 0.49
    assert level0["depth_m"] == 0.49
    assert level0["u_ms"] == pytest.approx(0.6)
    assert level0["v_ms"] == pytest.approx(0.8)
    assert level0["speed_ms"] == pytest.approx(1.0)
    assert level0["direction_deg"] == pytest.approx(36.869897, abs=1e-2)


# ── 3. test_snapshot_contains_all_ocean_observations ─────────────────────────
@patch("tools.copernicus_service.get_temperature")
@patch("tools.copernicus_service.get_salinity")
@patch("tools.copernicus_service.get_currents")
@patch("tools.copernicus_service.get_current_profile")
@patch("tools.copernicus_service.get_waves")
def test_snapshot_contains_all_ocean_observations(mock_wav, mock_prof, mock_cur, mock_sal, mock_temp):
    mock_temp.return_value = {"parameter": "sea_surface_temperature", "value": 29.5, "unit": "degC"}
    mock_sal.return_value = {"parameter": "sea_water_salinity", "value": 35.1, "unit": "psu"}
    mock_cur.return_value = {"parameter": "ocean_current", "speed_ms": 0.5, "direction_deg": 120.0}
    mock_prof.return_value = {"parameter": "ocean_current_profile", "profile": [{"depth_m": 0.49, "speed_ms": 0.5}]}
    mock_wav.return_value = {"parameter": "waves", "significant_wave_height_m": 1.2}

    snapshot = get_copernicus_marine_snapshot(13.08, 80.27)

    assert snapshot["status"] == "COMPLETE"
    assert "temperature" in snapshot["observations"]
    assert "salinity" in snapshot["observations"]
    assert "currents" in snapshot["observations"]
    assert "current_profile" in snapshot["observations"]
    assert "waves" in snapshot["observations"]


# ── 4. test_ocean_provenance ──────────────────────────────────────────────────
@patch("tools.copernicus_service.get_temperature")
@patch("tools.copernicus_service.get_salinity")
@patch("tools.copernicus_service.get_currents")
@patch("tools.copernicus_service.get_current_profile")
@patch("tools.copernicus_service.get_waves")
def test_ocean_provenance(mock_wav, mock_prof, mock_cur, mock_sal, mock_temp):
    mock_temp.return_value = {"value": 29.5}
    mock_sal.return_value = {"value": 35.1}
    mock_cur.return_value = {"speed_ms": 0.5}
    mock_prof.return_value = {"profile": [{"depth_m": 0.49}, {"depth_m": 9.57}]}
    mock_wav.return_value = {"significant_wave_height_m": 1.2}

    snapshot = get_copernicus_marine_snapshot(13.08, 80.27)

    prov = snapshot["provenance"]
    param_map = {p["parameter"]: p for p in prov}

    assert "sea_surface_temperature" in param_map
    assert param_map["sea_surface_temperature"]["dataset_id"] == TEMPERATURE_DATASET

    assert "sea_water_salinity" in param_map
    assert param_map["sea_water_salinity"]["dataset_id"] == SALINITY_DATASET

    assert "ocean_current" in param_map
    assert param_map["ocean_current"]["dataset_id"] == CURRENT_DATASET

    assert "ocean_current_profile" in param_map
    assert param_map["ocean_current_profile"]["dataset_id"] == CURRENT_DATASET
    assert param_map["ocean_current_profile"]["depth_levels_m"] == [0.49, 9.57]

    assert "waves" in param_map
    assert param_map["waves"]["dataset_id"] == WAVE_DATASET


# ── 5. test_ocean_artifact ─────────────────────────────────────────────────────
def test_ocean_artifact():
    location = {"status": "FOUND", "name": "Chennai Port", "latitude": 13.08, "longitude": 80.27}
    ocean_data = {
        "status": "COMPLETE",
        "observations": {
            "temperature": {"value": 28.5, "unit": "°C", "observation_time": "2026-09-20T12:00:00"},
            "salinity": {"value": 35.0, "unit": "psu", "observation_time": "2026-09-20T12:00:00"},
            "currents": {"speed_ms": 1.2, "direction_deg": 180.0, "u_ms": 0.0, "v_ms": -1.2},
            "current_profile": {"profile": [{"requested_depth_m": 0.49, "depth_m": 0.49, "speed_ms": 1.2}]},
            "waves": {"significant_wave_height_m": 1.8, "mean_wave_period_s": 6.5, "wave_direction_deg": 220.0},
        },
        "provenance": [{"parameter": "salinity", "dataset_id": SALINITY_DATASET}],
        "retrieved_at": "2026-09-20T12:00:00Z",
    }

    art = create_ocean_conditions_artifact(location, ocean_data)

    assert art is not None
    assert art["type"] == "ocean_card"
    assert art["title"] == "Ocean Hydrodynamics — Chennai Port"

    data = art["data"]
    assert data["temperature"]["value"] == 28.5
    assert data["salinity"]["value"] == 35.0
    assert data["currents"]["speed_ms"] == 1.2
    assert len(data["currents"]["profile"]) == 1
    assert data["waves"]["significant_wave_height_m"] == 1.8


# ── 6. test_strong_current_risk ───────────────────────────────────────────────
def test_strong_current_risk():
    ocean = {
        "observations": {
            "currents": {"speed_ms": 1.8, "direction_deg": 90.0},
            "waves": {"significant_wave_height_m": 0.5, "mean_wave_period_s": 8.0},
        }
    }
    weather = {"current": {"wind_speed_10m": 10.0}}
    geofence = {}

    risk = calculate_marine_risk(ocean, weather, geofence)

    assert any("Strong ocean current velocity detected." in r for r in risk["reasons"])
    assert risk["evaluated_parameters"]["ocean_current_speed_ms"] == 1.8
    assert risk["risk_score"] >= 20


# ── 7. test_short_period_high_wave_risk ──────────────────────────────────────
def test_short_period_high_wave_risk():
    ocean = {
        "observations": {
            "waves": {"significant_wave_height_m": 1.8, "mean_wave_period_s": 4.5, "wave_direction_deg": 180.0},
            "currents": {"speed_ms": 0.3},
        }
    }
    weather = {"current": {"wind_speed_10m": 10.0}}
    geofence = {}

    risk = calculate_marine_risk(ocean, weather, geofence)

    assert any("Steep, short-period wave conditions." in r for r in risk["reasons"])
    assert risk["evaluated_parameters"]["wave_height_m"] == 1.8
    assert risk["evaluated_parameters"]["wave_period_s"] == 4.5


# ── 8. test_missing_ocean_data_does_not_crash ────────────────────────────────
def test_missing_ocean_data_does_not_crash():
    empty_ocean = {}
    weather = {}
    geofence = {}

    # Risk engine with empty data
    risk = calculate_marine_risk(empty_ocean, weather, geofence)
    assert risk["risk_level"] == "LOW"
    assert risk["risk_score"] == 0

    # Artifact creation with missing/blocked ocean data
    location = {"status": "FOUND", "latitude": 13.08, "longitude": 80.27}
    art = create_ocean_conditions_artifact(location, {"status": "BLOCKED"})
    assert art is None

    # Ocean node with empty location
    state = {"plan": {"domains_needed": ["ocean"]}, "location": {"status": "MISSING"}}
    res = ocean_data_node(state)
    assert res["ocean_data"]["status"] == "BLOCKED"


# ── 9. test_existing_surface_current_compatibility ───────────────────────────
@patch("copernicusmarine.open_dataset")
def test_existing_surface_current_compatibility(mock_open):
    mock_ds = _MockDataset({"uo": 0.3, "vo": 0.4})
    mock_open.return_value = mock_ds

    res = get_currents(13.08, 80.27)

    # Validate exact backward compatible structure
    assert res["parameter"] == "ocean_current"
    assert res["u_ms"] == pytest.approx(0.3)
    assert res["v_ms"] == pytest.approx(0.4)
    assert res["speed_ms"] == pytest.approx(0.5)
    assert res["direction_deg"] == pytest.approx(36.869897, abs=1e-2)
    assert res["speed_unit"] == "m/s"
    assert res["status"] == "OBSERVED"
    assert res["dataset_id"] == CURRENT_DATASET


# ── 10. test_ocean_node_integration ──────────────────────────────────────────
@patch("graph.nodes.data_ocean.get_copernicus_marine_snapshot")
def test_ocean_node_integration(mock_snapshot):
    mock_snapshot.return_value = {
        "status": "COMPLETE",
        "observations": {
            "temperature": {"value": 29.0},
            "salinity": {"value": 35.0},
            "currents": {"speed_ms": 0.5},
            "current_profile": {"profile": []},
            "waves": {"significant_wave_height_m": 1.0},
        },
    }

    state = {
        "plan": {"domains_needed": ["ocean"]},
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
    }

    res = ocean_data_node(state)

    assert "ocean_data" in res
    assert res["ocean_data"]["status"] == "COMPLETE"
    assert "ocean_data_collector" in res["node_trace"]
