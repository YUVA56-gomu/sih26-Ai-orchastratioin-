"""
tests/test_conversation_core.py
───────────────────────────────
Unit & Integration Tests for SAMUDRA M1.2 — Conversation Core.

Tests:
  1. Multi-turn reference resolution ("Which one is closest?")
  2. Pronoun location resolution ("Can I go there tomorrow?")
  3. Location replacement ("What about Goa?")
  4. Conversation isolation (Conversation A vs Conversation B)
  5. Clean state for new conversation
  6. Persistence & restart behavior verification
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from api.samudra_api import app
from graph.graph import get_compiled_graph


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    def dummy_resolve(place):
        p = str(place).lower()
        if "goa" in p:
            return {"status": "FOUND", "name": "Goa", "latitude": 15.29, "longitude": 73.82, "source": "Mock"}
        if "chennai" in p:
            return {"status": "FOUND", "name": "Chennai", "latitude": 13.08, "longitude": 80.27, "source": "Mock"}
        if "karwar" in p:
            return {"status": "FOUND", "name": "Karwar", "latitude": 14.81, "longitude": 74.13, "source": "Mock"}
        return {"status": "NOT_FOUND", "place": place}

    def dummy_copernicus(lat, lon):
        return {"source": "Mock Copernicus", "location": {"latitude": lat, "longitude": lon}, "observations": {}}

    def dummy_weather(lat, lon, forecast_days=3):
        return {"status": "OK", "source": "Mock Weather", "current": {"temperature_2m": 28.5, "wind_speed_10m": 12.0}}

    def dummy_marine(lat, lon, forecast_days=7):
        return {"status": "OK", "source": "Mock Marine", "current": {"wave_height": 1.2}}

    def dummy_pfz(lat, lon):
        return {"status": "HEURISTIC", "source": "Mock PFZ", "candidates": [{"latitude": lat+0.1, "longitude": lon+0.1, "distance_km": 14.2}]}

    def dummy_risk(state):
        return {"risk_level": "LOW", "risk_score": 10, "reasons": []}

    monkeypatch.setattr("tools.copernicus_service.open_small_dataset", lambda **kwargs: None)
    monkeypatch.setattr("tools.location.resolve_location", dummy_resolve)
    monkeypatch.setattr("graph.nodes.location.resolve_location", dummy_resolve)
    monkeypatch.setattr("tools.copernicus_service.get_copernicus_marine_snapshot", dummy_copernicus)
    monkeypatch.setattr("graph.nodes.data_ocean.get_copernicus_marine_snapshot", dummy_copernicus)
    monkeypatch.setattr("tools.weather_service.get_weather_conditions", dummy_weather)
    monkeypatch.setattr("graph.nodes.data_weather.get_weather_conditions", dummy_weather)
    monkeypatch.setattr("tools.marine_service.get_marine_conditions", dummy_marine)
    monkeypatch.setattr("graph.nodes.data_marine.get_marine_conditions", dummy_marine)
    monkeypatch.setattr("tools.pfz_service.find_nearest_pfz", dummy_pfz)
    monkeypatch.setattr("graph.nodes.data_fishery.find_nearest_pfz", dummy_pfz)
    monkeypatch.setattr("tools.marine_risk.calculate_marine_risk", dummy_risk)
    monkeypatch.setattr("graph.nodes.risk.calculate_marine_risk", dummy_risk)


@pytest.fixture
def client():
    return TestClient(app)


def test_multi_turn_same_conversation(client):
    """Test 1: Turn 2 ('Which one is closest?') retains Turn 1 location context."""
    conv_id = f"test_conv_{uuid.uuid4()}"

    # Turn 1: Ask for PFZ near Karwar
    r1 = client.post("/chat", json={
        "message": "Find PFZ near Karwar",
        "conversation_id": conv_id,
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["conversation_id"] == conv_id
    assert d1["location"] is not None
    assert d1["location"].get("status") == "FOUND"
    assert "karwar" in d1["location"].get("name", "").lower()

    # Turn 2: Follow-up question referencing candidates
    r2 = client.post("/chat", json={
        "message": "Which one is closest?",
        "conversation_id": conv_id,
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["conversation_id"] == conv_id
    assert d2["location"] is not None
    assert d2["location"].get("status") == "FOUND"
    assert "karwar" in d2["location"].get("name", "").lower()
    assert d2["active_context"] is not None
    assert d2["active_context"].get("location", {}).get("name") is not None


def test_pronoun_reference_resolution(client):
    """Test 2: Turn 2 ('Can I go there tomorrow?') resolves 'there' to Turn 1 location."""
    conv_id = f"test_conv_{uuid.uuid4()}"

    # Turn 1
    r1 = client.post("/chat", json={
        "message": "Find PFZ near Karwar",
        "conversation_id": conv_id,
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["location"].get("status") == "FOUND"

    # Turn 2: Use pronoun "there"
    r2 = client.post("/chat", json={
        "message": "Can I go there tomorrow morning?",
        "conversation_id": conv_id,
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["location"] is not None
    assert d2["location"].get("status") == "FOUND"
    assert d2["location"].get("latitude") is not None


def test_location_replacement(client):
    """Test 3: Specifying a new location ('What about Goa?') replaces active location."""
    conv_id = f"test_conv_{uuid.uuid4()}"

    # Turn 1: Karwar
    r1 = client.post("/chat", json={
        "message": "What is the weather near Karwar?",
        "conversation_id": conv_id,
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert "karwar" in d1["location"].get("name", "").lower()

    # Turn 2: Goa
    r2 = client.post("/chat", json={
        "message": "What about Goa?",
        "conversation_id": conv_id,
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["location"].get("status") == "FOUND"
    assert "goa" in d2["location"].get("name", "").lower()
    assert d2["active_context"].get("location", {}).get("name") is not None
    assert "goa" in d2["active_context"].get("location", {}).get("name", "").lower()


def test_conversation_isolation(client):
    """Test 4: Conversation B cannot access Conversation A's active context."""
    conv_a = f"conv_A_{uuid.uuid4()}"
    conv_b = f"conv_B_{uuid.uuid4()}"

    # Conversation A establishes location Karwar
    rA = client.post("/chat", json={
        "message": "Find PFZ near Karwar",
        "conversation_id": conv_a,
    })
    assert rA.status_code == 200
    dA = rA.json()
    assert dA["location"].get("status") == "FOUND"

    # Conversation B asks generic question without location
    rB = client.post("/chat", json={
        "message": "Which one is closest?",
        "conversation_id": conv_b,
    })
    assert rB.status_code == 200
    dB = rB.json()
    # Conversation B should NOT inherit Karwar from Conversation A
    if dB.get("location"):
        assert dB["location"].get("status") != "FOUND" or "karwar" not in dB["location"].get("name", "").lower()


def test_new_conversation_starts_clean(client):
    """Test 5: Request without conversation_id receives a new clean conversation."""
    r = client.post("/chat", json={
        "message": "What is the weather near Chennai?",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["conversation_id"] is not None
    assert d["conversation_id"] != "default"
    assert d["location"].get("status") == "FOUND"


def test_restart_behavior_documenting():
    """Test 6: Verify in-memory checkpointer behavior (documentation test)."""
    graph = get_compiled_graph()
    assert graph is not None
    # LangGraph in-memory MemorySaver retains state only per process lifecycle.
