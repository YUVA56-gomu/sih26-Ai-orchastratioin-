"""
tests/test_persistence.py
──────────────────────────
Comprehensive unit & integration tests for M1.5 Persistent Conversation Storage.
"""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from storage.conversation_store import ConversationStore, generate_deterministic_title
from storage.sqlite_saver import SqliteSaver
from graph.graph import get_compiled_graph
from langchain_core.messages import HumanMessage


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    """Mock external APIs and LLM calls for reliable, fast test execution."""
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


def test_deterministic_title_generation():
    """Verify deterministic title generation without LLM calls."""
    assert generate_deterministic_title("  Find   PFZ near   Karwar  ") == "Find PFZ near Karwar"
    assert generate_deterministic_title("What is the weather in Goa?") == "What is the weather in Goa"
    assert generate_deterministic_title("  hi ") == "Hi"
    assert generate_deterministic_title("") == "New Marine Conversation"
    # Long message truncation
    long_msg = "Can you please check the wave height, wind speed, water temperature, and safety risk assessment for fishing near Karwar tomorrow morning?"
    title = generate_deterministic_title(long_msg)
    assert len(title) <= 50
    assert not title.endswith(" ")


def test_automatic_conversation_creation_and_title(client):
    """Verify POST /chat creates a persistent conversation and deterministic title when no conversation_id is passed."""
    res = client.post("/chat", json={"message": "Find PFZ near Karwar"})
    assert res.status_code == 200
    data = res.json()
    
    conv_id = data.get("conversation_id")
    thread_id = data.get("thread_id")
    assert conv_id is not None
    assert thread_id is not None
    assert conv_id == thread_id

    # Verify conversation exists in GET /conversations
    res_list = client.get("/conversations")
    assert res_list.status_code == 200
    convs = res_list.json()
    matched = [c for c in convs if c["conversation_id"] == conv_id]
    assert len(matched) == 1
    assert matched[0]["title"] == "Find PFZ near Karwar"

    # Verify GET /conversations/{id}
    res_detail = client.get(f"/conversations/{conv_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["conversation_id"] == conv_id
    assert len(detail["messages"]) >= 2  # user msg + AI msg


def test_multi_turn_persistence_across_requests(client):
    """Verify message history and active context are retained across multiple requests with same conversation_id."""
    conv_id = f"test_conv_{uuid.uuid4().hex[:8]}"

    # Turn 1
    r1 = client.post("/chat", json={"message": "Find PFZ near Karwar", "conversation_id": conv_id})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["active_context"]["location"]["name"] == "Karwar"

    # Turn 2: reference resolution
    r2 = client.post("/chat", json={"message": "Which one is closest?", "conversation_id": conv_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["active_context"]["location"]["name"] == "Karwar"

    # Check GET /conversations/{id} message count
    r_detail = client.get(f"/conversations/{conv_id}")
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert len(detail["messages"]) == 4  # 2 user + 2 AI


def test_conversation_isolation(client):
    """Verify Conversation A state does not leak to Conversation B."""
    conv_a = f"conv_a_{uuid.uuid4().hex[:8]}"
    conv_b = f"conv_b_{uuid.uuid4().hex[:8]}"

    # Conv A sets location to Karwar
    r_a = client.post("/chat", json={"message": "Find PFZ near Karwar", "conversation_id": conv_a})
    assert r_a.status_code == 200
    assert r_a.json()["active_context"]["location"]["name"] == "Karwar"

    # Conv B asks generic query
    r_b = client.post("/chat", json={"message": "What is the weather?", "conversation_id": conv_b})
    assert r_b.status_code == 200
    b_ctx = r_b.json().get("active_context", {})
    # Conv B should NOT have Karwar as active location or artifacts from A
    loc_b = b_ctx.get("location") if b_ctx else None
    assert loc_b is None or loc_b.get("name") != "Karwar"


def test_routing_path_transitions_with_persistence(client):
    """Verify FAST -> FAST -> DEEP -> FAST route path transitions persist correctly."""
    conv_id = f"conv_route_{uuid.uuid4().hex[:8]}"

    # Turn 1: FAST
    r1 = client.post("/chat", json={"message": "Hi", "conversation_id": conv_id})
    assert r1.status_code == 200
    assert r1.json()["route_path"] == "FAST"

    # Turn 2: FAST
    r2 = client.post("/chat", json={"message": "What is PFZ?", "conversation_id": conv_id})
    assert r2.status_code == 200
    assert r2.json()["route_path"] == "FAST"

    # Turn 3: DEEP
    r3 = client.post("/chat", json={"message": "Find PFZ near Karwar", "conversation_id": conv_id})
    assert r3.status_code == 200
    assert r3.json()["route_path"] == "DEEP"
    assert r3.json()["active_context"]["location"]["name"] == "Karwar"

    # Turn 4: FAST (referencing previous context)
    r4 = client.post("/chat", json={"message": "Thanks, what about waves there?", "conversation_id": conv_id})
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["route_path"] == "FAST"
    assert d4.get("active_context") is not None or d4.get("location") is not None



def test_simulated_backend_restart():
    """
    CRITICAL RESTART TEST:
    Simulates a complete backend restart by creating fresh instances of SqliteSaver,
    ConversationStore, and get_compiled_graph() connected to the same temporary SQLite DB file.
    Verifies that state, messages, active_context, and artifacts survive across restart.
    """
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    try:
        conv_id = f"restart_conv_{uuid.uuid4().hex[:8]}"

        # --- INSTANCE 1 (Before Restart) ---
        store1 = ConversationStore(db_path=db_path)
        graph1 = get_compiled_graph(db_path=db_path)
        config1 = {"configurable": {"thread_id": conv_id}}

        # Process Turn 1: DEEP query setting active location & artifacts
        store1.get_or_create_conversation(conv_id, first_query="Find PFZ near Karwar")
        state_in1 = {
            "messages": [HumanMessage(content="Find PFZ near Karwar")],
            "conversation_id": conv_id,
            "thread_id": conv_id,
            "user_query": "Find PFZ near Karwar",
        }
        res1 = graph1.invoke(state_in1, config=config1)
        assert res1["active_context"]["location"]["name"] == "Karwar"
        assert len(res1["artifacts"]) > 0

        # --- SIMULATE RESTART (Instance 2) ---
        # Instantiate fresh graph and store using a different temp DB path or resetting singleton
        restart_db = db_path
        store2 = ConversationStore(db_path=restart_db)
        # We re-fetch graph for restart_db
        graph2 = get_compiled_graph(db_path=restart_db)
        config2 = {"configurable": {"thread_id": conv_id}}

        # Verify metadata persisted in store
        meta = store2.get_conversation(conv_id)
        assert meta is not None
        assert meta["title"] == "Find PFZ near Karwar"

        # Verify state loaded from checkpointer before Turn 2
        checkpoint_state = graph2.get_state(config2)
        assert checkpoint_state.values is not None
        assert checkpoint_state.values.get("active_context", {}).get("location", {}).get("name") == "Karwar"
        assert len(checkpoint_state.values.get("messages", [])) >= 1

        # Process Turn 2 on restarted instance (anaphoric reference resolution)
        state_in2 = {
            "messages": [HumanMessage(content="Which one is closest?")],
            "conversation_id": conv_id,
            "thread_id": conv_id,
            "user_query": "Which one is closest?",
        }
        res2 = graph2.invoke(state_in2, config=config2)
        assert res2["active_context"]["location"]["name"] == "Karwar"


    finally:
        # Reset graph singleton to default db_path before cleaning up temp file
        get_compiled_graph(db_path="samudra_storage.db")
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except OSError:
            pass


def test_conversations_api_endpoints(client):
    """Verify GET /conversations and GET /conversations/{id} error handling."""
    # Test 404 for non-existent conversation
    r_404 = client.get(f"/conversations/non_existent_{uuid.uuid4().hex[:8]}")
    assert r_404.status_code == 404
    assert "not found" in r_404.json()["detail"].lower()
