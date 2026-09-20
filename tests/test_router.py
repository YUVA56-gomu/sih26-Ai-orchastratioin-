"""
tests/test_router.py
────────────────────
Unit & integration tests for M1.3 Fast/Deep Router.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)


def test_fast_path_queries(client):
    """Verify simple queries execute via FAST path."""
    fast_queries = [
        "Hi",
        "Who are you?",
        "What is PFZ?",
        "What is SST?",
        "What is SST near Karwar?",
        "What are the waves near Karwar?",
    ]

    for q in fast_queries:
        r = client.post("/chat", json={"message": q})
        assert r.status_code == 200
        d = r.json()
        assert d.get("route_path") == "FAST", f"Query '{q}' should be FAST but was {d.get('route_path')}"
        trace = d.get("node_trace", [])
        assert "fast_responder" in trace
        assert "planner" not in trace
        assert "ocean_data_collector" not in trace
        assert "anti_hallucination_gate" not in trace
        assert "risk_assessment" not in trace
        assert "synthesizer" not in trace
        # FAST response should not fabricate risk values
        assert d.get("risk_level") is None
        assert d.get("risk_score") is None


def test_deep_path_queries(client):
    """Verify complex queries execute via DEEP path."""
    deep_queries = [
        "Can I safely go fishing near Karwar tomorrow morning?",
        "Find the nearest PFZ and tell me whether it is safe.",
        "Find a safe route considering weather and waves.",
    ]

    for q in deep_queries:
        r = client.post("/chat", json={"message": q})
        assert r.status_code == 200
        d = r.json()
        assert d.get("route_path") == "DEEP", f"Query '{q}' should be DEEP but was {d.get('route_path')}"
        trace = d.get("node_trace", [])
        assert "planner" in trace
        assert "synthesizer" in trace


def test_context_switching_fast_fast_deep(client):
    """
    Test context retention across path switches:
    Turn 1: "What is the weather near Karwar?" (FAST)
    Turn 2: "What about the waves?" (FAST)
    Turn 3: "Can I safely go tomorrow?" (DEEP)
    """
    conv_id = f"test_switch_{uuid.uuid4()}"

    # Turn 1: FAST
    r1 = client.post("/chat", json={"message": "What is the weather near Karwar?", "conversation_id": conv_id})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1.get("route_path") == "FAST"
    assert d1.get("active_context") is not None
    assert d1.get("active_context", {}).get("location") is not None
    assert "karwar" in d1.get("active_context", {}).get("location", {}).get("name", "").lower()

    # Turn 2: FAST (inherits Karwar from Turn 1 active_context)
    r2 = client.post("/chat", json={"message": "What about the waves?", "conversation_id": conv_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("route_path") == "FAST"
    assert d2.get("active_context") is not None
    assert d2.get("active_context", {}).get("location") is not None
    assert "karwar" in d2.get("active_context", {}).get("location", {}).get("name", "").lower()

    # Turn 3: DEEP (safety decision requires DEEP path while preserving Karwar)
    r3 = client.post("/chat", json={"message": "Can I safely go tomorrow?", "conversation_id": conv_id})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3.get("route_path") == "DEEP"
    assert d3.get("location") is not None
    assert "karwar" in d3.get("location", {}).get("name", "").lower()


def test_conversation_isolation_fast_path(client):
    """Verify Fast Path context does not leak to a new conversation."""
    conv_a = f"conv_a_{uuid.uuid4()}"
    conv_b = f"conv_b_{uuid.uuid4()}"

    # Conv A
    rA = client.post("/chat", json={"message": "What is the weather near Karwar?", "conversation_id": conv_a})
    assert rA.status_code == 200

    # Conv B
    rB = client.post("/chat", json={"message": "What is the weather?", "conversation_id": conv_b})
    assert rB.status_code == 200
    dB = rB.json()
    assert dB.get("active_context") is None or dB.get("active_context", {}).get("location") is None
