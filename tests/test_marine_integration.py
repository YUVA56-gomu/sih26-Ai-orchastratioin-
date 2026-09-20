"""
tests/test_marine_integration.py
──────────────────────────────────
Tests for Open-Meteo Marine API integration.

All tests use mocking — no live network calls are made.

Import strategy: node modules are imported directly (bypassing
graph/__init__.py which pulls in langgraph at module level) so
tests pass without langgraph installed in the test environment.

Test coverage:
  Test 1  — Successful marine API response
  Test 2  — API / network failure
  Test 3  — Missing optional variable in response
  Test 4  — Invalid / missing location in graph node
  Test 5  — LangGraph state receives marine_data
  Test 6  — Existing graph behavior unaffected (backward compat)
  Test 7  — Existing data_weather and data_ocean nodes unchanged
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Stub langgraph so graph/__init__.py doesn't crash on import ───────────────
def _stub_langgraph():
    """Insert minimal stubs so node imports work without full stack installed."""
    def _mod(name):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)
        return sys.modules[name]

    # langgraph
    try:
        import langgraph.graph
        import langgraph.checkpoint.memory
    except ImportError:
        lg       = _mod("langgraph")
        lg_graph = _mod("langgraph.graph")
        lg_graph.StateGraph = MagicMock
        lg_graph.START = "__start__"
        lg_graph.END   = "__end__"
        _mod("langgraph.checkpoint")
        lg_mem = _mod("langgraph.checkpoint.memory")
        lg_mem.MemorySaver = MagicMock

    # langchain_core
    try:
        import langchain_core.messages
    except ImportError:
        _mod("langchain_core")
        _mod("langchain_core.messages")
        lc_msgs = sys.modules["langchain_core.messages"]
        lc_msgs.HumanMessage  = MagicMock
        lc_msgs.SystemMessage = MagicMock


    # langchain_google_genai / langchain_groq / langchain_ollama
    for mod in (
        "langchain_google_genai",
        "langchain_groq",
        "langchain_ollama",
    ):
        _mod(mod)

    # copernicusmarine + heavy scientific deps not installed in test env
    _mod("copernicusmarine")
    _mod("numpy")
    # stub numpy with a real-enough shim so copernicus_service.py parses
    import numpy as _np_real  # noqa: F401  — may already be present
    # if numpy IS installed, the real one is already in sys.modules; skip stub

_stub_langgraph()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — synthetic API payloads
# ─────────────────────────────────────────────────────────────────────────────

def _make_api_response(override: dict | None = None) -> dict:
    """Return a minimal but structurally complete Open-Meteo Marine response."""
    base = {
        "latitude": 13.08,
        "longitude": 80.27,
        "generationtime_ms": 1.2,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "current_units": {
            "time": "iso8601",
            "wave_height": "m",
            "wave_direction": "°",
            "wave_period": "s",
            "wave_peak_period": "s",
            "wind_wave_height": "m",
            "wind_wave_direction": "°",
            "wind_wave_period": "s",
            "wind_wave_peak_period": "s",
            "swell_wave_height": "m",
            "swell_wave_direction": "°",
            "swell_wave_period": "s",
            "swell_wave_peak_period": "s",
            "ocean_current_velocity": "km/h",
            "ocean_current_direction": "°",
            "sea_surface_temperature": "°C",
            "sea_level_height_msl": "m",
        },
        "current": {
            "time": "2026-09-15T06:00",
            "wave_height": 1.2,
            "wave_direction": 230.0,
            "wave_period": 8.5,
            "wave_peak_period": 9.1,
            "wind_wave_height": 0.8,
            "wind_wave_direction": 210.0,
            "wind_wave_period": 5.2,
            "wind_wave_peak_period": 5.8,
            "swell_wave_height": 0.9,
            "swell_wave_direction": 245.0,
            "swell_wave_period": 11.3,
            "swell_wave_peak_period": 12.0,
            "ocean_current_velocity": 1.8,
            "ocean_current_direction": 90.0,
            "sea_surface_temperature": 28.4,
            "sea_level_height_msl": 0.12,
        },
        "hourly_units": {
            "time": "iso8601",
            "wave_height": "m",
        },
        "hourly": {
            "time": ["2026-09-15T00:00", "2026-09-15T01:00"],
            "wave_height": [1.1, 1.2],
        },
    }
    if override:
        base.update(override)
    return base


def _make_mock_httpx_response(payload: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()  # no-op for 200
    return mock_resp


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Successful marine API response
# ─────────────────────────────────────────────────────────────────────────────

def test_successful_marine_response():
    """get_marine_conditions returns OK status and all current fields."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(_make_api_response())

        result = get_marine_conditions(13.08, 80.27, forecast_days=3)

    assert result["status"] in ("OK", "PARTIAL"), f"Unexpected status: {result['status']}"
    assert result["source"] == "Open-Meteo Marine"
    assert result["data_type"] == "MODELLED"
    assert result["latitude"] == 13.08
    assert result["longitude"] == 80.27
    assert isinstance(result["current"], dict)
    assert result["current"]["wave_height"] == 1.2
    assert result["current"]["sea_surface_temperature"] == 28.4
    assert result["current"]["sea_level_height_msl"] == 0.12
    assert result["current"]["ocean_current_velocity"] == 1.8
    assert "sea_level_note" in result
    assert "MODELLED" in result["sea_level_note"]
    assert isinstance(result["warnings"], list)
    assert result["forecast_days"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — API / network failure
# ─────────────────────────────────────────────────────────────────────────────

def test_network_failure_returns_error_status():
    """get_marine_conditions returns ERROR status on network exception."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = get_marine_conditions(13.08, 80.27)

    assert result["status"] == "ERROR"
    assert result["source"] == "Open-Meteo Marine"
    assert result["data_type"] == "MODELLED"
    assert "Connection refused" in result["error"]
    assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Missing optional variable in API response
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_optional_variable_returns_none_not_error():
    """
    If a variable is absent from the API response, its value is None
    and a warning is recorded — the call does not fail.
    """
    from tools.marine_service import get_marine_conditions

    payload = _make_api_response()
    del payload["current"]["sea_level_height_msl"]
    del payload["current"]["ocean_current_velocity"]

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(payload)

        result = get_marine_conditions(13.08, 80.27)

    assert result["status"] in ("OK", "PARTIAL")
    assert result["current"]["sea_level_height_msl"] is None
    assert result["current"]["ocean_current_velocity"] is None
    warning_text = " ".join(result["warnings"])
    assert "sea_level_height_msl" in warning_text
    assert "ocean_current_velocity" in warning_text


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Invalid / missing location in graph node
# ─────────────────────────────────────────────────────────────────────────────

def test_node_blocked_on_missing_location():
    """marine_data_node returns BLOCKED when location is not FOUND."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "NOT_PROVIDED"},
        "plan": {"forecast_days": 3},
        "recheck_domains": [],
    }

    result = marine_data_node(state)

    assert result["marine_data"]["status"] == "BLOCKED"
    assert result["marine_data"]["source"] == "Open-Meteo Marine"
    assert result["marine_data"]["data_type"] == "MODELLED"
    assert "marine_data_collector" in result["node_trace"]


