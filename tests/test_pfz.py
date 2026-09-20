"""
tests/test_pfz.py
──────────────────
Unit tests for Phase 2.3 Potential Fishing Zone (PFZ) & Fishery Intelligence.

All external calls are 100% mocked — zero live network requests.

Test cases:
  1. test_get_chlorophyll
  2. test_thermal_front_detection
  3. test_chlorophyll_gradient
  4. test_pfz_candidate_scoring
  5. test_incois_bulletin_parser
  6. test_pfz_artifact_schema
  7. test_missing_chlorophyll_fallback
  8. test_fishery_reasoner_context
  9. test_fishery_data_node
 10. test_pfz_provenance
 11. test_backward_compatibility_find_nearest_pfz
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

    try:
        import langchain_core.messages
    except ImportError:
        _mod("langchain_core")
        lc_msgs = _mod("langchain_core.messages")
        lc_msgs.HumanMessage = MagicMock
        lc_msgs.SystemMessage = MagicMock

    cm = _mod("copernicusmarine")
    if not hasattr(cm, "open_dataset"):
        cm.open_dataset = MagicMock()


_stub_dependencies()

import numpy as np
from tools.copernicus_service import (
    CHLOROPHYLL_DATASET,
    get_chlorophyll,
)
from tools.copernicus_grid import get_chlorophyll_grid
from tools.pfz_fronts import (
    detect_thermal_fronts,
    analyze_chlorophyll_productivity,
    calculate_spatial_gradient,
)
from tools.pfz_scoring import calculate_candidate_score
from tools.incois_bulletin import (
    parse_incois_bulletin,
    get_default_incois_status,
)
from tools.pfz_service import (
    calculate_pfz_candidates,
    find_nearest_pfz,
)
from tools.artifact_factory import create_pfz_map_artifact
from graph.nodes.data_fishery import fishery_data_node


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
            "latitude": _MockCoord(14.81),
            "longitude": _MockCoord(74.13),
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


# ── 1. test_get_chlorophyll ───────────────────────────────────────────────────
@patch("copernicusmarine.open_dataset")
def test_get_chlorophyll(mock_open):
    mock_ds = _MockDataset({"chl": 0.62})
    mock_open.return_value = mock_ds

    res = get_chlorophyll(14.81, 74.13)

    assert res["parameter"] == "chlorophyll_a"
    assert res["variable"] == "chl"
    assert res["value"] == 0.62
    assert res["unit"] == "mg/m3"
    assert res["status"] == "MODEL_ANALYSIS"
    assert res["dataset_id"] == CHLOROPHYLL_DATASET
    assert res["latitude"] == 14.81
    assert res["longitude"] == 74.13
    assert res["observation_time"] == "2026-09-20T12:00:00"


# ── 2. test_thermal_front_detection ───────────────────────────────────────────
def test_thermal_front_detection():
    # Synthetic 3x3 grid with strong thermal step (27.0°C to 28.5°C)
    lats = [14.7, 14.8, 14.9]
    lons = [74.0, 74.1, 74.2]
    sst_vals = np.array([
        [27.0, 27.8, 28.5],
        [27.1, 27.9, 28.6],
        [27.2, 28.0, 28.7],
    ])

    grid_dict = {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        "status": "OBSERVED",
        "latitudes": lats,
        "longitudes": lons,
        "values": sst_vals,
    }

    fronts = detect_thermal_fronts(grid_dict, min_gradient_c_per_km=0.03)

    assert len(fronts) > 0
    top_front = fronts[0]
    assert "gradient_c_per_km" in top_front
    assert top_front["gradient_c_per_km"] >= 0.03
    assert "front_strength" in top_front
    assert top_front["front_strength"] > 0.0


# ── 3. test_chlorophyll_gradient ──────────────────────────────────────────────
def test_chlorophyll_gradient():
    lats = [14.7, 14.8, 14.9]
    lons = [74.0, 74.1, 74.2]
    chl_vals = np.array([
        [0.2, 0.5, 1.2],
        [0.3, 0.6, 1.3],
        [0.4, 0.7, 1.4],
    ])

    grid_dict = {
        "dataset_id": "cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m",
        "status": "MODEL_ANALYSIS",
        "latitudes": lats,
        "longitudes": lons,
        "values": chl_vals,
    }

    features = analyze_chlorophyll_productivity(grid_dict, min_gradient=0.005)

    assert len(features) > 0
    top_feat = features[0]
    assert "chlorophyll_mg_m3" in top_feat
    assert "chlorophyll_gradient" in top_feat
    assert "productivity_signal" in top_feat
    assert top_feat["chlorophyll_mg_m3"] > 0.0


# ── 4. test_pfz_candidate_scoring ─────────────────────────────────────────────
def test_pfz_candidate_scoring():
    score_dict = calculate_candidate_score(
        candidate_lat=14.90,
        candidate_lon=74.25,
        target_lat=14.81,
        target_lon=74.13,
        sst_val=27.5,
        sst_grad=0.08,
        chl_val=0.8,
        chl_grad=0.02,
    )

    assert "score" in score_dict
    assert 0.0 <= score_dict["score"] <= 1.0
    assert score_dict["factors"]["sst_suitability"] == pytest.approx(1.0)
    assert score_dict["factors"]["distance"] > 0.0
    assert score_dict["distance_km"] > 0.0


# ── 5. test_incois_bulletin_parser ────────────────────────────────────────────
def test_incois_bulletin_parser():
    # Unavailable fallback
    unavail = parse_incois_bulletin(None)
    assert unavail["status"] == "UNAVAILABLE"
    assert unavail["source"] == "INCOIS"

    # Active bulletin payload
    payload = {
        "status": "ACTIVE",
        "bulletin_id": "INCOIS_2026_09_20",
        "bulletin_candidates": [
            {"latitude": 14.85, "longitude": 74.20, "bearing_deg": 45, "distance_km": 15.0}
        ]
    }
    parsed = parse_incois_bulletin(payload)
    assert parsed["status"] == "ACTIVE"
    assert len(parsed["bulletin_candidates"]) == 1
    assert parsed["bulletin_candidates"][0]["latitude"] == 14.85


# ── 6. test_pfz_artifact_schema ───────────────────────────────────────────────
def test_pfz_artifact_schema():
    location = {"status": "FOUND", "name": "Karwar", "latitude": 14.81, "longitude": 74.13}
    fishery_data = {
        "status": "CALCULATED",
        "candidates": [
            {"latitude": 14.95, "longitude": 74.25, "score": 0.88, "sst_c": 27.8, "chlorophyll_mg_m3": 0.65}
        ],
        "thermal_fronts": [{"latitude": 14.95, "longitude": 74.25, "gradient_c_per_km": 0.07}],
        "chlorophyll_features": [{"latitude": 14.95, "longitude": 74.25, "chlorophyll_mg_m3": 0.65}],
        "bulletin": {"source": "INCOIS", "status": "UNAVAILABLE"},
        "provenance": [{"parameter": "chlorophyll_a", "dataset_id": CHLOROPHYLL_DATASET}],
    }

    art = create_pfz_map_artifact(location, fishery_data)

    assert art is not None
    assert art["type"] == "pfz_map"
    assert art["title"] == "PFZ Candidates near Karwar"

    data = art["data"]
    assert data["pfz_status"] == "CALCULATED"
    assert len(data["candidates"]) == 1
    assert len(data["thermal_fronts"]) == 1
    assert data["bulletin"]["status"] == "UNAVAILABLE"


# ── 7. test_missing_chlorophyll_fallback ──────────────────────────────────────
@patch("tools.pfz_service.get_sst_grid")
@patch("tools.pfz_service.get_chlorophyll_grid")
def test_missing_chlorophyll_fallback(mock_chl_grid, mock_sst_grid):
    # Mock SST grid present, Chlorophyll grid fails
    mock_sst_grid.return_value = {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        "status": "OBSERVED",
        "latitudes": [14.7, 14.8, 14.9],
        "longitudes": [74.0, 74.1, 74.2],
        "values": [[27.5, 27.8, 28.1], [27.6, 27.9, 28.2], [27.7, 28.0, 28.3]],
    }
    mock_chl_grid.side_effect = RuntimeError("Chlorophyll dataset unavailable")

    res = calculate_pfz_candidates(14.81, 74.13)

    assert res["status"] == "CALCULATED"
    assert len(res["candidates"]) > 0
    assert len(res["warnings"]) == 1
    assert "Chlorophyll" in res["warnings"][0]


# ── 8. test_fishery_reasoner_context ──────────────────────────────────────────
@patch("graph.nodes.reason_fishery.get_llm")
def test_fishery_reasoner_context(mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Thermal fronts and chlorophyll concentrations indicate favorable PFZ candidates 20km offshore Karwar."
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    from graph.nodes.reason_fishery import fishery_reasoning_node

    state = {
        "user_query": "Find PFZ near Karwar",
        "fishery_data": {
            "status": "CALCULATED",
            "candidates": [{"latitude": 14.95, "longitude": 74.25, "score": 0.88}],
            "thermal_fronts": [{"gradient_c_per_km": 0.08}],
        },
        "ocean_data": {"status": "COMPLETE"},
    }

    res = fishery_reasoning_node(state)

    assert "fishery_reasoning" in res
    assert "thermal fronts" in res["fishery_reasoning"].lower()
    assert "fishery_reasoner" in res["node_trace"]


# ── 9. test_fishery_data_node ──────────────────────────────────────────────────
@patch("graph.nodes.data_fishery.find_nearest_pfz")
def test_fishery_data_node(mock_pfz):
    mock_pfz.return_value = {"status": "CALCULATED", "candidates": [{"score": 0.85}]}

    state = {
        "plan": {"domains_needed": ["fishery"]},
        "location": {"status": "FOUND", "latitude": 14.81, "longitude": 74.13},
    }

    res = fishery_data_node(state)

    assert "fishery_data" in res
    assert res["fishery_data"]["status"] == "CALCULATED"
    assert "fishery_data_collector" in res["node_trace"]


# ── 10. test_pfz_provenance ────────────────────────────────────────────────────
@patch("tools.pfz_service.get_sst_grid")
@patch("tools.pfz_service.get_chlorophyll_grid")
def test_pfz_provenance(mock_chl, mock_sst):
    mock_sst.return_value = {
        "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
        "status": "OBSERVED",
        "observation_time": "2026-09-20T12:00:00",
        "latitudes": [14.8],
        "longitudes": [74.1],
        "values": [[27.5]],
    }
    mock_chl.return_value = {
        "dataset_id": CHLOROPHYLL_DATASET,
        "status": "MODEL_ANALYSIS",
        "observation_time": "2026-09-20T12:00:00",
        "latitudes": [14.8],
        "longitudes": [74.1],
        "values": [[0.62]],
    }

    res = calculate_pfz_candidates(14.81, 74.13)

    prov = res["provenance"]
    param_map = {p.get("parameter"): p for p in prov}

    assert "sea_surface_temperature" in param_map
    assert param_map["sea_surface_temperature"]["data_class"] == "OBSERVED"

    assert "chlorophyll_a" in param_map
    assert param_map["chlorophyll_a"]["dataset_id"] == CHLOROPHYLL_DATASET
    assert param_map["chlorophyll_a"]["data_class"] == "MODEL_ANALYSIS"

    assert "thermal_fronts" in param_map
    assert param_map["thermal_fronts"]["data_class"] == "DERIVED"


# ── 11. test_backward_compatibility_find_nearest_pfz ──────────────────────────
@patch("tools.pfz_service.calculate_pfz_candidates")
def test_backward_compatibility_find_nearest_pfz(mock_calc):
    mock_calc.return_value = {
        "status": "CALCULATED",
        "source": "Copernicus Marine & Spatial Front Analysis",
        "candidates": [{"score": 0.88}],
        "nearest_candidate": {"score": 0.88},
        "important": "Disclaimer text",
    }

    res = find_nearest_pfz(14.81, 74.13)

    assert res["status"] in ("CALCULATED", "HEURISTIC")
    assert "candidates" in res
    assert "nearest_candidate" in res
    assert "important" in res
