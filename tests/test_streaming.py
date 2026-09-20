"""
tests/test_streaming.py
───────────────────────
Comprehensive test suite for SAMUDRA AI Phase 1 — Milestone 7 (Streaming Pipeline).

Tests:
1. /chat/stream basic connection
2. FAST-path streaming
3. DEEP-path streaming
4. Correct event ordering
5. Valid JSON SSE payloads
6. conversation_id preservation
7. thread_id preservation
8. route_path preservation
9. Final done event completeness
10. Final response correctness
11. Artifact delivery (incremental & final)
12. Persistence after streaming
13. context_summary compatibility & multi-turn streaming
14. Error event behavior
15. Backward compatibility with POST /chat
"""

import os
# Ensure mock LLM provider is active for fast deterministic testing
os.environ["LLM_PROVIDER"] = "mock"

import json
import pytest
from fastapi.testclient import TestClient

from api.samudra_api import app, conversation_store


@pytest.fixture
def client():
    return TestClient(app)


def parse_sse_events(raw_text: str) -> list[dict]:
    """Helper function to parse standard SSE streams into list of event dicts."""
    events = []
    blocks = raw_text.strip().split("\n\n")
    for block in blocks:
        if not block.strip():
            continue
        event_name = None
        data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line.replace("event:", "").strip()
            elif line.startswith("data:"):
                data_str = line.replace("data:", "").strip()
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    data = data_str
        if event_name:
            events.append({"event": event_name, "data": data})
    return events


def test_basic_stream_connection(client):
    """Test 1: GET /chat/stream connects and receives start event."""
    response = client.get("/chat/stream?query=Hi")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = parse_sse_events(response.text)
    assert len(events) >= 2
    assert events[0]["event"] == "start"
    assert "conversation_id" in events[0]["data"]
    assert events[-1]["event"] == "done"


def test_fast_path_streaming(client):
    """Test 2 & 8: FAST-path query streaming overhead and route_path."""
    response = client.get("/chat/stream?message=Hello")
    assert response.status_code == 200
    events = parse_sse_events(response.text)
    
    event_names = [e["event"] for e in events]
    assert "start" in event_names
    assert "node" in event_names
    assert "done" in event_names

    done_event = [e for e in events if e["event"] == "done"][0]
    assert done_event["data"]["route_path"] == "FAST"
    assert done_event["data"]["response"] != ""


def test_deep_path_streaming(client):
    """Test 3, 4, 5, 9, 10: DEEP-path streaming, node sequence, valid JSON payloads."""
    response = client.get("/chat/stream?query=Can+I+safely+go+fishing+near+Karwar+tomorrow+morning%3F")
    assert response.status_code == 200
    events = parse_sse_events(response.text)

    event_names = [e["event"] for e in events]
    assert "start" in event_names
    assert "node" in event_names
    assert "done" in event_names

    # Check node events sequence in DEEP path
    node_names = [e["data"]["node"] for e in events if e["event"] == "node"]
    assert "language_detection" in node_names
    assert "intent_router" in node_names
    assert "planner" in node_names
    assert "synthesizer" in node_names

    done_data = [e["data"] for e in events if e["event"] == "done"][0]
    assert done_data["route_path"] == "DEEP"
    assert done_data["response"] != ""
    assert "conversation_id" in done_data
    assert "thread_id" in done_data


def test_conversation_id_and_thread_id_preservation(client):
    """Test 6 & 7: Preservation of custom conversation_id and thread_id."""
    custom_conv_id = "test_stream_conv_123"
    response = client.get(f"/chat/stream?query=Hi&conversation_id={custom_conv_id}")
    assert response.status_code == 200
    events = parse_sse_events(response.text)

    start_data = events[0]["data"]
    done_data = events[-1]["data"]

    assert start_data["conversation_id"] == custom_conv_id
    assert start_data["thread_id"] == custom_conv_id
    assert done_data["conversation_id"] == custom_conv_id
    assert done_data["thread_id"] == custom_conv_id


def test_artifact_delivery(client):
    """Test 11: Incremental artifact event emission and final done artifact payload."""
    response = client.get("/chat/stream?query=Find+PFZ+near+Karwar")
    assert response.status_code == 200
    events = parse_sse_events(response.text)

    artifact_events = [e for e in events if e["event"] == "artifact"]
    done_event = [e for e in events if e["event"] == "done"][0]

    assert len(artifact_events) >= 1
    for art_evt in artifact_events:
        art = art_evt["data"]["artifact"]
        assert "id" in art
        assert "type" in art

    done_artifacts = done_event["data"]["artifacts"]
    assert len(done_artifacts) >= 1


def test_persistence_after_streaming(client):
    """Test 12: Streamed conversations are recorded in persistent store."""
    conv_id = "persist_stream_999"
    response = client.get(f"/chat/stream?query=What+is+the+weather+near+Goa%3F&conversation_id={conv_id}")
    assert response.status_code == 200

    record = conversation_store.get_conversation(conv_id)
    assert record is not None
    assert record["conversation_id"] == conv_id

    # Check conversation detail endpoint
    detail_res = client.get(f"/conversations/{conv_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["conversation_id"] == conv_id
    assert len(detail_data["messages"]) >= 2  # user + assistant turns stored in checkpoint


def test_multi_turn_context_streaming(client):
    """Test 13: Multi-turn conversational context retained across streams."""
    conv_id = "multi_turn_stream_888"
    
    # Turn 1
    res1 = client.get(f"/chat/stream?query=What+is+the+weather+near+Karwar%3F&conversation_id={conv_id}")
    assert res1.status_code == 200
    events1 = parse_sse_events(res1.text)
    done1 = [e["data"] for e in events1 if e["event"] == "done"][0]
    assert done1["active_context"] is not None
    assert "karwar" in done1["active_context"].get("location", {}).get("name", "").lower()

    # Turn 2: Anaphoric query referring back to Karwar
    res2 = client.get(f"/chat/stream?query=Can+I+safely+go+fishing+there+tomorrow%3F&conversation_id={conv_id}")
    assert res2.status_code == 200
    events2 = parse_sse_events(res2.text)
    done2 = [e["data"] for e in events2 if e["event"] == "done"][0]
    
    # Active location should still be preserved
    assert done2["location"] is not None
    assert "karwar" in done2["location"].get("name", "").lower()


def test_post_chat_stream_endpoint(client):
    """Test POST /chat/stream endpoint with ChatRequest JSON body."""
    payload = {
        "message": "Is it safe to sail near Malpe?",
        "conversation_id": "post_stream_conv_1",
    }
    response = client.post("/chat/stream", json=payload)
    assert response.status_code == 200
    events = parse_sse_events(response.text)

    start_event = events[0]
    assert start_event["event"] == "start"
    assert start_event["data"]["conversation_id"] == "post_stream_conv_1"

    done_event = events[-1]
    assert done_event["event"] == "done"
    assert done_event["data"]["response"] != ""


def test_empty_query_error_handling(client):
    """Test 14: Error handling for empty query string."""
    response = client.get("/chat/stream?query=")
    assert response.status_code == 400


def test_backward_compatibility_post_chat(client):
    """Test 15: POST /chat non-streaming endpoint continues to function perfectly."""
    payload = {
        "message": "Hello SAMUDRA",
        "conversation_id": "non_stream_compat_1",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "non_stream_compat_1"
    assert data["response"] != ""
    assert data["route_path"] == "FAST"