def test_node_blocked_on_error_location():
    """marine_data_node returns BLOCKED when location resolution failed."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "ERROR", "error": "geocoding timeout"},
        "plan": {},
        "recheck_domains": [],
    }

    result = marine_data_node(state)
    assert result["marine_data"]["status"] == "BLOCKED"


def test_node_skipped_on_empty_location():
    """marine_data_node returns BLOCKED when location key is absent."""
    from graph.nodes.data_marine import marine_data_node

    result = marine_data_node({})
    assert result["marine_data"]["status"] == "BLOCKED"


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — LangGraph state receives marine_data
# ─────────────────────────────────────────────────────────────────────────────

def test_node_writes_marine_data_to_state():
    """marine_data_node writes result into state['marine_data']."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {
            "status": "FOUND",
            "latitude": 13.08,
            "longitude": 80.27,
        },
        "plan": {"forecast_days": 1},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_marine.get_marine_conditions") as mock_fn:
        mock_fn.return_value = {
            "status": "OK",
            "source": "Open-Meteo Marine",
            "data_type": "MODELLED",
            "current": {"wave_height": 1.1},
            "hourly": {},
            "warnings": [],
        }
        result = marine_data_node(state)

    assert "marine_data" in result
    assert result["marine_data"]["status"] == "OK"
    assert result["marine_data"]["data_type"] == "MODELLED"
    assert result["marine_data"]["current"]["wave_height"] == 1.1
    assert "marine_data_collector" in result["node_trace"]
    assert "weather_data" not in result
    assert "ocean_data" not in result


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Existing graph behavior unaffected (backward compat)
# ─────────────────────────────────────────────────────────────────────────────

