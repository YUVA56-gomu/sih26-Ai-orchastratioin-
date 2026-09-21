# PHASE 3 — FRONTEND READINESS AUDIT

## 1. Executive Summary
**PHASE 3 FRONTEND IMPLEMENTATION IS 100% READY TO BEGIN**.

The SAMUDRA AI backend (`langgraph-core`) provides a comprehensive, production-grade API surface for modern web dashboards. All Phase 2 intelligence milestones (Weather, Ocean Hydrodynamics, PFZ Fishery, Tide Dynamics, Hazard Advisories, Geospatial EEZ Engine, Marine Route Intelligence, Deterministic Risk Evaluation, and Evidence & Provenance) are fully integrated into FastAPI REST endpoints, multi-turn persistent conversation memory, Server-Sent Events (SSE) streaming pipelines, and standardized UI rendering artifacts.

---

## 2. Existing Backend API

### Base URL & Protocol
- **Default Local Server**: `http://localhost:8000`
- **Protocol**: HTTP/1.1 REST & SSE (Server-Sent Events)

### Endpoint Directory

| Method | Path | Description | Request Payload | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health check | N/A | `HealthResponse` (`status`, `service`, `version`) |
| `POST` | `/chat` | Main conversational query | `ChatRequest` (JSON) | `ChatResponse` (JSON) |
| `GET` | `/chat/stream` | Real-time SSE streaming (GET query params) | Query params (`query`, `conversation_id`, `latitude`, `longitude`) | `text/event-stream` (SSE) |
| `POST` | `/chat/stream` | Real-time SSE streaming (POST JSON body) | `ChatRequest` (JSON) | `text/event-stream` (SSE) |
| `GET` | `/conversations` | List persistent conversations | N/A | `list[ConversationSummary]` |
| `GET` | `/conversations/{id}` | Retrieve conversation history & context | Path param (`conversation_id`) | `ConversationDetail` |
| `GET` | `/marine/point` | Direct Copernicus Marine point query | Query params (`latitude`, `longitude`) | Point snapshot (JSON) |
| `GET` | `/marine/grid` | Direct Copernicus Marine bounding box grid | Query params (`parameter`, `min_lat`, `max_lat`, `min_lon`, `max_lon`) | Bounded 2D spatial grid (JSON) |
| `GET` | `/marine/map/orca-layers` | Discover categorized WMTS layers | N/A | Layer catalog (JSON) |
| `GET` | `/marine/map/config/{param}` | Tile matrix template & legend config | Path param (`parameter`) | WMTS tile config (JSON) |
| `GET` | `/graph/schema` | Graph architecture visualization | N/A | Nodes & edges list (JSON) |

---

## 3. Conversation Flow

```
Frontend User Query
    │
    ▼
FastAPI REST / SSE Endpoint (`POST /chat` or `/chat/stream`)
    │
    ▼
Conversation Store (`storage/conversation_store.py`)
    │
    ▼
LangGraph Compiled Engine (`graph/graph.py`) with `thread_id`
    │
    ├─► Language Detection Node (`graph/nodes/language.py`)
    ├─► Intent Router Node (`graph/nodes/intent.py`)
    ├─► Fast / Deep Path Split (`graph/nodes/router.py`)
    │     │
    │     ├─► Fast Path: Fast Responder Node (`graph/nodes/fast_responder.py`)
    │     │
    │     └─► Deep Path:
    │           ├─► Planner Node (`graph/nodes/planner.py`)
    │           ├─► Location Resolver Node (`graph/nodes/location.py`)
    │           ├─► Parallel Data Collectors:
    │           │     ├─ Weather Collector (`graph/nodes/data_weather.py`)
    │           │     ├─ Ocean Collector (`graph/nodes/data_ocean.py`)
    │           │     ├─ Fishery PFZ Collector (`graph/nodes/data_fishery.py`)
    │           │     ├─ Tide & Hazard Collector (`graph/nodes/data_tide_hazard.py`)
    │           │     ├─ Geofence GIS Collector (`graph/nodes/data_geofence.py`)
    │           │     └─ Route Intelligence Collector (`graph/nodes/data_route.py`)
    │           ├─► Anti-Hallucination Gate (`graph/nodes/gate.py`)
    │           ├─► Risk Assessment Node (`graph/nodes/risk.py`)
    │           ├─► Parallel Specialist Reasoners (`graph/nodes/reason_*.py`)
    │           ├─► Multi-Agent Synthesizer (`graph/nodes/synthesizer.py`)
    │           └─► Output Translator & Artifact Generator (`graph/nodes/translate_out.py`)
    │
    ▼
SQLite Persistence Checkpointer (`storage/sqlite_saver.py`)
    │
    ▼
API Response Payload / SSE Stream to Frontend Client
```

