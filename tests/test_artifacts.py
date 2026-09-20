"""
tests/test_artifacts.py
─────────────────────────
Unit & integration tests for M1.4 Response & Artifact Protocol.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from tools.artifact_factory import (
    create_artifact,
    create_location_card_artifact,
    create_pfz_map_artifact,
    create_weather_card_artifact,
    create_marine_conditions_artifact,
    create_risk_summary_artifact,
)

@pytest.fixture
def client():
    return TestClient(app)


def test_artifact_factory_models():
    """Verify artifact helper functions produce valid Artifact dictionaries."""
    art = create_artifact("custom", "Test Title", {"key": "val"}, "Description text")
    assert art["id"].startswith("custom_")
    assert art["type"] == "custom"
    assert art["title"] == "Test Title"
    assert art["description"] == "Description text"
    assert art["data"] == {"key": "val"}

    # Test Location Card
    loc = {"status": "FOUND", "name": "Karwar", "latitude": 14.8, "longitude": 74.1}
    loc_art = create_location_card_artifact(loc)
    assert loc_art is not None
    assert loc_art["type"] == "location_card"
    assert loc_art["data"]["name"] == "Karwar"

    # Test Invalid location handling
    assert create_location_card_artifact({"status": "NOT_FOUND"}) is None


def test_fast_path_artifacts(client):
    """Verify FAST path queries return appropriate artifacts or empty list."""
    # Greetings & definitions -> no artifacts
    for msg in ["Hi", "Who are you?", "What is PFZ?"]:
        r = client.post("/chat", json={"message": msg})
        assert r.status_code == 200
        d = r.json()
        assert d.get("route_path") == "FAST"
        assert d.get("artifacts") == []

    # Single-tool lookup -> weather card artifact
    r2 = client.post("/chat", json={"message": "What is the weather near Karwar?"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("route_path") == "FAST"
    artifacts = d2.get("artifacts", [])
    assert len(artifacts) > 0
    assert any(a["type"] in ("weather_card", "location_card") for a in artifacts)


def test_deep_path_artifacts(client):
    """Verify DEEP path queries generate rich marine artifacts."""
    # PFZ Query -> pfz_map artifact
    r1 = client.post("/chat", json={"message": "Find PFZ near Karwar"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1.get("route_path") == "DEEP"
    artifacts1 = d1.get("artifacts", [])
    assert len(artifacts1) > 0
    assert any(a["type"] == "pfz_map" for a in artifacts1)

    # Safety Query -> risk_summary artifact
    r2 = client.post("/chat", json={"message": "Can I safely fish near Karwar tomorrow morning?"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("route_path") == "DEEP"
    artifacts2 = d2.get("artifacts", [])
    assert len(artifacts2) > 0
    assert any(a["type"] == "risk_summary" for a in artifacts2)


def test_artifact_context_retention_and_isolation(client):
    """Verify artifact context retention across turns and isolation between conversations."""
    conv_a = f"conv_art_a_{uuid.uuid4()}"
    conv_b = f"conv_art_b_{uuid.uuid4()}"

    # Conv A Turn 1
    rA1 = client.post("/chat", json={"message": "Find PFZ near Karwar", "conversation_id": conv_a})
    assert rA1.status_code == 200
    dA1 = rA1.json()
    assert dA1.get("active_context") is not None
    active_arts_A = dA1.get("active_context", {}).get("active_artifacts", [])
    assert len(active_arts_A) > 0

    # Conv A Turn 2 (inherits active_artifacts and selected_artifact)
    rA2 = client.post("/chat", json={"message": "Which one is closest?", "conversation_id": conv_a})
    assert rA2.status_code == 200
    dA2 = rA2.json()
    assert dA2.get("active_context", {}).get("selected_artifact") is not None

    # Conv B (must NOT inherit Conv A artifacts)
    rB = client.post("/chat", json={"message": "What is the weather?", "conversation_id": conv_b})
    assert rB.status_code == 200
    dB = rB.json()
    b_arts = dB.get("active_context", {}).get("active_artifacts") if dB.get("active_context") else None
    assert b_arts is None or len(b_arts) == 0