def test_marine_risk_existing_behavior_unchanged():
    """
    calculate_marine_risk called WITHOUT marine arg works identically
    to pre-integration behavior.
    """
    from tools.marine_risk import calculate_marine_risk

    ocean = {
        "observations": {
            "waves": {"significant_wave_height_m": 2.0},
            "currents": {},
        }
    }
    weather = {
        "current": {
            "wind_speed_10m": 35.0,
            "weather_code": 61,
            "precipitation": 2.0,
        }
    }
    geofence = {"inside_restricted_zone": False}

    result = calculate_marine_risk(ocean, weather, geofence)

    assert result["risk_level"] in ("LOW", "MODERATE", "HIGH", "VERY HIGH")
    assert isinstance(result["risk_score"], (int, float))
    assert result["decision_support_only"] is True
    # marine fields present but None when not supplied
    assert "ocean_current_velocity_kmh" in result["evaluated_parameters"]
    assert result["evaluated_parameters"]["ocean_current_velocity_kmh"] is None


def test_marine_risk_with_marine_fallback():
    """
    When Copernicus wave data is absent, marine wave_height is used as fallback.
    wave_height=3.0 → score +=40. No wind/weather/geofence → total=40 → MODERATE.
    """
    from tools.marine_risk import calculate_marine_risk

    ocean    = {"observations": {}}   # no Copernicus wave data
    weather  = {"current": {"wind_speed_10m": 10.0, "weather_code": 1, "precipitation": 0.0}}
    geofence = {"inside_restricted_zone": False}
    marine   = {
        "status": "OK",
        "data_type": "MODELLED",
        "current": {
            "wave_height": 3.0,
            "ocean_current_velocity": 5.2,
            "sea_surface_temperature": 28.5,
        }
    }

    result = calculate_marine_risk(ocean, weather, geofence, marine)

    # wave_height=3.0 → +40; wind=10 → +0; total=40 → MODERATE (25≤score<55)
    assert result["risk_score"] >= 40
    assert result["risk_level"] in ("MODERATE", "HIGH", "VERY HIGH")
    assert result["evaluated_parameters"]["ocean_current_velocity_kmh"] == 5.2
    assert result["evaluated_parameters"]["marine_sst_c"] == 28.5


