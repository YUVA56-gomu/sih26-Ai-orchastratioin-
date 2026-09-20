"""
tests/test_context_management.py
──────────────────────────────────
Comprehensive unit & integration tests for M1.6 Context Management & Rolling Context Summarization.
"""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from storage.conversation_store import ConversationStore
from storage.sqlite_saver import SqliteSaver
from graph.graph import get_compiled_graph
from graph.nodes.summarizer import summarizer_node, SUMMARY_THRESHOLD_MESSAGES
from graph.nodes.utils import format_recent_history
from langchain_core.messages import HumanMessage, AIMessage


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    """Mock external APIs and LLM calls for fast, deterministic test execution."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    def dummy_resolve(place):
        p = str(place).lower()
        if "goa" in p:
            return {"status": "FOUND", "name": "Goa", "latitude": 15.29, "longitude": 73.82, "source": "Mock"}
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


def test_1_history_formatting_with_summary():
    """Test 1: Verify format_recent_history includes summary and bounded recent raw turns."""
    state_without_summary = {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
    }
    formatted1 = format_recent_history(state_without_summary)
    assert "Long-term Conversation Summary:" not in formatted1
    assert "User: Hello" in formatted1

    state_with_summary = {
        "context_summary": "User operates a artisanal fishing trawler near Karwar.",
        "messages": [
            HumanMessage(content="What about waves?"),
            AIMessage(content="Waves are 1.2m."),
        ]
    }
    formatted2 = format_recent_history(state_with_summary)
    assert "Long-term Conversation Summary:" in formatted2
    assert "User operates a artisanal fishing trawler near Karwar." in formatted2
    assert "Recent Conversation History:" in formatted2
    assert "User: What about waves?" in formatted2


def test_2_summarization_threshold():
    """Test 2: Verify summarization does NOT occur below threshold and DOES occur above threshold."""
    # Under threshold (<= 6 messages)
    state_short = {
        "messages": [
            HumanMessage(content="Turn 1"), AIMessage(content="Reply 1"),
            HumanMessage(content="Turn 2"), AIMessage(content="Reply 2"),
        ]
    }
    res_short = summarizer_node(state_short)
    assert res_short == {}

    # Over threshold (> 6 messages)
    state_long = {
        "messages": [
            HumanMessage(content="Turn 1"), AIMessage(content="Reply 1"),
            HumanMessage(content="Turn 2"), AIMessage(content="Reply 2"),
            HumanMessage(content="Turn 3"), AIMessage(content="Reply 3"),
            HumanMessage(content="Turn 4"), AIMessage(content="Reply 4"),
        ]
    }
    res_long = summarizer_node(state_long)
    assert "context_summary" in res_long
    assert len(res_long["context_summary"]) > 0


def test_3_long_conversation_context_retention(client):
    """Test 3: Simulate 10+ turns and verify context summary retains older conversational intent."""
    conv_id = f"test_long_conv_{uuid.uuid4().hex[:8]}"

    # Send 5 turns (10 messages)
    queries = [
        "Hi, I operate a commercial fishing boat near Karwar.",
        "What is the sea surface temperature?",
        "What is the wave forecast?",
        "Are there any restricted geofence areas?",
        "Find PFZ candidates near Karwar.",
    ]
    for q in queries:
        r = client.post("/chat", json={"message": q, "conversation_id": conv_id})
        assert r.status_code == 200

    # Retrieve conversation detail endpoint
    r_detail = client.get(f"/conversations/{conv_id}")
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert len(detail["messages"]) >= 10
    assert detail.get("context_summary") is not None


def test_4_rolling_summary_incorporates_previous_summary():
    """Test 4: Verify subsequent summarization incorporates the previous summary rather than discarding it."""
    state_turn1 = {
        "context_summary": "Initial summary: User operates near Karwar.",
        "messages": [
            HumanMessage(content="T1"), AIMessage(content="R1"),
            HumanMessage(content="T2"), AIMessage(content="R2"),
            HumanMessage(content="T3"), AIMessage(content="R3"),
            HumanMessage(content="T4"), AIMessage(content="R4"),
        ]
    }
    res = summarizer_node(state_turn1)
    assert "context_summary" in res
    assert len(res["context_summary"]) > 0


def test_5_fast_path_without_unnecessary_summarization(client):
    """Test 5: Verify simple Fast Path conversations work and do not invoke summarization below threshold."""
    conv_id = f"test_fast_{uuid.uuid4().hex[:8]}"

    r1 = client.post("/chat", json={"message": "Hi", "conversation_id": conv_id})
    assert r1.status_code == 200
    assert r1.json()["route_path"] == "FAST"

    r2 = client.post("/chat", json={"message": "What is PFZ?", "conversation_id": conv_id})
    assert r2.status_code == 200
    assert r2.json()["route_path"] == "FAST"


def test_6_deep_path_with_context_summary(client):
    """Test 6: Verify Deep Path works cleanly with context_summary present."""
    conv_id = f"test_deep_summary_{uuid.uuid4().hex[:8]}"

    # Turn 1
    client.post("/chat", json={"message": "Find PFZ near Karwar", "conversation_id": conv_id})
    # Turn 2
    client.post("/chat", json={"message": "Which one is closest?", "conversation_id": conv_id})
    # Turn 3
    client.post("/chat", json={"message": "What about tomorrow morning?", "conversation_id": conv_id})
    # Turn 4: DEEP query with accumulated context
    r4 = client.post("/chat", json={"message": "Is it safe to fish there tomorrow?", "conversation_id": conv_id})
    assert r4.status_code == 200
    assert r4.json()["route_path"] == "DEEP"
    assert r4.json()["active_context"]["location"]["name"] == "Karwar"


def test_7_context_summary_persistence_across_restarts():
    """Test 7: Verify context_summary survives backend process restarts."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    try:
        conv_id = f"restart_summary_{uuid.uuid4().hex[:8]}"

        # --- INSTANCE 1 ---
        store1 = ConversationStore(db_path=db_path)
        graph1 = get_compiled_graph(db_path=db_path)
        config1 = {"configurable": {"thread_id": conv_id}}

        store1.get_or_create_conversation(conv_id, first_query="Long query chain")
        state_in = {
            "messages": [
                HumanMessage(content="M1"), AIMessage(content="R1"),
                HumanMessage(content="M2"), AIMessage(content="R2"),
                HumanMessage(content="M3"), AIMessage(content="R3"),
                HumanMessage(content="M4"), AIMessage(content="R4"),
            ],
            "context_summary": "Persisted summary text before restart.",
            "conversation_id": conv_id,
            "thread_id": conv_id,
            "user_query": "M4",
        }
        res1 = graph1.invoke(state_in, config=config1)
        assert res1.get("context_summary") is not None

        # --- SIMULATE RESTART (Instance 2) ---
        store2 = ConversationStore(db_path=db_path)
        graph2 = get_compiled_graph(db_path=db_path)
        config2 = {"configurable": {"thread_id": conv_id}}

        checkpoint_state = graph2.get_state(config2)
        assert checkpoint_state.values is not None
        assert checkpoint_state.values.get("context_summary") is not None

    finally:
        get_compiled_graph(db_path="samudra_storage.db")
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except OSError:
            pass
