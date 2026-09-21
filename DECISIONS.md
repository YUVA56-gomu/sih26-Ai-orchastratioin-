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

---

### ADR-014: Phase 2.3 PFZ & Fishery Intelligence Integration
* **Status**: ACCEPTED
* **Context**: Potential Fishing Zone (PFZ) intelligence must not rely on single-point SST threshold heuristics or hallucinated LLM scores. It requires spatial grid sampling, numerical front gradient analysis, ocean productivity features, multi-factor deterministic candidate scoring, explicit data classification/provenance tracking, and structured official bulletin alignment.
* **Decision**: Integrate Copernicus BGC Chlorophyll-a (`cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m`, variable `chl` in $\text{mg/m}^3$, classified as `MODEL_ANALYSIS`). Spatial grid sampling (`tools/copernicus_grid.py`) extracts bounded grids ($\pm 0.5^\circ$) for SST (0.083° resolution) and Chlorophyll (0.25° resolution). Numerical front detection (`tools/pfz_fronts.py`) computes 2D spatial gradients ($\nabla \text{SST}$ in $^\circ\text{C/km}$ and $\nabla \text{CHL}$ in $\text{mg/m}^3\text{/km}$) using `numpy.gradient` with physical km scaling adjusted for latitude ($\Delta\text{lon} \times 111.0 \times \cos(\text{lat})$). Multi-factor scoring (`tools/pfz_scoring.py`) combines SST suitability ($26^\circ\text{C} - 29^\circ\text{C}$ Gaussian envelope), SST front strength ($\ge 0.05^\circ\text{C/km}$), Chlorophyll level, Chlorophyll gradient, and distance into a 0.0–1.0 decision-support score. Official INCOIS bulletin integration (`tools/incois_bulletin.py`) provides standardized schema with safe `UNAVAILABLE` fallback when live feeds are inactive. Enriched `pfz_map` artifacts (`tools/artifact_factory.py`) bundle candidate coordinates, thermal fronts, productivity features, bulletin status, and provenance records. Legacy `find_nearest_pfz()` is preserved as a compatible wrapper.

---

### ADR-015: Phase 2.4 Tide Dynamics & Hazard Alert Feeds Integration
* **Status**: ACCEPTED
* **Context**: Tidal dynamics and official hazard alerts (IMD, INCOIS) are critical for coastal marine safety. Modelled sea-level height data must never be claimed as authoritative tide-gauge reading or nautical chart datum, and official hazard warnings must never be fabricated if live feeds are unreachable or unconfigured.
* **Decision**: Implement `tools/tide_service.py` consuming Open-Meteo Marine 48-hour sea-level timeseries (`sea_level_height_msl`) to numerically detect local High/Low tide extrema (`extract_tide_extrema`), current sea level, trend (`RISING`/`FALLING`), phase (`FLOODING`/`EBBING`), and tidal range with explicit MSL model disclaimers (`data_class: "MODELLED"`). Implement `tools/hazard_service.py` to parse structured official hazard bulletins (`CYCLONE`, `HIGH_WAVE`, `SWELL_SURGE`, `TSUNAMI`, `GALE_WIND`, `COASTAL_FLOOD` across `ADVISORY`, `WATCH`, `WARNING`, `SEVERE_WARNING`) with default safe fallback (`status: "UNAVAILABLE"`, `data_class: "UNAVAILABLE"`) when unconfigured. Update `tools/marine_risk.py` to evaluate high-tide wave superposition ($\ge 2.0$ m wave during high tide $\rightarrow +15$ pts), extreme tidal range ($\ge 2.5$ m $\rightarrow +10$ pts), and active official warnings ($+20$ to $+50$ pts). Integrate `tide_hazard_data_node` into parallel LangGraph collection and expose structured `tide_card` and `hazard_alert` UI artifacts.

---

### ADR-016: Phase 2.5 Hybrid GIS Spatial Engine & Provenance Architecture
* **Status**: ACCEPTED
* **Context**: Geofence checks must not rely on demo circle heuristics or LLM spatial guessing. Spatial polygon containment and boundary distances must be evaluated deterministically in Python. Furthermore, because official vector GIS datasets for Indian military/naval defense zones are not publicly published, the system must handle missing defense GIS data safely (`status: "UNAVAILABLE"`) without fabricating military polygons or assigning false risk penalties.
* **Decision**: Implement a pure Python deterministic GIS spatial engine (`tools/gis_service.py`) using raycasting point-in-polygon containment (`point_in_polygon`), Haversine boundary distance calculations (`distance_to_geometry_boundary_km`), and bounding-box pre-filtering (`bounding_box_contains`). Ingest Flanders Marine Institute (VLIZ) Marine Regions Indian EEZ boundary dataset (`data/gis/eez_india.geojson`) under CC-BY 4.0 (`data_class: "INFORMATIONAL_GIS"`, `authority_class: "RESEARCH_INSTITUTION"`). Standardize 3-tier provenance tracking across layers (`status`, `data_class`, `authority_class`). Provide explicit safe fallback (`status: "UNAVAILABLE"`, `data_class: "UNAVAILABLE"`, `authority_class: "OFFICIAL_GOVERNMENT_REQUIRED"`) for military/naval restricted areas without creating fake polygons. Update `tools/marine_risk.py` to evaluate spatial geofence penalties (+50 inside, +15 proximity buffer). Expose structured `geofence_alert` UI artifacts (`tools/artifact_factory.py`) bundling matched zones, boundary distances, and provenance metadata.

---

### ADR-017: Phase 2.6 Marine Route Intelligence & Safety Optimizer Architecture
* **Status**: ACCEPTED
* **Context**: Marine route optimization must be weather- and wave-aware, avoid restricted boundary zones, and remain strictly deterministic. The LLM must NEVER calculate waypoint coordinates, distances, bearings, or route geometry. Missing dataset layers (such as Marine Protected Areas and Naval Restricted Zones) must be explicitly reported as `UNAVAILABLE` without claiming routes are cleared of military or environmental restrictions.
* **Decision**: Implement a pure Python deterministic spatial route engine (`tools/route_service.py`) operating over a documented maritime waypoint network (27 Indian coastal and offshore transit nodes). Route search uses deterministic A* graph search with admissible Haversine distance heuristic $h(n)$. Candidate edge costs are evaluated using an inspectable multi-factor formula: $\text{Cost}(e) = d_{\text{Haversine}} \times (1.0 + C_{\text{wind}} + C_{\text{wave}} + C_{\text{curr}} + C_{\text{tide}} + C_{\text{hazard}} + C_{\text{spatial}})$. Wind cost accounts for headwind/crosswind/gusts; wave cost accounts for significant wave height and steep wave periods; ocean current cost computes vector dot products (assisting current reduces cost up to $-0.25$, opposing current increases cost); hazard cost accounts for active advisories; spatial cost blocks restricted zones ($\infty$) and penalizes boundary proximity buffer (+15%). EEZ membership adds 0 risk penalty. Implement `evaluate_route_risk()` in `tools/marine_risk.py` to evaluate structured route safety. Register `fetch_route_data` node in `graph/nodes/data_route.py` and wire `route_data_collector` into `graph/graph.py` parallel fan-out/fan-in execution. Expose `route_map` UI artifacts (`tools/artifact_factory.py`) containing GeoJSON LineString route lines, segment metrics, data completeness map, verification status (`eez: "INFORMATIONAL"`, `mpa: "UNAVAILABLE"`, `naval: "UNAVAILABLE"`), and explicit safety disclaimers.
