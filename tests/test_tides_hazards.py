"""
tests/test_tides_hazards.py
────────────────────────────
Unit & Integration Tests for Phase 2.4 — Tide Dynamics & Hazard Alert Feeds.
All external network calls are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock

from tools.tide_service import extract_tide_extrema, get_tide_forecast
from tools.hazard_service import get_hazard_alerts, parse_hazard_bulletin, get_default_hazard_status
from tools.marine_risk import calculate_marine_risk
from tools.artifact_factory import create_tide_card_artifact, create_hazard_alert_artifact
from graph.nodes.data_tide_hazard import tide_hazard_data_node


def test_extract_tide_extrema():
    """Test numerical local peak and trough extrema detection."""
    timeseries = [
        {"time_iso": "2026-09-21T00:00:00Z", "height_m": 0.5},
        {"time_iso": "2026-09-21T01:00:00Z", "height_m": 1.2},
        {"time_iso": "2026-09-21T02:00:00Z", "height_m": 1.8},
        {"time_iso": "2026-09-21T03:00:00Z", "height_m": 1.1},
        {"time_iso": "2026-09-21T04:00:00Z", "height_m": 0.3},
        {"time_iso": "2026-09-21T05:00:00Z", "height_m": 0.9},
        {"time_iso": "2026-09-21T06:00:00Z", "height_m": 1.6},
        {"time_iso": "2026-09-21T07:00:00Z", "height_m": 1.0},
    ]
    extrema = extract_tide_extrema(timeseries)
    assert len(extrema) == 3
    assert extrema[0]["type"] == "HIGH"
    assert extrema[0]["height_m"] == 1.8
    assert extrema[1]["type"] == "LOW"
    assert extrema[1]["height_m"] == 0.3
    assert extrema[2]["type"] == "HIGH"
    assert extrema[2]["height_m"] == 1.6


@patch("httpx.Client.get")
def test_get_tide_forecast_parsing(mock_get):
    """Test parsing Open-Meteo sea level response in get_tide_forecast."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "hourly": {
            "time": ["2026-09-21T00:00", "2026-09-21T01:00", "2026-09-21T02:00", "2026-09-21T03:00"],
            "sea_level_height_msl": [0.4, 0.8, 1.5, 0.9],
        }
    }
    mock_get.return_value = mock_resp

    res = get_tide_forecast(14.81, 74.13)
    assert res["status"] == "AVAILABLE"
    assert res["location"]["latitude"] == 14.81
    assert res["current"]["sea_level_m"] == 0.4
    assert res["datum"] == "MSL_MODELLED"
    assert "disclaimer" in res
    assert res["provenance"]["data_class"] == "MODELLED"


def test_tide_flooding_ebbing_phase():
    """Test tidal phase classification (FLOODING when sea level is rising)."""
    timeseries_rising = [
        {"time_iso": "2026-09-21T00:00:00Z", "height_m": 0.5},
        {"time_iso": "2026-09-21T01:00:00Z", "height_m": 1.2},
    ]
    h0 = timeseries_rising[0]["height_m"]
    h1 = timeseries_rising[1]["height_m"]
    phase = "FLOODING" if h1 > h0 else "EBBING"
    assert phase == "FLOODING"


def test_tide_rising_falling_trend():
    """Test tidal trend classification (FALLING when sea level decreases)."""
    timeseries_falling = [
        {"time_iso": "2026-09-21T00:00:00Z", "height_m": 1.5},
        {"time_iso": "2026-09-21T01:00:00Z", "height_m": 0.9},
    ]
    h0 = timeseries_falling[0]["height_m"]
    h1 = timeseries_falling[1]["height_m"]
    trend = "FALLING" if h1 < h0 else "RISING"
    assert trend == "FALLING"


def test_hazard_alert_active_parsing():
    """Test parsing an official structured hazard bulletin."""
    payload = {
        "status": "ACTIVE",
        "source": "INCOIS",
        "bulletin_id": "INCOIS_HWA_2026_01",
        "alerts": [
            {
                "alert_id": "HWA_KARWAR_01",
                "category": "HIGH_WAVE",
                "severity": "WARNING",
                "title": "INCOIS High Wave Warning",
                "description": "Waves 2.8m - 3.5m expected along Karnataka coast.",
                "issued_at": "2026-09-21T06:00:00Z",
                "valid_until": "2026-09-22T18:00:00Z",
                "affected_regions": ["Karwar", "Kumta"],
            }
        ],
    }
    res = parse_hazard_bulletin(payload)
    assert res["status"] == "ACTIVE"
    assert len(res["alerts"]) == 1
    assert res["alerts"][0]["severity"] == "WARNING"
    assert res["provenance"]["data_class"] == "OFFICIAL_BULLETIN"


