# SAMUDRA.AI — Architecture & Developer Guide

**Branch:** `langgraph-core`
**Stack:** LangGraph · LangChain · FastAPI · Python 3.11+

---

## What Was Built

SAMUDRA.AI is an **Agentic AI Marine Intelligence Platform** built for Smart India Hackathon 2026.

The `langgraph-core` branch replaces the previous Google ADK-based orchestration with a
full **LangGraph StateGraph** pipeline. Every step of the reasoning process is an explicit,
inspectable, independently-testable node. There are no hidden agent loops or magic routing —
every edge in the graph is declared.

---

## How to Run

### 1. Clone & switch to the branch

```bash
git clone https://github.com/pixelcrisscross/sih.git
cd sih
git checkout langgraph-core
```

### 2. Set up environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | What it does |
|---|---|
| `LLM_PROVIDER` | `gemini` / `groq` / `ollama` |
| `GOOGLE_API_KEY` | Gemini API key (if provider=gemini) |
| `GROQ_API_KEY` | Groq API key (if provider=groq) |
| `OLLAMA_BASE_URL` | Ollama server URL (if provider=ollama) |
| `COPERNICUSMARINE_SERVICE_USERNAME` | Copernicus Marine account |
| `COPERNICUSMARINE_SERVICE_PASSWORD` | Copernicus Marine password |

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Local Ollama setup

```bash
# Install Ollama from https://ollama.com
ollama pull qwen3:8b
# Set LLM_PROVIDER=ollama in .env
```

### 5. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Test it

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Is it safe to fish near Visakhapatnam tomorrow?", "thread_id": "fisherman-001"}'

# Same thread, follow-up (multi-turn memory)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What about the day after?", "thread_id": "fisherman-001"}'

# With explicit coordinates
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Where is the nearest PFZ?", "latitude": 17.68, "longitude": 83.21, "thread_id": "boat-42"}'

# View graph structure (for visualization / debugging)
curl http://localhost:8000/graph/schema
```

### 7. Interactive API docs

```
http://localhost:8000/docs
```

---

## Orchestration Model

```
                        ┌─────────────────────────────────────────────────────┐
                        │               USER QUERY (any language)             │
                        └───────────────────────┬─────────────────────────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │  language_detection   │
                                    │  Detect lang + translate to English     │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │    intent_router      │
                                    │  safety / fishery /   │
                                    │  weather / navigation │
                                    │  ocean / geospatial   │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │       planner         │
                                    │  Decompose query →    │
                                    │  domains_needed,      │
                                    │  forecast_days,       │
                                    │  location_text, etc.  │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │   location_resolver   │
                                    │  Place name → lat/lon │
                                    │  (Open-Meteo Geocode) │
                                    └──┬──┬──┬──┬───────────┘
                                       │  │  │  │
                          ─────────────┘  │  │  └─────────────
                         │                │  │                │
               ┌─────────▼──────┐  ┌──────▼──┴───┐  ┌───────▼────────┐  ┌────────▼───────┐
               │  ocean_data    │  │ weather_data │  │ fishery_data   │  │ geofence_data  │
               │  Copernicus    │  │ Open-Meteo   │  │ PFZ heuristic  │  │ MPA / EEZ      │
               │  SST/waves/    │  │ wind/rain/   │  │ INCOIS stub    │  │ boundary check │
               │  currents      │  │ cyclone code │  │                │  │                │
               └────────┬───────┘  └──────┬───────┘  └───────┬────────┘  └────────┬───────┘
                        │                 │                   │                    │
                        └────────┬────────┘                   └──────────┬─────────┘
                                 │                                        │
                                 └────────────────┬───────────────────────┘
                                                  │
                                   ┌──────────────▼──────────────┐
                                   │   anti_hallucination_gate   │
                                   │  Cross-validate all sources │
                                   │  Confidence score 0.0-1.0   │
                                   └──────────────┬──────────────┘
                                                  │
                          ┌───────────────────────┼──────────────────────┐
                          │                       │                      │
                    RECHECK (loop)              PASS                  BLOCKED
                    max 2 times                  │                      │
                          │                      │                      │
                          │         ┌────────────▼──────────┐           │
                          │         │    risk_assessment    │           │
                          │         │  Deterministic scorer │           │
                          │         │  0-100, LOW/MOD/HIGH  │           │
                          │         │  (no LLM, rules-based)│           │
                          │         └──┬──┬──┬──┬───────────┘           │
                          │            │  │  │  │                       │
                    ──────┘   ─────────┘  │  │  └─────────              │
                             │            │  │          │               │
                   ┌─────────▼─────┐ ┌────▼──┴──┐ ┌────▼──────┐ ┌──────▼──────┐
                   │ ocean_reasoner│ │ weather_ │ │ fishery_  │ │ safety_     │
                   │ SST/waves     │ │ reasoner │ │ reasoner  │ │ reasoner    │
                   │ interpretation│ │ wind/rain│ │ PFZ/front │ │ operational │
                   │               │ │ cyclone  │ │ upwelling │ │ risk assess │
                   └───────┬───────┘ └────┬─────┘ └────┬──────┘ └──────┬──────┘
                           │              │             │               │
                           └──────────────┼─────────────┘               │
                                          └──────────────────────────────┘
                                                         │
                                          ┌──────────────▼──────────────┐
                                          │        synthesizer          │
                                          │  Evidence + reasoning →     │
                                          │  explainable response       │
                                          │  with source attribution    │
                                          └──────────────┬──────────────┘
                                                         │
                                          ┌──────────────▼──────────────┐
                                          │       translate_out         │
                                          │  English → user's language  │
                                          │  hi/ta/te/ml/kn/bn/mr/gu…   │
                                          └──────────────┬──────────────┘
                                                         │
                                          ┌──────────────▼──────────────┐
                                          │   RESPONSE TO USER          │
                                          │   text + risk_level +       │
                                          │   confidence + node_trace   │
                                          └─────────────────────────────┘