---

## 4. SSE / Streaming Contract

### Overview
Both `GET /chat/stream` and `POST /chat/stream` emit Server-Sent Events with `Content-Type: text/event-stream`.

### Event Event Types & Payloads

1. **`start`**:
   ```json
   event: start
   data: {"conversation_id": "conv-123", "thread_id": "conv-123", "query": "Is it safe to sail from Mumbai to Goa?"}
   ```

2. **`node`** / **`agent_step`**:
   ```json
   event: agent_step
   data: {
     "node": "weather_data_collector",
     "status": "completed",
     "message": "Fetched weather forecast — Temp: 28.5°C | Wind: 18.2 km/h.",
     "thought": "Fetched weather forecast — Temp: 28.5°C | Wind: 18.2 km/h.",
     "icon": "🌤️",
     "label": "Open-Meteo Weather Collector",
     "summary": {"temperature": 28.5, "wind_speed": 18.2},
     "path": "DEEP"
   }
   ```

3. **`artifact`**:
   ```json
   event: artifact
   data: {
     "artifact": {
       "id": "route_map_18.92_72.83",
       "type": "route_map",
       "title": "A* Marine Route: Mumbai to Goa Port Outer",
       "data": { ... }
     }
   }
   ```

4. **`response`**:
   ```json
   event: response
   data: {"content": "Marine conditions along the route from Mumbai to Goa are MODERATE...", "incremental": true}
   ```

5. **`done`**:
   ```json
   event: done
   data: {
     "conversation_id": "conv-123",
     "thread_id": "conv-123",
     "response": "Final synthesized report...",
     "artifacts": [ ... ],
     "route_path": "DEEP",
     "detected_language": "en",
     "intent": "navigation",
     "risk_level": "MODERATE",
     "risk_score": 45,
     "confidence_score": 0.92,
     "gate_decision": "PASS",
     "node_trace": [ ... ],
     "location": { ... }
   }
   ```

6. **`error`**:
   ```json
   event: error
   data: {"error": "Graph execution error: Connection timed out"}
   ```

---

## 5. Artifact Contract

10 UI artifact categories are currently produced by `tools/artifact_factory.py`:

| Artifact Type | Schema Title | Primary Data Contents |
| :--- | :--- | :--- |
| `location_card` | Location Overview | `name`, `latitude`, `longitude`, `country`, `admin1` |
| `weather_card` | Weather Forecast | `current`, `daily`, `hourly` (24h bounded), `units`, `provenance` |
| `ocean_card` | Ocean Hydrodynamics | `observations` (SST, currents, salinity, waves), `provenance` |
| `marine_conditions` | Wave Dynamics | `current` (wave_height, swell_period, wave_direction) |
| `pfz_map` | Potential Fishing Zone | `pfz_status`, `candidates`, `thermal_fronts`, `chlorophyll_features`, `bulletin`, `provenance` |
| `risk_summary` | Marine Risk Score | `overall_status`, `risk_level`, `risk_score`, `reasons`, `evaluated_parameters`, `disclaimer` |
| `tide_card` | Tide Dynamics | `current_sea_level_m`, `trend`, `phase`, `extrema`, `provenance` |
| `hazard_alert` | Coastal Hazard Advisories | `status`, `active_count`, `alerts`, `bulletin_source`, `provenance` |
| `geofence_alert` | Geofence & Boundary | `inside_restricted_zone`, `proximity_warning`, `matched_zones`, `verification`, `provenance` |
| `route_map` | A* Marine Route Map | `status`, `origin`, `destination`, `distance_km`, `estimated_cost`, `geojson`, `waypoints`, `segment_metrics`, `verification`, `provenance` |

---

## 6. Evidence / Provenance Contract

Every data collector emits standardized `EvidenceRecord` metadata into `state["evidence"]`. Frontends can expose an expandable **Data Provenance & Scientific Evidence** drawer.

### Evidence Item Schema
```json
{
  "source_id": "weather_open_meteo",
  "provider": "Open-Meteo",
  "dataset": "Global Weather Forecast API",
  "source_type": "API",
  "authority_class": "FORECAST",
  "data_class": "FORECAST",
  "status": "AVAILABLE",
  "retrieved_at": "2026-09-21T22:45:00+00:00",
  "forecast_time": "2026-09-21T23:00:00+00:00",
  "freshness": {
    "age_minutes": 15.0,
    "freshness_status": "FRESH",
    "ref_timestamp": "2026-09-21T22:45:00+00:00"
  },
  "attribution": "Open-Meteo (CC BY 4.0)",
  "license_type": "CC BY 4.0",
  "limitations": ["Modelled forecast data, not real-time physical weather station reading"]
}
```

