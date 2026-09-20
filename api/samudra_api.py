"""
api/samudra_api.py
───────────────────
SAMUDRA.AI FastAPI application

Endpoints:
  POST /chat          — main conversational query
  GET  /chat/stream   — real-time SSE streaming of agent execution steps
  GET  /health        — health check
  GET  /graph/schema  — returns graph structure for debugging/viz
  + Includes Marine Data Gateway endpoints (/marine/point, /marine/grid, /marine/map/*)
"""

from __future__ import annotations

import os
import json
import uuid
import asyncio
from typing import Optional, AsyncGenerator
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles

from api.models import ChatRequest, ChatResponse, HealthResponse
from graph.graph import get_compiled_graph

# Import marine data tools directly for unified gateway API
from tools.copernicus_service import get_copernicus_marine_snapshot
from tools.copernicus_grid import get_copernicus_grid
from tools.copernicus_wmts import (
    discover_layers,
    discover_orca_layers,
    get_capabilities_xml,
    build_orca_tile_template,
    build_orca_legend_url,
    get_orca_wmts_layer,
)

app = FastAPI(
    title="SAMUDRA.AI",
    description="Agentic AI Marine Intelligence Platform with Multi-Agent Thinking Stream",
    version="1.0.0-langgraph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# ── MARINE GATEWAY ENDPOINTS ─────────────────────────────────────────────────

@app.get("/marine/point")
def marine_point(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        return get_copernicus_marine_snapshot(latitude=latitude, longitude=longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "Copernicus retrieval failed", "message": str(exc)})


@app.get("/marine/grid")
def marine_grid(
    parameter: str = Query(...),
    minimum_latitude: float = Query(..., ge=-90, le=90),
    maximum_latitude: float = Query(..., ge=-90, le=90),
    minimum_longitude: float = Query(..., ge=-180, le=180),
    maximum_longitude: float = Query(..., ge=-180, le=180),
):
    try:
        return get_copernicus_grid(
            parameter,
            minimum_latitude=minimum_latitude,
            maximum_latitude=maximum_latitude,
            minimum_longitude=minimum_longitude,
            maximum_longitude=maximum_longitude,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "Grid retrieval failed", "message": str(exc)})


@app.get("/marine/map/capabilities", response_class=Response)
def wmts_capabilities():
    try:
        return Response(content=get_capabilities_xml(), media_type="application/xml")
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "Capabilities failed", "message": str(exc)})


@app.get("/marine/map/layers")
def wmts_layers():
    try:
        layers = discover_layers()
        return {"service": "Copernicus Marine WMTS", "count": len(layers), "layers": layers}
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "Layer discovery failed", "message": str(exc)})


@app.get("/marine/map/orca-layers")
def orca_map_layers():
    try:
        layers = discover_layers()
        categorized = discover_orca_layers(layers)
        return {"service": "Copernicus Marine WMTS", "count": len(layers), "categories": categorized}
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "WMTS discovery failed", "message": str(exc)})


@app.get("/marine/map/config/{parameter}")
def map_config(parameter: str):
    parameter = parameter.lower().strip()
    try:
        definition = get_orca_wmts_layer(parameter)
        return {
            "parameter": parameter,
            "title": definition["title"],
            "unit": definition["unit"],
            "layer": definition["layer"],
            "projection": "EPSG:3857",
            "tile_matrix_set": definition["matrix_set"],
            "tile_size": 256,
            "tile_url": build_orca_tile_template(parameter),
            "legend_url": build_orca_legend_url(parameter),
            "style": definition["style"],
            "source": "Copernicus Marine WMTS",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"error": "Map config failed", "message": str(exc)})


# ── AGENT STEP FORMATTER ──────────────────────────────────────────────────────

_NODE_METADATA = {
    "language_detection": ("🌐", "Language Detection Agent"),
    "intent_router": ("🧭", "Intent Router Agent"),
    "fast_responder": ("⚡", "Fast Response Agent"),
    "planner": ("📋", "Decomposition Planner Agent"),
    "location_resolver": ("📍", "Location Resolver Agent"),
    "ocean_data_collector": ("🌊", "Copernicus Ocean Data Collector"),
    "weather_data_collector": ("🌤️", "Open-Meteo Weather Collector"),
    "marine_data_collector": ("⚓", "Marine Wave Dynamics Collector"),
    "fishery_data_collector": ("🐟", "Fishery & PFZ Service"),
    "geofence_data_collector": ("🛡️", "Geofence & MPA Guard"),
    "anti_hallucination_gate": ("⚡", "Anti-Hallucination Safety Gate"),
    "risk_assessment": ("🧮", "Deterministic Marine Risk Engine"),
    "ocean_reasoner": ("🌊", "Ocean Specialist Agent"),
    "weather_reasoner": ("🌤️", "Weather Specialist Agent"),
    "fishery_reasoner": ("🐟", "Fishery Specialist Agent"),
    "safety_reasoner": ("🛟", "Marine Safety Specialist Agent"),
    "synthesizer": ("🤖", "Multi-Agent Synthesizer"),
    "translate_out": ("🌐", "Translation & Output Agent"),
}