```

### Anti-Hallucination Gate — decision logic

```
gate_decision = PASS    → continue to risk + reasoning (normal flow)
gate_decision = RECHECK → re-fetch only flagged domains (max 2 loops)
gate_decision = BLOCKED → skip reasoning, go straight to synthesizer
                          (synthesizer explains what is missing)
```

### Multi-turn memory

Every conversation has a `thread_id`. The `MemorySaver` checkpointer persists state
between calls on the same thread, enabling follow-up questions without re-stating context.

---

## Project Structure

```
sih/
├── main.py                      ← uvicorn entry point
├── requirements.txt
├── .env.example
│
├── graph/
│   ├── graph.py                 ← StateGraph definition (edges + routing)
│   ├── llm.py                   ← LLM factory (Gemini / Groq / Ollama)
│   └── nodes/
│       ├── language.py          ← detect language, translate to English
│       ├── intent.py            ← classify query intent
│       ├── planner.py           ← decompose query into execution plan
│       ├── location.py          ← resolve place name → lat/lon
│       ├── data_ocean.py        ← fetch Copernicus Marine data
│       ├── data_weather.py      ← fetch Open-Meteo weather
│       ├── data_fishery.py      ← fetch PFZ heuristic data
│       ├── data_geofence.py     ← check geofence / MPA / EEZ
│       ├── gate.py              ← anti-hallucination gate
│       ├── risk.py              ← deterministic risk scorer
│       ├── reason_ocean.py      ← ocean specialist LLM reasoning
│       ├── reason_weather.py    ← weather specialist LLM reasoning
│       ├── reason_fishery.py    ← fishery specialist LLM reasoning
│       ├── reason_safety.py     ← safety specialist LLM reasoning
│       ├── synthesizer.py       ← final response synthesis
│       └── translate_out.py     ← translate response to user language
│
├── state/
│   └── schema.py                ← SamudraState TypedDict (shared state)
│
├── prompts/
│   └── system_prompts.py        ← all LLM system prompts (tune here)
│
├── api/
│   ├── samudra_api.py           ← FastAPI routes
│   └── models.py                ← Pydantic request/response models
│
└── tools/                       ← pure Python data fetchers (no LLM)
    ├── copernicus_service.py    ← SST, waves, currents
    ├── weather_service.py       ← Open-Meteo forecast
    ├── pfz_service.py           ← PFZ heuristic
    ├── geofence.py              ← zone boundary check
    ├── marine_risk.py           ← risk scoring rules
    └── location.py              ← geocoding
```

---

## Is This Enough for the Problem Statement?

### What is fully covered

| PS Requirement | Status |
|---|---|
| Natural language query understanding | ✅ intent_router + planner |
| Multi-turn contextual conversation | ✅ MemorySaver thread_id |
| Autonomous planning & task decomposition | ✅ planner node |
| Multiple specialized AI agents | ✅ 4 parallel reasoning agents |
| Ocean data (SST, waves, currents) | ✅ Copernicus Marine |
| Weather / storm / cyclone data | ✅ Open-Meteo |
| Fishery / PFZ information | ⚠️ Heuristic only (see gaps below) |
| Geofence / boundary alerts | ⚠️ Demo zones (see gaps below) |
| Risk assessment with explanation | ✅ Deterministic scorer + safety reasoner |
| Explainable evidence-based responses | ✅ Synthesizer with provenance |
| Indian regional language support | ✅ 11 languages via translate nodes |
| Anti-hallucination / cross-validation | ✅ Gate node with RECHECK loop |
| Source attribution | ✅ Every tool tags its source |
| FastAPI backend for web/mobile | ✅ /chat, /health, /graph/schema |

---

## Gaps — What Needs to Be Added

### 1. Real PFZ Data (HIGH priority)
**Current:** SST heuristic guessing fishing zones near the user's location.
**What's needed:** Live INCOIS PFZ bulletin API.
- INCOIS provides daily PFZ advisories at `https://incois.gov.in/portal/datainfo/pfz.jsp`
- They have a REST API (registration required): contact incois.gov.in
- Alternative: scrape the daily PDF/image bulletin and parse it

```
tools/incois_pfz.py   ← replace pfz_service.py with real INCOIS API call
```

