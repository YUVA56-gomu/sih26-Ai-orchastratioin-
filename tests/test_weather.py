"""
tests/test_weather.py
──────────────────────
Dedicated test suite for SAMUDRA AI Phase 2.1 — Weather Service Integration.

Tests:
1. Weather response structure (current, hourly, daily, units, provenance)
2. Existing weather variables availability
3. Daily forecast fields population
4. Provenance metadata contents (source, provider, data_class, retrieved_at)
5. Weather artifact payload structure
6. Hourly artifact data bounded window
7. Weather API error handling on failure
8. Marine risk response to elevated wind gusts
9. Weather data node integration
"""

import os
# Ensure mock LLM provider is active for fast deterministic testing
os.environ["LLM_PROVIDER"] = "mock"

import pytest
from unittest.mock import patch, MagicMock

from tools.weather_service import get_weather_conditions
from tools.artifact_factory import create_weather_card_artifact
from tools.marine_risk import calculate_marine_risk
from graph.nodes.data_weather import weather_data_node


@pytest.fixture
def mock_open_meteo_response():
    """Mock JSON response from Open-Meteo Weather API with full parameters."""
    return {
        "latitude": 14.81,
        "longitude": 74.13,
        "current_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "apparent_temperature": "°C",
            "precipitation": "mm",
            "weather_code": "wmo code",
            "surface_pressure": "hPa",
            "pressure_msl": "hPa",
            "wind_speed_10m": "km/h",
            "wind_direction_10m": "°",
            "wind_gusts_10m": "km/h",
        },
        "current": {
            "time": "2026-09-20T12:00",
            "temperature_2m": 28.5,
            "relative_humidity_2m": 78,
            "apparent_temperature": 32.1,
            "precipitation": 0.0,
            "weather_code": 1,
            "surface_pressure": 1011.2,
            "pressure_msl": 1012.0,
            "wind_speed_10m": 18.5,
            "wind_direction_10m": 240,
            "wind_gusts_10m": 42.0,
        },
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "wind_speed_10m": "km/h",
            "wind_gusts_10m": "km/h",
        },
        "hourly": {
            "time": [f"2026-09-20T{i:02d}:00" for i in range(48)],
            "temperature_2m": [28.0 + (i % 3) for i in range(48)],
            "relative_humidity_2m": [75 + (i % 5) for i in range(48)],
            "dew_point_2m": [23.5 for _ in range(48)],
            "precipitation_probability": [10 for _ in range(48)],
            "precipitation": [0.0 for _ in range(48)],
            "weather_code": [1 for _ in range(48)],
            "pressure_msl": [1012.0 for _ in range(48)],
            "surface_pressure": [1011.0 for _ in range(48)],
            "cloud_cover": [20 for _ in range(48)],
            "visibility": [10000.0 for _ in range(48)],
            "wind_speed_10m": [18.0 for _ in range(48)],
            "wind_direction_10m": [240 for _ in range(48)],
            "wind_gusts_10m": [42.0 for _ in range(48)],
            "uv_index": [5.5 for _ in range(48)],
        },
        "daily_units": {
            "time": "iso8601",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "wind_speed_10m_max": "km/h",
            "wind_gusts_10m_max": "km/h",
        },
        "daily": {
            "time": ["2026-09-20", "2026-09-21", "2026-09-22"],
            "weather_code": [1, 2, 3],
            "temperature_2m_max": [30.5, 31.0, 29.8],
            "temperature_2m_min": [24.0, 24.5, 23.8],
            "apparent_temperature_max": [34.0, 35.1, 33.2],
            "apparent_temperature_min": [26.0, 26.5, 25.8],
            "sunrise": ["2026-09-20T06:12", "2026-09-21T06:12", "2026-09-22T06:13"],
            "sunset": ["2026-09-20T18:25", "2026-09-21T18:24", "2026-09-22T18:23"],
            "precipitation_sum": [0.0, 2.5, 5.0],
            "rain_sum": [0.0, 2.5, 5.0],
            "precipitation_hours": [0, 2, 4],
            "precipitation_probability_max": [20, 45, 60],
            "wind_speed_10m_max": [22.0, 25.0, 28.0],
            "wind_gusts_10m_max": [45.0, 52.0, 58.0],
            "wind_direction_10m_dominant": [240, 250, 230],
            "uv_index_max": [8.0, 8.5, 7.5],
        },
    }


