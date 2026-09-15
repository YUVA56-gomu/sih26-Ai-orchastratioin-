"""
api/samudra_api.py
───────────────────
SAMUDRA.AI FastAPI application

Endpoints:
  POST /chat          — main conversational query
  GET  /health        — health check
  GET  /graph/schema  — returns graph structure for debugging/viz
"""

from __future__ import annotations

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import ChatRequest, ChatResponse, HealthResponse
from graph.graph import get_compiled_graph

app = FastAPI(
    title="SAMUDRA.AI",
    description="Agentic AI Marine Intelligence Platform",
    version="1.0.0-langgraph",
)

# Allow all origins in dev; lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main conversational endpoint.

    Accepts a natural language query and optional lat/lon override.
    Returns the synthesized response plus metadata.
    """

    graph = get_compiled_graph()

    # Build initial state
    initial_state = {
        "user_query": request.query.strip(),
        "conversation_history": [],
        "errors": [],
        "node_trace": [],
        "recheck_count": 0,
    }

    # If caller provides explicit coordinates, inject them into the plan
    # so the planner skips geocoding entirely
    if request.latitude is not None and request.longitude is not None:
        initial_state["plan"] = {
            "intent": "general",
            "location_text": f"{request.latitude},{request.longitude}",
            "coordinates_provided": True,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "time_request": "now",
            "forecast_days": 1,
            "domains_needed": ["ocean", "weather", "geofence"],
            "needs_safety": True,
            "needs_fishery": False,
            "needs_navigation": False,
        }

    # thread_id enables multi-turn memory via MemorySaver checkpointer
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph execution error: {exc}")

    # Extract risk info safely
    risk = result.get("risk_assessment", {})
    risk_level = risk.get("risk_level", "UNKNOWN")
    risk_score = int(risk.get("risk_score", -1))

    return ChatResponse(
        response=result.get("final_response") or result.get("final_response_english", ""),
        detected_language=result.get("detected_language", "en"),
        intent=str(result.get("intent", "general")),
        risk_level=risk_level,
        risk_score=risk_score,
        confidence_score=float(result.get("confidence_score", 1.0)),
        gate_decision=result.get("gate_decision", "PASS"),
        node_trace=result.get("node_trace", []),
        errors=result.get("errors", []),
        location=result.get("location"),
        thread_id=request.thread_id,
    )


@app.get("/graph/schema")
async def graph_schema():
    """Return node and edge list for frontend visualization."""
    graph = get_compiled_graph()
    try:
        # LangGraph exposes get_graph() for introspection
        schema = graph.get_graph()
        return {
            "nodes": [n for n in schema.nodes],
            "edges": [{"source": e.source, "target": e.target} for e in schema.edges],
        }
    except Exception as exc:
        return {"error": str(exc)}