---

## 7. Session & Conversation UX Contract

- **Anonymous Sessions**: Supported out of the box (UUIDs generated automatically when `conversation_id` is omitted).
- **Multi-Turn Context**: Supported via persistent `SqliteSaver` checkpointer and `ConversationStore`.
- **Conversation List**: `GET /conversations` returns lightweight summaries (`conversation_id`, `title`, `created_at`, `updated_at`).
- **Conversation Detail**: `GET /conversations/{id}` returns message history turns, active location context, rolling summary, and associated UI artifacts.

---

## 8. CORS Configuration

### Current Backend Configuration (`api/samudra_api.py`)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **Local Dev Compatibility**: Fully compatible with Vite/React (`http://localhost:5173`), Next.js (`http://localhost:3000`), or Flutter Web (`http://localhost:8080`).

---

## 9. Frontend Dependencies Required

For building Phase 3 Web Dashboard:
- **Core Framework**: React 18+ / Vite (or vanilla HTML5/JS if lightweight single-page app).
- **Mapping**: Leaflet 1.9+ or Mapbox GL JS (with GeoJSON layer support for route lines, EEZ polygons, and PFZ markers).
- **SSE Client**: Standard EventSource API or `fetch-event-source` library.
- **Icons**: Lucide React or FontAwesome icons.

---

## 10. Backend Gaps Blocking Phase 3
**NONE**. There are no blocking backend gaps preventing Phase 3 UI development.

---

## 11. Backend Gaps That Can Be Deferred

1. **Top-level `evidence` in `ChatResponse` model**: Currently `evidence` records are stored in `state["evidence"]` and embedded inside artifacts (`data["provenance"]`). Exposing `evidence` and `evidence_summary` directly on top-level `ChatResponse` Pydantic model can be added if frontend requires a global evidence list outside artifacts.
2. **WebSocket Support**: SSE is fully functional and sufficient for agent thinking streams. WebSockets are deferred to Phase 5.

---

## 12. Recommended Phase 3 Implementation Order

1. **Milestone 3.1 — Base App & Layout**: Modern ChatGPT-like dark-mode UI with collapsible sidebar conversation history, main chat view, and header.
2. **Milestone 3.2 — SSE Agent Thinking Stream**: Render live agent execution steps (`icon`, `label`, `thought`, `progress`) as LangGraph nodes execute.
3. **Milestone 3.3 — Dynamic Artifact Renderer**: Interactive cards for weather, ocean hydrodynamics, tide dynamics, risk summaries, and hazard warnings.
4. **Milestone 3.4 — Interactive Leaflet Map Integration**: Render GeoJSON route lines, PFZ candidate markers, and EEZ boundary polygons on an embedded Leaflet map view.
5. **Milestone 3.5 — Expandable Evidence Drawer**: Render expandable data provenance tabs displaying dataset freshness, provider attributions, and unmapped layer notices (`UNAVAILABLE`).

---

## 13. Example API Request & Response Payloads

### POST /chat Request
```json
{
  "message": "Plan a safe marine route from Mumbai to Goa and check weather conditions",
  "conversation_id": "conv-mumbai-goa-001"
}
```

### POST /chat Response
```json
{
  "conversation_id": "conv-mumbai-goa-001",
  "thread_id": "conv-mumbai-goa-001",
  "response": "The recommended marine route from Mumbai to Goa Port Outer spans approximately 485 km...",
  "artifacts": [
    {
      "id": "route_map_18.92_72.83",
      "type": "route_map",
      "title": "A* Marine Route: Mumbai to Goa Port Outer",
      "description": "Deterministic A* marine transit route with multi-factor environmental edge costs.",
      "data": {
        "status": "OK",
        "distance_km": 485.2,
        "estimated_cost": 542.1,
        "geojson": {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [[72.83, 18.92], [72.80, 18.75], [73.80, 15.49]]
          }
        }
      }
    }
  ],
  "route_path": "DEEP",
  "detected_language": "en",
  "intent": "navigation",
  "risk_level": "MODERATE",
  "risk_score": 42,
  "confidence_score": 0.95,
  "gate_decision": "PASS",
  "node_trace": ["intent_router", "planner", "location_resolver", "data_route", "risk_assessment", "synthesizer", "translate_out"],
  "errors": []
}
```

---

## 14. Final Readiness Assessment

- **Backend Readiness**: **100% READY**
- **Test Baseline**: **136 passed, 1 warning, 0 failures**
- **Working Tree State**: **CLEAN / UNCOMMITTED (READ-ONLY AUDIT)**
- **Phase 3 Recommendation**: Proceed immediately to **Phase 3.1 UI Development**.
