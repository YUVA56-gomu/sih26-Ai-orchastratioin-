# CURRENT_STATE.md — SAMUDRA AI System State Audit

This document describes the exact implementation status of the SAMUDRA AI repository as of today.

---

## 1. SUBSYSTEM AUDIT SUMMARY

| Subsystem | Classification | Implementation Details & File Location |
| :--- | :--- | :--- |
| **Backend** | `IMPLEMENTED` | FastAPI app in [api/samudra_api.py](file:///d:/Oscorp/sih/api/samudra_api.py) providing REST (`/chat`, `/conversations`), metadata endpoints, and SSE streaming. |
| **Graph / Orchestration** | `IMPLEMENTED` | LangGraph compiled graph in [graph/graph.py](file:///d:/Oscorp/sih/graph/graph.py) with Fast/Deep routing, fan-out data collection, anti-hallucination gate loop, deterministic risk engine, and parallel specialist reasoners. |
| **State** | `IMPLEMENTED` | Central `SamudraState` TypedDict in [state/schema.py](file:///d:/Oscorp/sih/state/schema.py) with typed accumulators (`node_trace`, `errors`, `conversation_history`, `active_context`, `artifacts`, `route_path`). |
| **LLM** | `IMPLEMENTED` / `PROTOTYPE` | Factory in [graph/llm.py](file:///d:/Oscorp/sih/graph/llm.py) supporting `gemini`, `groq`, `ollama` with a zero-dependency fallback mock `FallbackMockLLM`. |
| **Intent Classification** | `IMPLEMENTED` | LLM node in [graph/nodes/intent.py](file:///d:/Oscorp/sih/graph/nodes/intent.py) classifying queries into `safety`, `fishery`, `weather`, `navigation`, `ocean`, `geospatial`, `general`. |
| **Fast / Deep Router** | `IMPLEMENTED` | Fast/Deep router in [graph/nodes/router.py](file:///d:/Oscorp/sih/graph/nodes/router.py) routing simple queries fast and complex queries to Deep intelligence pipeline. |
| **Planning** | `IMPLEMENTED` | LLM node in [graph/nodes/planner.py](file:///d:/Oscorp/sih/graph/nodes/planner.py) executed conditionally on Deep Path. |
| **Location Resolution** | `IMPLEMENTED` | Node in [graph/nodes/location.py](file:///d:/Oscorp/sih/graph/nodes/location.py) calling Open-Meteo Geocoding API via [tools/location.py](file:///d:/Oscorp/sih/tools/location.py) with active location context retention and replacement. |
| **Marine Data (Ocean Hydrodynamics)** | `IMPLEMENTED` (Phase 2.2) | Copernicus Marine API in [tools/copernicus_service.py](file:///d:/Oscorp/sih/tools/copernicus_service.py) providing SST (`thetao`), sea-water salinity (`so`), surface and multi-depth current velocity profiles (`uo`, `vo` at 0.49m, 9.57m, 21.6m, 51.9m), and wave dynamics (`VHM0`, `VTM02`, `VMDR`). Open-Meteo Marine API in [tools/marine_service.py](file:///d:/Oscorp/sih/tools/marine_service.py). |
| **Weather Data** | `IMPLEMENTED` (Phase 2.1) | Enhanced Open-Meteo Weather API integration in [tools/weather_service.py](file:///d:/Oscorp/sih/tools/weather_service.py) with current, hourly (14 variables), daily (15 variables) forecast coverage, UTC ISO-8601 provenance metadata, wind-gust risk scoring, and enriched `weather_card` artifacts. |
| **PFZ (Potential Fishing Zone)** | `IMPLEMENTED` (Phase 2.3) | Multi-factor spatial intelligence engine in [tools/pfz_service.py](file:///d:/Oscorp/sih/tools/pfz_service.py) integrating Copernicus BGC Chlorophyll-a (`chl` in `cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m`), SST (`thetao`), spatial gradient thermal front detection (`tools/pfz_fronts.py`), ocean productivity analysis, deterministic multi-factor scoring (`tools/pfz_scoring.py`), INCOIS/MOSDAC bulletin alignment structure (`tools/incois_bulletin.py`), and enriched `pfz_map` artifacts. |
| **Tide & Hazard Feeds** | `IMPLEMENTED` (Phase 2.4) | Hourly sea-level timeseries extrema detection (`extract_tide_extrema`), tidal phase (`FLOODING`/`EBBING`) & trend, MSL datum model disclaimers in [tools/tide_service.py](file:///d:/Oscorp/sih/tools/tide_service.py), standardized official hazard advisory parser & safe `UNAVAILABLE` fallback in [tools/hazard_service.py](file:///d:/Oscorp/sih/tools/hazard_service.py), tide-wave superposition & active warning penalties in [tools/marine_risk.py](file:///d:/Oscorp/sih/tools/marine_risk.py), parallel data collector [graph/nodes/data_tide_hazard.py](file:///d:/Oscorp/sih/graph/nodes/data_tide_hazard.py), and typed `tide_card` & `hazard_alert` UI artifacts. |
| **Geofencing / Spatial Engine** | `IMPLEMENTED` (Phase 2.5) | Pure Python deterministic spatial engine in [tools/gis_service.py](file:///d:/Oscorp/sih/tools/gis_service.py) with raycasting point-in-polygon containment, Haversine boundary distance calculations, bounding box pre-filtering, Marine Regions EEZ layer ([data/gis/eez_india.geojson](file:///d:/Oscorp/sih/data/gis/eez_india.geojson)), 3-tier provenance tracking (`status`, `data_class`, `authority_class`), explicit `UNAVAILABLE` fallback for unmapped military defense zones, and typed `geofence_alert` UI artifacts. |
| **Marine Route Intelligence** | `IMPLEMENTED` (Phase 2.6) | Deterministic A* spatial route engine in [tools/route_service.py](file:///d:/Oscorp/sih/tools/route_service.py) operating over a documented Indian maritime waypoint graph with multi-factor environmental edge cost evaluation (wind, waves, ocean currents, tides, hazards, and geofence boundaries), route risk evaluation in [tools/marine_risk.py](file:///d:/Oscorp/sih/tools/marine_risk.py), data collector [graph/nodes/data_route.py](file:///d:/Oscorp/sih/graph/nodes/data_route.py), and typed `route_map` UI artifacts. |
| **Evidence & Provenance Layer** | `IMPLEMENTED` (Phase 2.7) | Standardized evidence and data provenance engine in [tools/evidence_service.py](file:///d:/Oscorp/sih/tools/evidence_service.py) providing `EvidenceRecord` metadata, source classification (`AuthorityClass`, `DataClass`), deterministic freshness age calculation (`FRESH`, `RECENT`, `STALE`), completeness score aggregation (`aggregate_evidence`), race-condition free LangGraph state evidence merging via `operator.add`, explicit `UNAVAILABLE` evidence reporting for unmapped layers (MPA, Naval/Defence), and artifact evidence attachment. |
| **Risk Assessment** | `IMPLEMENTED` | Deterministic marine risk engine in [tools/marine_risk.py](file:///d:/Oscorp/sih/tools/marine_risk.py) computing 0–100 risk score and level (`LOW`, `MODERATE`, `HIGH`, `VERY HIGH`) with wind gust, strong ocean current ($\ge 1.5$ m/s), steep wave, high-tide wave superposition, official hazard advisory sensitivity, spatial geofence boundary penalties (+50 inside, +15 proximity), and route risk evaluation (`evaluate_route_risk`). |
| **Specialist Reasoning** | `IMPLEMENTED` | Parallel LLM nodes in [graph/nodes/reason_*.py](file:///d:/Oscorp/sih/graph/nodes/) for ocean, weather, fishery, and marine safety (with tide dynamics, hazard warnings, spatial geofence evidence, and route metrics). |
| **Synthesis** | `IMPLEMENTED` | LLM node in [graph/nodes/synthesizer.py](file:///d:/Oscorp/sih/graph/nodes/synthesizer.py) synthesizing evidence into a unified English report. |
| **Translation** | `IMPLEMENTED` | LLM node in [graph/nodes/translate_out.py](file:///d:/Oscorp/sih/graph/nodes/translate_out.py) outputting final response in detected user language. |
| **Artifact Protocol** | `IMPLEMENTED` | Artifact schema in [state/schema.py](file:///d:/Oscorp/sih/state/schema.py) and factory helpers in [tools/artifact_factory.py](file:///d:/Oscorp/sih/tools/artifact_factory.py) producing typed UI artifacts (`location_card`, `weather_card`, `ocean_card`, `pfz_map`, `marine_conditions`, `risk_summary`, `tide_card`, `hazard_alert`, `geofence_alert`, `route_map`). |
| **Database / Persistence** | `IMPLEMENTED` (M1.5) | Local SQLite persistence in [storage/sqlite_saver.py](file:///d:/Oscorp/sih/storage/sqlite_saver.py) and metadata management in [storage/conversation_store.py](file:///d:/Oscorp/sih/storage/conversation_store.py). Survives process restarts. |
| **Conversation Memory** | `IMPLEMENTED` (Durable) | Multi-turn conversation context resolution, reference resolution ("there", "which one", "tomorrow"), active location context tracking, artifact retention/selection, and isolated thread memory via persistent `SqliteSaver`. |
| **Context Management** | `IMPLEMENTED` (M1.6) | Threshold-triggered rolling context summarization in [graph/nodes/summarizer.py](file:///d:/Oscorp/sih/graph/nodes/summarizer.py) maintaining persistent `context_summary` alongside a bounded window of recent raw turns (`messages`), preventing token ballooning across 10+ turn conversations. |
| **Web Interface** | `PROTOTYPE` | [web/index.html](file:///d:/Oscorp/sih/web/index.html) single-page HTML/JS dashboard with Leaflet map, agent thinking stream viewer, and query box. |
| **Flutter Application** | `MISSING` | No Flutter codebase exists in repository. |
| **Voice Interface** | `MISSING` | No Speech-to-Text (STT) or Text-to-Speech (TTS) components exist. |
| **Authentication** | `MISSING` | No user registration, login, anonymous session tokens, or account migration exist. |
| **Streaming** | `IMPLEMENTED` (M1.7) | Standardized Server-Sent Events (SSE) streaming pipeline via `GET /chat/stream` and `POST /chat/stream` emitting normalized events (`start`, `node`, `response`, `artifact`, `done`, `error`). Fully compatible with persistence and context summarization. |
| **Tests** | `IMPLEMENTED` | Comprehensive automated test suite in [tests/](file:///d:/Oscorp/sih/tests/) (136 passed) covering Marine integrations, Conversation Core, Router, Artifact Protocol, Persistent Storage, Context Summarization, Streaming Pipeline, Weather Integration, Ocean Hydrodynamics, PFZ Intelligence, Tide & Hazard Feeds, GIS Spatial Engine, Marine Route Intelligence, and Evidence & Provenance. |



---

## 2. ACTIVE DATA SOURCES

1. **Copernicus Marine Data Service (CMEMS)**: Real satellite/modelled SST (`thetao`), Chlorophyll-a (`chl`), salinity (`so`), currents (`uo`, `vo`), and wave dynamics (`VHM0`, `VTM02`, `VMDR`).
2. **Open-Meteo Weather API**: Free public endpoint for atmospheric temperature, wind speed/direction, precipitation, pressure, visibility.
3. **Open-Meteo Marine API**: Free public endpoint for modelled wave, swell, current velocity, SST, and hourly sea-level timeseries (`sea_level_height_msl`).
4. **Open-Meteo Geocoding API**: Free public endpoint for place name -> coordinate resolution.
5. **INCOIS / MOSDAC / IMD Bulletin Structure**: Standardized official hazard warning parser (`OFFICIAL_BULLETIN`) with default `UNAVAILABLE` fallback when live feeds are unconfigured.

---

## 3. KNOWN LIMITATIONS & ARCHITECTURAL GAPS

1. **Geofence Simplification**: Geofencing relies on static demo circle geometry.
2. **Database Engine**: Current storage uses local SQLite checkpointer (`samudra_storage.db`) suitable for local development/single node deployment. PostgreSQL/Redis support planned for future production scale.
3. **Authentication & User Association**: Conversations are currently indexed by `conversation_id` without user account authentication.