def test_marine_risk_geofence_still_dominant():
    """Geofence hit still adds 50 points regardless of marine data."""
    from tools.marine_risk import calculate_marine_risk

    ocean    = {"observations": {}}
    weather  = {"current": {}}
    geofence = {"inside_restricted_zone": True}
    marine   = {"status": "OK", "current": {"wave_height": 0.1}}

    result = calculate_marine_risk(ocean, weather, geofence, marine)

    assert result["risk_score"] >= 50
    assert any("restricted" in r.lower() for r in result["reasons"])


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Existing data_weather and data_ocean nodes unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_weather_node_unaffected():
    """data_weather node still writes weather_data and does not touch marine_data."""
    from graph.nodes.data_weather import weather_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"domains_needed": ["weather"], "forecast_days": 1},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_weather.get_weather_conditions") as mock_fn:
        mock_fn.return_value = {
            "status": "OK",
            "source": "Open-Meteo Weather",
            "current": {"wind_speed_10m": 12.0},
            "hourly": {},
            "data_status": "FORECAST_AVAILABLE",
        }
        result = weather_data_node(state)

    assert "weather_data" in result
    assert result["weather_data"]["status"] == "OK"
    assert "marine_data" not in result
    assert "ocean_data"  not in result


def test_ocean_node_unaffected():
    """data_ocean node still writes ocean_data and does not touch marine_data."""
    from graph.nodes.data_ocean import ocean_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"domains_needed": ["ocean"]},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_ocean.get_copernicus_marine_snapshot") as mock_fn:
        mock_fn.return_value = {
            "status": "COMPLETE",
            "source": "Copernicus Marine",
            "observations": {
                "waves": {"significant_wave_height_m": 1.5}
            },
        }
        result = ocean_data_node(state)

    assert "ocean_data" in result
    assert result["ocean_data"]["status"] == "COMPLETE"
    assert "marine_data"  not in result
    assert "weather_data" not in result


def test_recheck_skip_marine_node():
    """marine_data_node returns empty update when marine not in recheck_domains."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {},
        "recheck_domains": ["ocean", "weather"],   # marine NOT listed
    }

    result = marine_data_node(state)

    assert "marine_data" not in result
    assert any("recheck_skipped" in t for t in result.get("node_trace", []))


def test_recheck_fetches_marine_when_flagged():
    """marine_data_node re-fetches when 'marine' is in recheck_domains."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"forecast_days": 1},
        "recheck_domains": ["marine"],
    }

    with patch("graph.nodes.data_marine.get_marine_conditions") as mock_fn:
        mock_fn.return_value = {"status": "OK", "data_type": "MODELLED", "current": {}}
        result = marine_data_node(state)

    assert "marine_data" in result
    mock_fn.assert_called_once()


def test_state_schema_has_marine_data_field():
    """SamudraState TypedDict includes the marine_data field."""
    from state.schema import SamudraState
    annotations = SamudraState.__annotations__
    assert "marine_data" in annotations