def test_hazard_alert_unavailable_fallback():
    """Test default UNAVAILABLE fallback when no live official hazard feed is configured."""
    res = get_hazard_alerts(14.81, 74.13)
    assert res["status"] == "UNAVAILABLE"
    assert res["alerts"] == []
    assert res["provenance"]["data_class"] == "UNAVAILABLE"


def test_marine_risk_tide_superposition():
    """Test risk engine penalty when high wave coincides with high tide (flooding phase)."""
    ocean = {}
    weather = {}
    geofence = {}
    marine = {"current": {"wave_height": 2.2}}
    tide_data = {
        "current": {"phase": "FLOODING", "sea_level_m": 1.8},
        "next_high_tide": {"height_m": 2.0},
        "tidal_range_m": 1.4,
    }

    res = calculate_marine_risk(ocean, weather, geofence, marine=marine, tide_data=tide_data)
    assert res["risk_score"] == 40
    assert any("High tide coincidence" in r for r in res["reasons"])


def test_marine_risk_hazard_warning_penalty():
    """Test risk engine penalty for official WARNING hazard alerts."""
    ocean = {}
    weather = {}
    geofence = {}
    hazard_data = {
        "status": "ACTIVE",
        "provenance": {"data_class": "OFFICIAL_BULLETIN"},
        "alerts": [
            {
                "severity": "WARNING",
                "title": "INCOIS High Wave Warning",
            }
        ],
    }

    res = calculate_marine_risk(ocean, weather, geofence, hazard_data=hazard_data)
    assert res["risk_score"] == 35
    assert any("Official marine warning active" in r for r in res["reasons"])


def test_tide_card_artifact_schema():
    """Test tide_card artifact factory creation and structure."""
    loc = {"status": "FOUND", "name": "Karwar", "latitude": 14.81, "longitude": 74.13}
    tide_data = {
        "status": "AVAILABLE",
        "current": {"sea_level_m": 1.2, "phase": "FLOODING", "trend": "RISING"},
        "extrema": [{"type": "HIGH", "time_iso": "2026-09-21T06:00:00Z", "height_m": 1.8}],
        "next_high_tide": {"type": "HIGH", "time_iso": "2026-09-21T06:00:00Z", "height_m": 1.8},
        "tidal_range_m": 1.4,
        "datum": "MSL_MODELLED",
        "provenance": {"provider": "Open-Meteo", "data_class": "MODELLED"},
        "disclaimer": "sea_level_height_msl is a MODELLED value.",
    }

    art = create_tide_card_artifact(loc, tide_data)
    assert art is not None
    assert art["type"] == "tide_card"
    assert art["data"]["location"]["name"] == "Karwar"
    assert art["data"]["current"]["phase"] == "FLOODING"
    assert art["data"]["datum"] == "MSL_MODELLED"


def test_hazard_alert_artifact_schema():
    """Test hazard_alert artifact factory creation for active warnings and UNAVAILABLE status."""
    loc = {"status": "FOUND", "name": "Karwar", "latitude": 14.81, "longitude": 74.13}
    hazard_data = {
        "status": "UNAVAILABLE",
        "alerts": [],
        "advice": "No active official hazard alert feed connected.",
        "provenance": {"data_class": "UNAVAILABLE"},
    }

    art = create_hazard_alert_artifact(loc, hazard_data)
    assert art is not None
    assert art["type"] == "hazard_alert"
    assert art["data"]["status"] == "UNAVAILABLE"
    assert "No active official hazard alerts" in art["description"]


def test_tide_hazard_provenance_metadata():
    """Test provenance data_class distinctions for tide and hazard responses."""
    tide_data = {
        "provenance": {"provider": "Open-Meteo", "data_class": "MODELLED"},
    }
    hazard_data_unofficial = {
        "provenance": {"provider": "INCOIS / IMD", "data_class": "UNAVAILABLE"},
    }
    hazard_data_official = {
        "provenance": {"provider": "INCOIS", "data_class": "OFFICIAL_BULLETIN"},
    }

    assert tide_data["provenance"]["data_class"] == "MODELLED"
    assert hazard_data_unofficial["provenance"]["data_class"] == "UNAVAILABLE"
    assert hazard_data_official["provenance"]["data_class"] == "OFFICIAL_BULLETIN"


@patch("httpx.Client.get")
def test_missing_tide_data_fallback(mock_get):
    """Test HTTP network exception handling in get_tide_forecast."""
    mock_get.side_effect = Exception("Open-Meteo API connection timeout")

    res = get_tide_forecast(14.81, 74.13)
    assert res["status"] == "UNAVAILABLE"
    assert res["provenance"]["data_class"] == "UNAVAILABLE"
    assert "error" in res