### 2. Real Geofence Boundaries (HIGH priority)
**Current:** One hard-coded demo zone near Visakhapatnam.
**What's needed:**
- **EEZ boundaries** — India's Exclusive Economic Zone (200nm)
- **International Maritime Boundary Line (IMBL)**
- **Marine Protected Areas (MPAs)**
- **Ecologically Sensitive Zones**

**Data sources (all free):**
- Marine Regions: `https://www.marineregions.org/downloads.php` (GeoJSON/Shapefile)
- India MPA: `https://india.wdpa.io/` (WDPA database)
- Load these as GeoJSON and do point-in-polygon checks with `shapely`

```
tools/geofence.py     ← replace demo zones with shapely + real GeoJSON
```

### 3. Tide Data (MEDIUM priority)
**Current:** Not fetched at all.
**What's needed:** Tide predictions for fishing safety and port operations.
- **INCOIS Tidal Data API**: `https://incois.gov.in/portal/datainfo/tide.jsp`
- **Open-Meteo Marine API** (`marine.open-meteo.com`) — already partially used in pfz_service,
  also provides `ocean_current_velocity`, `wave_direction`, `sea_level` (tide proxy)

```
tools/tide_service.py       ← new node
graph/nodes/data_tide.py    ← new data node
```

### 4. Cyclone / Active Alert Feed (MEDIUM priority)
**Current:** Weather codes from Open-Meteo catch heavy weather but no named alerts.
**What's needed:** Real-time cyclone track data and official IMD warnings.
- **IMD RSS feeds**: `https://mausam.imd.gov.in/`
- **RSMC New Delhi cyclone advisories**: available as XML/RSS
- **NOAA JTWC**: `https://www.metoc.navy.mil/jtwc/jtwc.html`

```
tools/cyclone_alerts.py     ← poll IMD RSS, parse active warnings
graph/nodes/data_alerts.py  ← new parallel data node
```

### 5. In-Situ Buoy Data (LOW-MEDIUM priority)
**Current:** Not integrated.
**What's needed:** Real-time sea conditions from INCOIS buoys.
- INCOIS ARGO float data and moored buoy network
- `https://incois.gov.in/portal/datainfo/drb.jsp`
- Adds validation for the anti-hallucination gate (compare Copernicus model vs buoy observation)

### 6. Route Optimisation / A* Navigation (MEDIUM priority)
**Current:** Not implemented (in your architecture diagram but not yet in this branch).
**What's needed:**
- A grid of navigational hazard scores (built from wave + wind + geofence data)
- A* or Dijkstra pathfinding over that grid
- Return: safest route as a list of lat/lon waypoints

```
tools/navigation.py          ← A* over risk grid
graph/nodes/navigation.py   ← called when intent=navigation
```

### 7. WebSocket Streaming (LOW priority for core, HIGH for UX)
**Current:** REST endpoint returns after full graph execution (~5-15 seconds).
**What's needed:** Stream node-by-node progress to the frontend so the user sees activity.
- LangGraph supports `astream_events()` — add a `/chat/stream` WebSocket endpoint
- Each node completion fires an event the frontend can display

### 8. MOSDAC / ISRO Satellite Data (NICE TO HAVE)
**Current:** Only Copernicus Marine (European).
**What's needed for full PS coverage:**
- **MOSDAC (ISRO)**: `https://mosdac.gov.in/` — OCM-3 chlorophyll, INSAT-3D cloud/rain
- **NOAA CoastWatch**: SST from MODIS/VIIRS — higher resolution near-coast
- These require account registration but are free for research

---

## Recommended Next Steps (Priority Order)

1. **Register INCOIS API** → replace `pfz_service.py` with real PFZ data
2. **Download Marine Regions GeoJSON** → replace demo geofence with real EEZ/MPA boundaries
3. **Add tide node** → Open-Meteo Marine API (already in requirements, zero extra cost)
4. **Add cyclone alert node** → IMD RSS (free, 15-minute polling)
5. **Add WebSocket streaming** → frontend UX (LangGraph `astream_events`)
6. **Add A* navigation node** → route optimisation for vessel planning queries
7. **Register MOSDAC** → ISRO satellite data for Indian Ocean coverage

---

## API Reference

### POST /chat

```json
// Request
{
  "query": "Is it safe to venture into the sea tomorrow near Chennai?",
  "thread_id": "session-123",
  "latitude": null,
  "longitude": null
}

// Response
{
  "response": "Based on forecast data for Chennai...",
  "detected_language": "en",
  "intent": "safety",
  "risk_level": "MODERATE",
  "risk_score": 42,
  "confidence_score": 0.85,
  "gate_decision": "PASS",
  "node_trace": ["language_detection", "intent_router", "planner", ...],
  "errors": [],
  "location": {"status": "FOUND", "name": "Chennai", "latitude": 13.08, "longitude": 80.27},
  "thread_id": "session-123"
}
```

### GET /health
Returns `{"status": "ok", "service": "SAMUDRA.AI", "version": "1.0.0-langgraph"}`

### GET /graph/schema
Returns node and edge list for frontend graph visualization.