def test_sea_level_note_present_in_response():
    """sea_level_note is always present and contains the word MODELLED."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(_make_api_response())
        result = get_marine_conditions(0.0, 0.0)

    assert "sea_level_note" in result
    note = result["sea_level_note"]
    assert "MODELLED" in note
    assert "NOT" in note.upper()



# ─────────────────────────────────────────────────────────────────────────────
# Helpers — synthetic API payloads
# ─────────────────────────────────────────────────────────────────────────────

def _make_api_response(override: dict | None = None) -> dict:
    """Return a minimal but structurally complete Open-Meteo Marine response."""
    base = {
        "latitude": 13.08,
        "longitude": 80.27,
        "generationtime_ms": 1.2,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "current_units": {
            "time": "iso8601",
            "wave_height": "m",
            "wave_direction": "°",
            "wave_period": "s",
            "wave_peak_period": "s",
            "wind_wave_height": "m",
            "wind_wave_direction": "°",
            "wind_wave_period": "s",
            "wind_wave_peak_period": "s",
            "swell_wave_height": "m",
            "swell_wave_direction": "°",
            "swell_wave_period": "s",
            "swell_wave_peak_period": "s",
            "ocean_current_velocity": "km/h",
            "ocean_current_direction": "°",
            "sea_surface_temperature": "°C",
            "sea_level_height_msl": "m",
        },
        "current": {
            "time": "2026-09-15T06:00",
            "wave_height": 1.2,
            "wave_direction": 230.0,
            "wave_period": 8.5,
            "wave_peak_period": 9.1,
            "wind_wave_height": 0.8,
            "wind_wave_direction": 210.0,
            "wind_wave_period": 5.2,
            "wind_wave_peak_period": 5.8,
            "swell_wave_height": 0.9,
            "swell_wave_direction": 245.0,
            "swell_wave_period": 11.3,
            "swell_wave_peak_period": 12.0,
            "ocean_current_velocity": 1.8,
            "ocean_current_direction": 90.0,
            "sea_surface_temperature": 28.4,
            "sea_level_height_msl": 0.12,
        },
        "hourly_units": {
            "time": "iso8601",
            "wave_height": "m",
        },
        "hourly": {
            "time": ["2026-09-15T00:00", "2026-09-15T01:00"],
            "wave_height": [1.1, 1.2],
        },
    }
    if override:
        base.update(override)
    return base


def _make_mock_httpx_response(payload: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()  # no-op for 200
    return mock_resp


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Successful marine API response
# ─────────────────────────────────────────────────────────────────────────────

def test_successful_marine_response():
    """get_marine_conditions returns OK status and all current fields."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(_make_api_response())

        result = get_marine_conditions(13.08, 80.27, forecast_days=3)

    assert result["status"] in ("OK", "PARTIAL"), f"Unexpected status: {result['status']}"
    assert result["source"] == "Open-Meteo Marine"
    assert result["data_type"] == "MODELLED"
    assert result["latitude"] == 13.08
    assert result["longitude"] == 80.27
    assert isinstance(result["current"], dict)
    assert result["current"]["wave_height"] == 1.2
    assert result["current"]["sea_surface_temperature"] == 28.4
    assert result["current"]["sea_level_height_msl"] == 0.12
    assert result["current"]["ocean_current_velocity"] == 1.8
    assert "sea_level_note" in result
    assert "MODELLED" in result["sea_level_note"]
    assert isinstance(result["warnings"], list)
    assert result["forecast_days"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — API / network failure
# ─────────────────────────────────────────────────────────────────────────────

def test_network_failure_returns_error_status():
    """get_marine_conditions returns ERROR status on network exception."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = get_marine_conditions(13.08, 80.27)

    assert result["status"] == "ERROR"
    assert result["source"] == "Open-Meteo Marine"
    assert result["data_type"] == "MODELLED"
    assert "Connection refused" in result["error"]
    # Must not raise — always returns structured dict
    assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Missing optional variable in API response
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_optional_variable_returns_none_not_error():
    """
    If a variable is absent from the API response, its value is None
    and a warning is recorded — the call does not fail.
    """
    from tools.marine_service import get_marine_conditions

    payload = _make_api_response()
    # Remove sea_level_height_msl and ocean_current_velocity from current
    del payload["current"]["sea_level_height_msl"]
    del payload["current"]["ocean_current_velocity"]

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(payload)

        result = get_marine_conditions(13.08, 80.27)

    assert result["status"] in ("OK", "PARTIAL")
    assert result["current"]["sea_level_height_msl"] is None
    assert result["current"]["ocean_current_velocity"] is None
    # Warnings must mention the missing variables
    warning_text = " ".join(result["warnings"])
    assert "sea_level_height_msl" in warning_text
    assert "ocean_current_velocity" in warning_text


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Invalid / missing location in graph node
# ─────────────────────────────────────────────────────────────────────────────

def test_node_blocked_on_missing_location():
    """marine_data_node returns BLOCKED when location is not FOUND."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "NOT_PROVIDED"},
        "plan": {"forecast_days": 3},
        "recheck_domains": [],
    }

    result = marine_data_node(state)

    assert result["marine_data"]["status"] == "BLOCKED"
    assert result["marine_data"]["source"] == "Open-Meteo Marine"
    assert result["marine_data"]["data_type"] == "MODELLED"
    assert "marine_data_collector" in result["node_trace"]