def build_node_thought(node_name: str, node_output: dict) -> tuple[str, str, str, dict]:
    """Extract (icon, label, thought_text, summary_data) for a given node output."""
    icon, label = _NODE_METADATA.get(node_name, ("🤖", f"Agent ({node_name})"))
    thought = "Agent completed execution step."
    summary_data = {}

    if node_name == "language_detection":
        lang = node_output.get("detected_language", "en")
        thought = f"Detected query language: '{lang}'."
        summary_data = {"detected_language": lang}

    elif node_name == "intent_router":
        intent = node_output.get("intent", "general")
        thought = f"Classified primary intent as: {str(intent).upper()}."
        summary_data = {"intent": intent}

    elif node_name == "fast_responder":
        resp = node_output.get("final_response_english", "")
        thought = "Executed simple query via Fast Path ⚡."
        summary_data = {"response_snippet": resp[:150] + "..." if len(resp) > 150 else resp}

    elif node_name == "planner":
        plan = node_output.get("plan", {})
        domains = plan.get("domains_needed", [])
        thought = f"Decomposed query into domain plan: {', '.join(domains)}."
        summary_data = plan

    elif node_name == "location_resolver":
        loc = node_output.get("location", {})
        loc_str = loc.get("name") or f"{loc.get('latitude')}, {loc.get('longitude')}"
        thought = f"Resolved target coordinates to: {loc_str} ({loc.get('latitude')}, {loc.get('longitude')})."
        summary_data = loc

    elif node_name == "ocean_data_collector":
        ocean = node_output.get("ocean_data", {})
        sst = ocean.get("sst", {}).get("value")
        current_spd = ocean.get("current", {}).get("speed")
        thought = f"Fetched ocean data — SST: {sst if sst else 'N/A'}°C | Current Speed: {current_spd if current_spd else 'N/A'} m/s."
        summary_data = ocean

    elif node_name == "weather_data_collector":
        wx = node_output.get("weather_data", {})
        wind = wx.get("current", {}).get("wind_speed_10m")
        temp = wx.get("current", {}).get("temperature_2m")
        thought = f"Fetched weather forecast — Temp: {temp if temp is not None else 'N/A'}°C | Wind: {wind if wind is not None else 'N/A'} km/h."
        summary_data = {"temperature": temp, "wind_speed": wind}

    elif node_name == "marine_data_collector":
        marine = node_output.get("marine_data", {})
        waves = marine.get("current", {}).get("wave_height")
        thought = f"Fetched wave dynamics — Significant Wave Height: {waves if waves is not None else 'N/A'} m."
        summary_data = marine

    elif node_name == "fishery_data_collector":
        fish = node_output.get("fishery_data", {})
        pfz = fish.get("pfz_status", "Calculated")
        thought = f"Evaluated Potential Fishing Zones (PFZ): Status = {pfz}."
        summary_data = fish

    elif node_name == "geofence_data_collector":
        geo = node_output.get("geofence_data", {})
        restricted = geo.get("inside_restricted_zone", False)
        thought = f"Spatial boundary check: Inside Restricted Marine Area = {restricted}."
        summary_data = geo

    elif node_name == "anti_hallucination_gate":
        decision = node_output.get("gate_decision", "PASS")
        conf = node_output.get("confidence_score", 1.0)
        thought = f"Gate Verification: Decision = {decision} | Confidence Score = {conf*100:.0f}%."
        summary_data = {"gate_decision": decision, "confidence_score": conf}

    elif node_name == "risk_assessment":
        risk = node_output.get("risk_assessment", {})
        level = risk.get("risk_level", "UNKNOWN")
        score = risk.get("risk_score", -1)
        thought = f"Calculated Marine Safety Risk Level: {level} (Score: {score}/100)."
        summary_data = risk

    elif node_name in ("ocean_reasoner", "weather_reasoner", "fishery_reasoner", "safety_reasoner"):
        key = f"{node_name.split('_')[0]}_reasoning"
        reasoning = node_output.get(key, "")
        snippet = reasoning.replace("\n", " ")[:120]
        thought = f"Specialist Reasoning: {snippet}..."
        summary_data = {key: reasoning}

    elif node_name == "synthesizer":
        eng = node_output.get("final_response_english", "")
        thought = "Synthesized multi-specialist evidence into unified marine intelligence report."
        summary_data = {"final_response_english": eng[:200] + "..."}

    elif node_name == "translate_out":
        final_resp = node_output.get("final_response", "")
        thought = "Finalized output generation and multi-lingual translation."
        summary_data = {"final_response": final_resp[:200] + "..."}

    return icon, label, thought, summary_data


# ── CONVERSATIONAL CHAT ENDPOINTS ─────────────────────────────────────────────