def test_weather_response_structure_and_provenance(mock_open_meteo_response):
    """Test 1, 2, 3, 4: Enhanced get_weather_conditions returns current, hourly, daily, units, provenance."""
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_open_meteo_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        res = get_weather_conditions(14.81, 74.13, forecast_days=3)

        assert res["status"] == "OK"
        assert "current" in res
        assert "hourly" in res
        assert "daily" in res
        assert "current_units" in res
        assert "hourly_units" in res
        assert "daily_units" in res
        assert "provenance" in res

        # 2. Existing weather variables
        curr = res["current"]
        assert curr["temperature_2m"] == 28.5
        assert curr["wind_speed_10m"] == 18.5
        assert curr["precipitation"] == 0.0
        assert curr["weather_code"] == 1
        assert curr["wind_gusts_10m"] == 42.0

        # 3. Daily forecast fields
        daily = res["daily"]
        assert "temperature_2m_max" in daily
        assert daily["temperature_2m_max"][0] == 30.5
        assert daily["wind_gusts_10m_max"][0] == 45.0
        assert "sunrise" in daily
        assert "sunset" in daily

        # 4. Provenance contents
        prov = res["provenance"]
        assert prov["source"] == "Open-Meteo Weather API"
        assert prov["provider"] == "Open-Meteo"
        assert prov["data_class"] == "FORECAST"
        assert "retrieved_at" in prov


def test_weather_artifact_structure_and_bounding(mock_open_meteo_response):
    """Test 5 & 6: create_weather_card_artifact builds enriched artifact with bounded hourly data."""
    weather_data = {
        "status": "OK",
        "current": mock_open_meteo_response["current"],
        "hourly": mock_open_meteo_response["hourly"],
        "daily": mock_open_meteo_response["daily"],
        "current_units": mock_open_meteo_response["current_units"],
        "hourly_units": mock_open_meteo_response["hourly_units"],
        "daily_units": mock_open_meteo_response["daily_units"],
        "provenance": {
            "source": "Open-Meteo Weather API",
            "provider": "Open-Meteo",
            "data_class": "FORECAST",
            "retrieved_at": "2026-09-20T12:00:00+00:00",
        },
    }

    location = {"status": "FOUND", "name": "Karwar", "latitude": 14.81, "longitude": 74.13}

    art = create_weather_card_artifact(location, weather_data)

    assert art is not None
    assert art["type"] == "weather_card"
    assert "data" in art

    data = art["data"]
    assert "location" in data
    assert "current" in data
    assert "daily" in data
    assert "hourly" in data
    assert "units" in data
    assert "provenance" in data

    # Test 6: Bounded hourly data (max 24 items)
    hourly_bounded = data["hourly"]
    assert "temperature_2m" in hourly_bounded
    assert len(hourly_bounded["temperature_2m"]) == 24
    assert len(hourly_bounded["time"]) == 24


def test_weather_api_failure_error_handling():
    """Test 7: Weather API failure returns safe ERROR status."""
    with patch("httpx.get") as mock_get:
        mock_get.side_effect = Exception("Open-Meteo API connection timeout")

        res = get_weather_conditions(14.81, 74.13)

        assert res["status"] == "ERROR"
        assert res["data_status"] == "UNAVAILABLE"
        assert "error" in res
        assert "connection timeout" in res["error"]


def test_marine_risk_wind_gust_evaluation():
    """Test 8: calculate_marine_risk factors in elevated wind gusts deterministically."""
    ocean = {"observations": {"waves": {"significant_wave_height_m": 0.8}}}
    geofence = {"inside_restricted_zone": False}

    # Case A: Low gusts (<28 km/h)
    wx_low = {"current": {"wind_speed_10m": 12.0, "wind_gusts_10m": 20.0, "weather_code": 0}}
    risk_low = calculate_marine_risk(ocean, wx_low, geofence)
    assert risk_low["risk_level"] == "LOW"
    assert risk_low["evaluated_parameters"]["wind_gusts_kmh"] == 20.0

    # Case B: Severe peak gusts (>= 55 km/h)
    wx_high = {"current": {"wind_speed_10m": 22.0, "wind_gusts_10m": 60.0, "weather_code": 0}}
    risk_high = calculate_marine_risk(ocean, wx_high, geofence)
    assert risk_high["evaluated_parameters"]["wind_gusts_kmh"] == 60.0
    assert any("Severe peak wind gusts" in r for r in risk_high["reasons"])
    assert risk_high["risk_score"] > risk_low["risk_score"]


def test_weather_data_node_integration(mock_open_meteo_response):
    """Test 9: weather_data_node integration returns weather_data when required by plan."""
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_open_meteo_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        state = {
            "plan": {"domains_needed": ["weather"], "forecast_days": 3},
            "location": {"status": "FOUND", "name": "Goa", "latitude": 15.29, "longitude": 73.91},
        }

        result = weather_data_node(state)

        assert "weather_data" in result
        assert result["weather_data"]["status"] == "OK"
        assert "provenance" in result["weather_data"]
        assert "weather_data_collector" in result["node_trace"]