def test_node_blocked_on_error_location():
    """marine_data_node returns BLOCKED when location resolution failed."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "ERROR", "error": "geocoding timeout"},
        "plan": {},
        "recheck_domains": [],
    }

    result = marine_data_node(state)

    assert result["marine_data"]["status"] == "BLOCKED"


def test_node_skipped_on_empty_location():
    """marine_data_node returns BLOCKED when location key is absent."""
    from graph.nodes.data_marine import marine_data_node

    result = marine_data_node({})

    assert result["marine_data"]["status"] == "BLOCKED"


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — LangGraph state receives marine_data
# ─────────────────────────────────────────────────────────────────────────────

def test_node_writes_marine_data_to_state():
    """marine_data_node writes result into state['marine_data']."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {
            "status": "FOUND",
            "latitude": 13.08,
            "longitude": 80.27,
        },
        "plan": {"forecast_days": 1},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_marine.get_marine_conditions") as mock_fn:
        mock_fn.return_value = {
            "status": "OK",
            "source": "Open-Meteo Marine",
            "data_type": "MODELLED",
            "current": {"wave_height": 1.1},
            "hourly": {},
            "warnings": [],
        }
        result = marine_data_node(state)

    assert "marine_data" in result
    assert result["marine_data"]["status"] == "OK"
    assert result["marine_data"]["data_type"] == "MODELLED"
    assert result["marine_data"]["current"]["wave_height"] == 1.1
    assert "marine_data_collector" in result["node_trace"]
    # Must NOT accidentally write other state keys
    assert "weather_data" not in result
    assert "ocean_data" not in result


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Existing graph behavior unaffected (backward compat)
# ─────────────────────────────────────────────────────────────────────────────

def test_marine_risk_existing_behavior_unchanged():
    """
    calculate_marine_risk called WITHOUT marine arg works identically
    to pre-integration behavior.
    """
    from tools.marine_risk import calculate_marine_risk

    ocean = {
        "observations": {
            "waves": {"significant_wave_height_m": 2.0},
            "currents": {},
        }
    }
    weather = {
        "current": {
            "wind_speed_10m": 35.0,
            "weather_code": 61,
            "precipitation": 2.0,
        }
    }
    geofence = {"inside_restricted_zone": False}

    # Old call signature — no marine arg
    result = calculate_marine_risk(ocean, weather, geofence)

    assert result["risk_level"] in ("LOW", "MODERATE", "HIGH", "VERY HIGH")
    assert isinstance(result["risk_score"], (int, float))
    assert result["decision_support_only"] is True
    # marine fields appear but are None (not an error)
    assert "ocean_current_velocity_kmh" in result["evaluated_parameters"]
    assert result["evaluated_parameters"]["ocean_current_velocity_kmh"] is None


def test_marine_risk_with_marine_fallback():
    """
    When Copernicus wave data is absent, marine wave_height is used as fallback.
    """
    from tools.marine_risk import calculate_marine_risk

    ocean   = {"observations": {}}          # no wave data from Copernicus
    weather = {"current": {"wind_speed_10m": 10.0, "weather_code": 1, "precipitation": 0.0}}
    geofence = {"inside_restricted_zone": False}
    marine  = {
        "status": "OK",
        "data_type": "MODELLED",
        "current": {
            "wave_height": 3.0,             # should trigger VERY HIGH wave score
            "ocean_current_velocity": 5.2,
            "sea_surface_temperature": 28.5,
        }
    }

    result = calculate_marine_risk(ocean, weather, geofence, marine)

    # wave_height=3.0 → score += 40; wind=10 → 0; total=40 → MODERATE (25≤score<55)
    assert result["risk_score"] >= 40
    assert result["risk_level"] in ("MODERATE", "HIGH", "VERY HIGH")
    assert result["evaluated_parameters"]["ocean_current_velocity_kmh"] == 5.2
    assert result["evaluated_parameters"]["marine_sst_c"] == 28.5