# ── CONVERSATIONAL CHAT ENDPOINTS ─────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main conversational endpoint with multi-turn context support."""
    user_text = (request.message or request.query or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    conv_id = request.conversation_id or request.thread_id
    if not conv_id or conv_id == "default":
        conv_id = str(uuid.uuid4())
    t_id = conv_id

    graph = get_compiled_graph()

    initial_state = {
        "conversation_id": conv_id,
        "thread_id": t_id,
        "user_query": user_text,
        "errors": [],
        "node_trace": [],
        "recheck_count": 0,
    }

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

    config = {"configurable": {"thread_id": t_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph execution error: {exc}")

    route_path = result.get("route_path", "DEEP")
    risk = result.get("risk_assessment")
    risk_level = risk.get("risk_level") if isinstance(risk, dict) else None
    risk_score = int(risk.get("risk_score")) if isinstance(risk, dict) and risk.get("risk_score") is not None else None
    confidence_score = float(result["confidence_score"]) if "confidence_score" in result else None
    gate_decision = result.get("gate_decision")

    return ChatResponse(
        conversation_id=conv_id,
        thread_id=t_id,
        response=result.get("final_response") or result.get("final_response_english", ""),
        artifacts=result.get("artifacts", []),
        route_path=route_path,
        detected_language=result.get("detected_language", "en"),
        intent=str(result.get("intent", "general")),
        risk_level=risk_level,
        risk_score=risk_score,
        confidence_score=confidence_score,
        gate_decision=gate_decision,
        node_trace=result.get("node_trace", []),
        errors=result.get("errors", []),
        location=result.get("location"),
        active_context=result.get("active_context"),
    )


@app.get("/chat/stream")
async def chat_stream(
    query: Optional[str] = Query(None),
    message: Optional[str] = Query(None),
    conversation_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
):
    """
    Server-Sent Events (SSE) streaming endpoint with multi-turn conversation support.
    Yields live updates as each AI agent node in the LangGraph graph executes.
    """
    user_text = (message or query or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    conv_id = conversation_id or thread_id
    if not conv_id or conv_id == "default":
        conv_id = str(uuid.uuid4())
    t_id = conv_id

    graph = get_compiled_graph()

    initial_state = {
        "conversation_id": conv_id,
        "thread_id": t_id,
        "user_query": user_text,
        "errors": [],
        "node_trace": [],
        "recheck_count": 0,
    }

    if latitude is not None and longitude is not None:
        initial_state["plan"] = {
            "intent": "general",
            "location_text": f"{latitude},{longitude}",
            "coordinates_provided": True,
            "latitude": latitude,
            "longitude": longitude,
            "time_request": "now",
            "forecast_days": 1,
            "domains_needed": ["ocean", "weather", "geofence"],
            "needs_safety": True,
            "needs_fishery": False,
            "needs_navigation": False,
        }

    config = {"configurable": {"thread_id": t_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        final_state = {}
        try:
            # Stream node output updates from LangGraph
            async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    if isinstance(node_output, dict):
                        final_state.update(node_output)
                        icon, label, thought, summary = build_node_thought(node_name, node_output)
                        event_data = {
                            "node": node_name,
                            "icon": icon,
                            "label": label,
                            "thought": thought,
                            "summary": summary,
                        }
                        yield f"event: agent_step\ndata: {json.dumps(event_data)}\n\n"
                        await asyncio.sleep(0.05)

            # Final response compilation
            risk = final_state.get("risk_assessment")
            response_text = final_state.get("final_response") or final_state.get("final_response_english", "Analysis complete.")
            done_payload = {
                "conversation_id": conv_id,
                "thread_id": t_id,
                "response": response_text,
                "artifacts": final_state.get("artifacts", []),
                "route_path": final_state.get("route_path", "DEEP"),
                "detected_language": final_state.get("detected_language", "en"),
                "intent": str(final_state.get("intent", "general")),
                "risk_level": risk.get("risk_level") if isinstance(risk, dict) else None,
                "risk_score": int(risk.get("risk_score")) if isinstance(risk, dict) and risk.get("risk_score") is not None else None,
                "confidence_score": float(final_state["confidence_score"]) if "confidence_score" in final_state else None,
                "gate_decision": final_state.get("gate_decision"),
                "node_trace": final_state.get("node_trace", []),
                "location": final_state.get("location"),
                "active_context": final_state.get("active_context"),
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except Exception as exc:
            err_payload = {"error": f"Graph streaming error: {str(exc)}"}
            yield f"event: error\ndata: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/graph/schema")
async def graph_schema():
    """Return node and edge list for frontend visualization."""
    graph = get_compiled_graph()
    try:
        schema = graph.get_graph()
        return {
            "nodes": [n for n in schema.nodes],
            "edges": [{"source": e.source, "target": e.target} for e in schema.edges],
        }
    except Exception as exc:
        return {"error": str(exc)}


web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")


