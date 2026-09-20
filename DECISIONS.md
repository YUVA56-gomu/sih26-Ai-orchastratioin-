# DECISIONS.md — SAMUDRA AI Architectural Decision Records (ADRs)

This document records the foundational architectural decisions governing the SAMUDRA AI platform.

---

### ADR-001: Evolve Existing Codebase
* **Status**: ACCEPTED
* **Context**: SAMUDRA AI has an existing working foundation including LangGraph orchestration, FastAPI backend, Copernicus integrations, Open-Meteo services, deterministic risk scoring, and web frontend.
* **Decision**: We will evolve and refactor the existing codebase incrementally across controlled milestone phases rather than discarding or rewriting from scratch.

---

### ADR-002: Conversation as Central Product Abstraction
* **Status**: ACCEPTED
* **Context**: Marine workflows often require multi-turn exploration (e.g. asking for weather, then nearest fishing zone, then safety for tomorrow).
* **Decision**: The entire user experience centers around a single conversational interface ("ChatGPT for the Ocean"). Users do not navigate isolated single-purpose tool pages; conversation drives tool and artifact selection.

---

### ADR-003: Text and Voice Share Unified Conversation Engine
* **Status**: ACCEPTED
* **Context**: Voice interaction should not feel like an isolated IVR system or separate AI brain.
* **Decision**: Text and Voice input pipelines feed directly into the same Conversation Engine, sharing conversation state, context memory, tools, reasoning nodes, and evidence protocols.

---

### ADR-004: Unified Backend for Web and Flutter Clients
* **Status**: ACCEPTED
* **Context**: Web and mobile apps require identical intelligence, safety scoring, and data layers.
* **Decision**: Web and Flutter clients act purely as presentation layers. All business logic, marine intelligence, agent orchestration, and artifact generation reside in the backend Conversation API.

---

### ADR-005: Fast Path for Simple Queries
* **Status**: ACCEPTED
* **Context**: Trivial queries (e.g. *"What is the SST at 15°N, 73°E?"*) do not require multi-agent planning or parallel domain gathering.
* **Decision**: Simple queries bypass full multi-agent graph fan-out via a Fast Path, invoking direct tool execution for sub-second responses.

---

### ADR-006: Deep Path for Complex Agentic Workflows
* **Status**: ACCEPTED
* **Context**: Multi-domain inquiries involving safety, fishing, weather, and geofencing require structured planning and multi-agent evidence correlation.
* **Decision**: Complex queries use a Deep Path with dynamic planning, parallel data collection, safety gate validation, and multi-agent reasoning.

---

### ADR-007: Deterministic Calculations Handled by Code
* **Status**: ACCEPTED
* **Context**: LLMs can produce inconsistent or inaccurate numerical calculations (e.g. Haversine distance, geofence radius checks, risk scoring).
* **Decision**: All calculations, geometric intersections, distance metrics, and safety threshold checks are performed deterministically in Python code. LLMs interpret and explain these deterministic outputs.

---

### ADR-008: Explicit Provenance and Data Classification
* **Status**: ACCEPTED
* **Context**: Mixing satellite observations, numerical models, prototype heuristics, and demo geometry without distinction creates safety hazards.
* **Decision**: Every data payload must explicitly declare its provenance class: `OBSERVED`, `MODELLED`, `FORECAST`, `HEURISTIC`, or `DEMO`. Heuristic or demo data must never be claimed as official or authoritative.

---

### ADR-009: Structured Conversation Artifacts
* **Status**: ACCEPTED
* **Context**: Conversational text alone cannot effectively convey geospatial maps, PFZ overlays, or multi-day parameter charts.
* **Decision**: Responses bundle natural language text alongside structured `Artifact` JSON objects (`map`, `pfz_map`, `weather_card`, `risk_summary`, `route_map`) rendered dynamically by frontends.

---

### ADR-010: AI Agents as Implementation Workers
* **Status**: ACCEPTED
* **Context**: AI coding agents operating on the repository must follow strict architectural constraints.
* **Decision**: AI coding agents must strictly obey the repository constitution (`AGENTS.md`, `ARCHITECTURE.md`, `CURRENT_STATE.md`, `DECISIONS.md`). Agents are forbidden from independently redesigning system architecture without explicit user instructions.

---

### ADR-011: Normalized SSE Streaming Protocol
* **Status**: ACCEPTED
* **Context**: Real-time agent thought streaming and incremental response rendering must be decoupled from internal framework implementations (e.g. LangGraph) so client applications (Web, Flutter) consume a stable contract.
* **Decision**: SSE streaming (`/chat/stream`) emits a normalized event schema (`start`, `node`, `response`, `artifact`, `done`, `error`) with JSON payloads. Streaming preserves conversation state, checkpoints to SQLite, and maintains context summarization compatibility without duplicating graph logic.

---

### ADR-012: Enhanced Weather Service Coverage & Provenance
* **Status**: ACCEPTED
* **Context**: Atmospheric forecasting requires multi-day daily summaries, hourly timeseries, peak wind gust risk detection, and explicit provenance tracking to prevent hallucination and misattribution.
* **Decision**: The weather service (`tools/weather_service.py`) expands Open-Meteo coverage to include `current` (10 parameters), `hourly` (14 parameters), `daily` (15 parameters), unit dictionaries, and explicit UTC ISO-8601 provenance metadata (`source`, `provider`, `data_class: "FORECAST"`, `retrieved_at`). `weather_card` artifacts bundle daily forecast arrays, bounded 24-hour hourly windows, unit dictionaries, and provenance metadata.

---

### ADR-013: Phase 2.2 Ocean Hydrodynamics Integration
* **Status**: ACCEPTED
* **Context**: Comprehensive ocean hydrodynamics intelligence requires sea-water salinity (`so`), multi-depth current velocity profiles (`uo`, `vo` at 0.49m, 9.57m, 21.6m, 51.9m), structured ocean artifacts (`ocean_card`), deterministic current/wave risk scoring, and anti-hallucinated specialist reasoning.
* **Decision**: Copernicus Marine integration (`tools/copernicus_service.py`) expands parallel parameter retrieval to 5 tasks (`temperature`, `salinity`, `currents`, `current_profile`, `waves`). `get_salinity()` consumes CMEMS dataset `cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m`. `get_current_profile()` performs robust nearest-depth selection over target coordinates without assuming exact dataset levels. The deterministic risk engine (`tools/marine_risk.py`) adds strong current ($\ge 1.5$ m/s) and steep wave ($VHM0 \ge 1.5$ m AND $VTM02 \le 5.0$ s) rules. The specialist ocean reasoner formats full hydrodynamics evidence up to 2500 characters. Standardized `ocean_card` artifacts bundle location, temperature, salinity, currents, wave spectrum, and provenance metadata.