def test_marine_risk_geofence_still_dominant():
    """Geofence hit still adds 50 points regardless of marine data."""
    from tools.marine_risk import calculate_marine_risk

    ocean    = {"observations": {}}
    weather  = {"current": {}}
    geofence = {"inside_restricted_zone": True}
    marine   = {"status": "OK", "current": {"wave_height": 0.1}}

    result = calculate_marine_risk(ocean, weather, geofence, marine)

    assert result["risk_score"] >= 50
    assert any("restricted" in r.lower() for r in result["reasons"])


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Existing data_weather and data_ocean nodes unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_weather_node_unaffected():
    """data_weather node still writes weather_data and does not touch marine_data."""
    from graph.nodes.data_weather import weather_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"domains_needed": ["weather"], "forecast_days": 1},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_weather.get_weather_conditions") as mock_fn:
        mock_fn.return_value = {
            "status": "OK",
            "source": "Open-Meteo Weather",
            "current": {"wind_speed_10m": 12.0},
            "hourly": {},
            "data_status": "FORECAST_AVAILABLE",
        }
        result = weather_data_node(state)

    assert "weather_data" in result
    assert result["weather_data"]["status"] == "OK"
    assert "marine_data" not in result       # must NOT be written by weather node
    assert "ocean_data"  not in result


def test_ocean_node_unaffected():
    """data_ocean node still writes ocean_data and does not touch marine_data."""
    from graph.nodes.data_ocean import ocean_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"domains_needed": ["ocean"]},
        "recheck_domains": [],
    }

    with patch("graph.nodes.data_ocean.get_copernicus_marine_snapshot") as mock_fn:
        mock_fn.return_value = {
            "status": "COMPLETE",
            "source": "Copernicus Marine",
            "observations": {
                "waves": {"significant_wave_height_m": 1.5}
            },
        }
        result = ocean_data_node(state)

    assert "ocean_data" in result
    assert result["ocean_data"]["status"] == "COMPLETE"
    assert "marine_data"  not in result      # must NOT be written by ocean node
    assert "weather_data" not in result


def test_recheck_skip_marine_node():
    """marine_data_node returns empty update when marine not in recheck_domains."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {},
        "recheck_domains": ["ocean", "weather"],   # marine NOT listed
    }

    result = marine_data_node(state)

    # Should return only node_trace — no marine_data key
    assert "marine_data" not in result
    assert any("recheck_skipped" in t for t in result.get("node_trace", []))


def test_recheck_fetches_marine_when_flagged():
    """marine_data_node re-fetches when 'marine' is in recheck_domains."""
    from graph.nodes.data_marine import marine_data_node

    state = {
        "location": {"status": "FOUND", "latitude": 13.08, "longitude": 80.27},
        "plan": {"forecast_days": 1},
        "recheck_domains": ["marine"],             # marine IS listed
    }

    with patch("graph.nodes.data_marine.get_marine_conditions") as mock_fn:
        mock_fn.return_value = {"status": "OK", "data_type": "MODELLED", "current": {}}
        result = marine_data_node(state)

    assert "marine_data" in result
    mock_fn.assert_called_once()


def test_state_schema_has_marine_data_field():
    """SamudraState TypedDict includes the marine_data field."""
    from state.schema import SamudraState
    annotations = SamudraState.__annotations__
    assert "marine_data" in annotations


def test_sea_level_note_present_in_response():
    """sea_level_note is always present and contains the word MODELLED."""
    from tools.marine_service import get_marine_conditions

    with patch("tools.marine_service.httpx.get") as mock_get:
        mock_get.return_value = _make_mock_httpx_response(_make_api_response())
        result = get_marine_conditions(0.0, 0.0)

    assert "sea_level_note" in result
    note = result["sea_level_note"]
    assert "MODELLED" in note
    assert "NOT" in note.upper()  # must contain a disclaimer
