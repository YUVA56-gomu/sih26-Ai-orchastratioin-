# PHASE 2.6 — MARINE ROUTE INTELLIGENCE ARCHITECTURAL AUDIT

This document provides a comprehensive, read-only architectural audit for **Phase 2.6 — Marine Route Intelligence** in SAMUDRA AI. It evaluates existing codebase components, data sources, spatial capabilities, algorithmic suitability, safety contracts, data availability, and implementation readiness.

---

## 1. Current Routing Capabilities

Currently, SAMUDRA AI has **NO spatial marine pathfinding or route calculation engine**.

* **Intent Routing vs. Spatial Routing**: References to `route_path` in [`graph/nodes/router.py`](file:///d:/Oscorp/sih/graph/nodes/router.py) and [`state/schema.py`](file:///d:/Oscorp/sih/state/schema.py) refer exclusively to the **Fast/Deep Intent Router** (M1.3), which determines whether a conversational turn bypasses or invokes full multi-node LangGraph execution (`FAST` vs `DEEP`).
* **Point-to-Point Distance**: Point-to-point and point-to-segment Haversine distance functions exist in [`tools/gis_service.py`](file:///d:/Oscorp/sih/tools/gis_service.py) (`haversine_distance_km`, `distance_to_segment_km`), but no path graph or sequence of waypoints is computed.
* **Navigation Intent Handling**: Intent classification in [`graph/nodes/intent.py`](file:///d:/Oscorp/sih/graph/nodes/intent.py) recognizes `IntentType.NAVIGATION` ("navigation", route optimization, safe path), but currently routes to general marine safety reasoners without invoking a spatial route engine.

---

## 2. Existing Relevant Files

| File | Purpose / Role | Relevant Functions / Constructs |
| :--- | :--- | :--- |
| [`tools/gis_service.py`](file:///d:/Oscorp/sih/tools/gis_service.py) | Deterministic GIS Spatial Engine | `haversine_distance_km`, `distance_to_segment_km`, `point_in_polygon`, `bounding_box_contains`, `check_geofence` |
| [`tools/marine_risk.py`](file:///d:/Oscorp/sih/tools/marine_risk.py) | Deterministic Marine Risk Engine | `calculate_marine_risk` (wind, wave, current, tide, hazard, geofence penalties) |
| [`tools/weather_service.py`](file:///d:/Oscorp/sih/tools/weather_service.py) | Atmospheric Forecast Client | `get_weather_conditions` (wind speed, direction, gusts, visibility) |
| [`tools/marine_service.py`](file:///d:/Oscorp/sih/tools/marine_service.py) | Marine Hydrodynamics Client | `get_marine_conditions` (waves, swell, ocean currents, SST, sea-level) |
| [`tools/copernicus_service.py`](file:///d:/Oscorp/sih/tools/copernicus_service.py) | Copernicus Hydrodynamics | Multi-depth ocean currents (`uo`, `vo`), wave dynamics (`VHM0`, `VTM02`, `VMDR`) |
| [`tools/tide_service.py`](file:///d:/Oscorp/sih/tools/tide_service.py) | Tide Dynamics Engine | `get_tide_conditions` (extrema, phase, MSL sea level) |
| [`tools/hazard_service.py`](file:///d:/Oscorp/sih/tools/hazard_service.py) | Active Hazard Feeds | `get_hazard_alerts` (INCOIS/IMD warning bulletins) |
| [`tools/artifact_factory.py`](file:///d:/Oscorp/sih/tools/artifact_factory.py) | UI Artifact Factory | Standardized artifact creators (`risk_summary`, `geofence_alert`, `weather_card`, etc.) |
| [`state/schema.py`](file:///d:/Oscorp/sih/state/schema.py) | Central LangGraph State | `ArtifactType.ROUTE_MAP`, `IntentType.NAVIGATION`, `SamudraState` |

---

## 3. Existing Environmental Inputs

SAMUDRA AI already gathers rich, deterministic environmental parameters across multiple spatial data collectors:

### A. Weather (Open-Meteo Atmospheric)
* **Wind Speed & Direction**: `wind_speed_10m` (km/h), `wind_direction_10m` (°deg).
* **Wind Gusts**: `wind_gusts_10m` (km/h).
* **Visibility & Cloud Cover**: `visibility` (m), `cloud_cover` (%).
* **Precipitation**: `precipitation` (mm), `weather_code` (WMO).
* **Forecast Horizon & Resolution**: Up to 7 days, 1-hour temporal resolution, ~11 km spatial resolution.

### B. Ocean Hydrodynamics (Copernicus Marine & Open-Meteo Marine)
* **Currents**: Surface velocity `uo`, `vo` (m/s), total speed `ocean_current_velocity` (m/s), direction `ocean_current_direction` (°deg), and multi-depth profile (0.49m, 9.57m, 21.6m, 51.9m).
* **Waves**: Significant wave height `VHM0` / `wave_height` (m), wave direction `VMDR` / `wave_direction` (°deg), wave period `VTM02` / `wave_period` (s), swell height/direction/period.
* **Sea Surface Temperature & Salinity**: SST (`thetao`, °C), Salinity (`so`, psu).
* **Data Classification**: `MODELLED` (not observed tide-gauge data).

### C. Tide Dynamics (Open-Meteo Marine & Extrema Processing)
* **Tide Extrema & Phase**: High tide, low tide, tidal range, `FLOODING` / `EBBING` phase.
* **Sea Level Height**: `sea_level_height_msl` (m, MSL datum).

### D. Hazard Advisories (INCOIS / IMD Feeds)
* **Alert Status**: `ACTIVE` advisory list or `UNAVAILABLE` fallback.
* **Severity & Affected Region**: Advisory / Warning severity and geographical scope.

---

## 4. Existing GIS Capabilities

* **Polygon Containment**: Pure Python ray-casting point-in-polygon (`point_in_polygon`, `point_in_multipolygon`).
* **Bounding Box Filtering**: Fast pre-filtering (`bounding_box_contains`).
* **Distance Math**: WGS84 Haversine spherical distance (`haversine_distance_km`), point-to-segment distance (`distance_to_segment_km`), and minimum polygon boundary distance (`distance_to_geometry_boundary_km`).
* **EEZ Spatial Layer**: Flanders Marine Institute (VLIZ) Marine Regions v12 GeoJSON boundary layer loaded at [`data/gis/eez_india.geojson`](file:///d:/Oscorp/sih/data/gis/eez_india.geojson) (Indian mainland, Lakshadweep, Andaman & Nicobar).
* **3-Tier Provenance Tracking**: `status` (`AVAILABLE` / `UNAVAILABLE`), `data_class` (`INFORMATIONAL_GIS` / `RESEARCH_INSTITUTION`), `authority_class` (`RESEARCH_INSTITUTION` / `OFFICIAL_GOVERNMENT_REQUIRED`).

---

## 5. Existing Risk Capabilities

The deterministic risk engine [`tools/marine_risk.py`](file:///d:/Oscorp/sih/tools/marine_risk.py) evaluates:
* Wind speed ($\ge 35$ km/h) & gusts ($\ge 50$ km/h).
* Ocean current speed ($\ge 1.5$ m/s).
* Wave height ($\ge 2.5$ m) & wave period ($\le 5$ s steep waves).
* High tide + wave superposition penalty (+15 pts).
* Official hazard advisories (+40 pts).
* Restricted zone polygon containment (+50 pts) & proximity buffer (+15 pts).
* EEZ membership = **0 penalty points** (geographic context only).

---

## 6. Existing Artifacts

* `ArtifactType.ROUTE_MAP` ("route_map") is registered in [`state/schema.py`](file:///d:/Oscorp/sih/state/schema.py) (line 38).
* **Gap**: No helper function `create_route_map_artifact()` currently exists in [`tools/artifact_factory.py`](file:///d:/Oscorp/sih/tools/artifact_factory.py).
* **Gap**: No node in [`graph/nodes/`](file:///d:/Oscorp/sih/graph/nodes/) currently builds or emits a `route_map` artifact.

---

## 7. Data Availability Table

| Capability / Dataset | Available | Source | Authority Class | Suitable for Routing |
| :--- | :--- | :--- | :--- | :--- |
| **Indian EEZ** | **YES** | VLIZ Marine Regions v12 | `INFORMATIONAL_GIS` / `RESEARCH_INSTITUTION` | **YES** (Geographic context only; 0 risk penalty) |
| **Marine Protected Areas (MPA)** | **NO** (`UNAVAILABLE`) | None integrated | `OFFICIAL_GOVERNMENT_REQUIRED` | **NO** (Must declare layer unavailable; cannot claim MPA avoidance) |
| **Naval / Defence Restrictions** | **NO** (`UNAVAILABLE`) | None integrated | `OFFICIAL_GOVERNMENT_REQUIRED` | **NO** (Must declare layer unavailable; cannot claim military clearance) |
| **Atmospheric Wind** | **YES** | Open-Meteo Weather API | `FORECAST` | **YES** (Headwind / crosswind / gust edge cost penalties) |
| **Wave Dynamics** | **YES** | Copernicus Marine / Open-Meteo Marine | `MODELLED` | **YES** (High wave / steep wave / beam wave edge cost penalties) |
| **Ocean Currents** | **YES** | Copernicus Marine / Open-Meteo Marine | `MODELLED` | **YES** (Current vector alignment: opposing = penalty, assisting = bonus) |
| **Tide Dynamics** | **YES** | Open-Meteo Marine (`sea_level_height_msl`) | `MODELLED` | **YES** (Coastal waypoint sea-level & tidal window checks) |
| **Hazard Advisories** | **STRUCTURED** | INCOIS / IMD Warning Feeds | `OFFICIAL_BULLETIN` | **YES** (Hazard region boundary cost multiplier when active) |

---

## 8. Missing Components

1. **Routing Service (`tools/route_service.py`)**: Deterministic spatial route engine.
2. **Waypoints & Graph Generator**: Coastal navigation graph (major Indian ports & passage waypoints) combined with local grid mesh interpolation around origin & destination.
3. **Multi-Factor Edge Cost Evaluator**: Mathematical function scoring candidate route segments based on Haversine distance, wind vector alignment, wave height/period, current vector projection, hazard advisories, and boundary proximity.
4. **Segment Containment / Raycasting Intersector**: Function testing candidate route edges against spatial boundary polygons and landmass boundaries.
5. **Route Artifact Creator (`create_route_map_artifact`)**: Function in [`tools/artifact_factory.py`](file:///d:/Oscorp/sih/tools/artifact_factory.py) serializing waypoints, total distance, ETA, weather/wave summary, risk breakdown, data gap disclaimers, and GeoJSON features.
6. **Route Data Node (`graph/nodes/data_route.py`)**: Data node executing when `intent == NAVIGATION` or `plan["needs_navigation"] == True`.
7. **Specialist Route Reasoner (`graph/nodes/reason_route.py`)**: Specialist LLM reasoner synthesizing deterministic route metrics into natural language safety guidance.

---

## 9. Recommended Route Architecture

The end-to-end pipeline MUST follow SAMUDRA AI's strict deterministic spatial architecture:

```text
User Query ("Find safe route from Mumbai to Goa")
  ↓
Location Resolver (Resolves Origin & Destination coordinates)
  ↓
Parallel Data Collectors (Weather, Ocean, Tides, Hazards, GIS)
  ↓
Deterministic GIS & Marine Route Engine (Python: A* / Waypoint Graph Search)
  ↓
Anti-Hallucination Gate (Verifies route geometry, waypoints, distance, and data gaps)
  ↓
Deterministic Marine Risk Engine (Evaluates total route safety level & score)
  ↓
Specialist Safety & Route Reasoners (Synthesizes guidance from deterministic stats)
  ↓
Translate Out / Artifact Factory (Emits route_map artifact & localized explanation)
```

**CRITICAL RULE**: The LLM must **NEVER** calculate waypoint coordinates or route geometry. All coordinates, distances, headings, and costs MUST originate from deterministic Python functions.

---

## 10. Recommended Algorithm

### Hybrid Maritime Waypoint Graph + Dynamic A* Search

* **Why Grid-only A* is insufficient**: A pure uniform 2D grid across the Indian Ocean requires high resolution (~0.05° grid = thousands of nodes) and produces jagged grid artifacts unless complex smoothing is applied.
* **Why Visibility Graph alone is insufficient**: Visibility graphs optimize for shortest distance around obstacles, but do not naturally incorporate dynamic environmental vector fields (wind, waves, currents).
* **Recommended Hybrid Architecture**:
  1. **Pre-defined Maritime Highway Graph**: Standard coastal & offshore navigation waypoints covering Indian maritime zones (Mumbai, Murud, Ratnagiri, Malvan, Goa, Karwar, Mangalore, Kannur, Kochi, Tuticorin, Chennai, Krishnapatnam, Visakhapatnam, Paradeep, Haldia, Port Blair, Male passage, Ten Degree Channel).
  2. **Dynamic Endpoint Interpolation**: Origin and Destination coordinates are dynamically linked to the nearest 3 maritime waypoints via direct line-of-sight edges.
  3. **Deterministic A* Search**: A* algorithm operates on the resulting directed graph.
  4. **Admissible Heuristic**: $h(n) = \text{haversine\_distance\_km}(n, \text{destination})$.
  5. **Edge Cost Function**:
     $$\text{Cost}(e_{uv}) = d_{uv} \times \left( 1.0 + w_{\text{wind}} \cdot C_{\text{wind}} + w_{\text{wave}} \cdot C_{\text{wave}} - w_{\text{curr}} \cdot C_{\text{curr}} + w_{\text{hazard}} \cdot C_{\text{hazard}} + w_{\text{geo}} \cdot C_{\text{geo}} \right)$$
     where:
     * $d_{uv}$: Haversine distance of segment $u \to v$ (km).
     * $C_{\text{wind}}$: Penalty for headwind / strong crosswind ($> 30$ km/h).
     * $C_{\text{wave}}$: Penalty for high significant wave height ($> 2.0$ m) or steep waves.
     * $C_{\text{curr}}$: Vector dot product of vessel heading vs. current velocity (opposing current adds cost; assisting current reduces cost).
     * $C_{\text{hazard}}$: High penalty multiplier if segment intersects active hazard advisory polygon.
     * $C_{\text{geo}}$: Infinite cost ($\infty$) if segment intersects restricted zone; buffer penalty if within 10 km buffer.

---

## 11. Safety & Anti-Hallucination Requirements

1. **Explicit Data Gap Statements**: If a dataset is `UNAVAILABLE` (e.g. Naval/Defence or MPA), the engine and LLM response MUST explicitly state:
   * *"Naval restriction GIS dataset is UNAVAILABLE; this route cannot be verified against military restricted areas. Mariners must check active NHO NAVAREA VIII notices."*
   * *"Marine Protected Area (MPA) polygon dataset is UNAVAILABLE; this route cannot be verified against local MPAs."*
2. **Never Claim Absence of Danger**: Missing dataset $\neq$ safe condition. Missing data MUST return `status = UNAVAILABLE`.
3. **No Fabricated Waypoints**: All waypoints in the `route_map` artifact must come strictly from the deterministic spatial engine output.
4. **Proximity Buffer Distinction**: 10 km proximity warnings must be explicitly identified as decision-support heuristics, not official legal boundaries.

---

## 12. Proposed Implementation Stages (For Phase 2.6)

* **Stage 1: Spatial Route Engine Core (`tools/route_service.py`)**
  * Implement maritime waypoint graph for Indian waters.
  * Implement line-segment boundary intersector & Haversine cost calculator.
  * Implement deterministic A* graph search algorithm.
* **Stage 2: Route Artifact & Factory (`tools/artifact_factory.py`)**
  * Implement `create_route_map_artifact()` supporting GeoJSON route lines, waypoints, metrics, and disclaimers.
* **Stage 3: Graph Node Integration (`graph/nodes/data_route.py` & `graph/graph.py`)**
  * Connect route data collector node into LangGraph execution pipeline.
  * Integrate route output into deterministic risk engine and specialist safety reasoner.
* **Stage 4: Automated Testing (`tests/test_route_intelligence.py`)**
  * Create unit & integration test suite (origin/destination routing, boundary avoidance, environmental penalty checks, unavailable data warnings).

---

## 13. Testing Strategy

* **Unit Tests**:
  * Verify Haversine distance & segment intersector math.
  * Verify A* graph search finds optimal path between key ports (e.g. Mumbai to Goa, Chennai to Visakhapatnam).
  * Verify opposing ocean current increases edge cost while assisting current reduces cost.
  * Verify restricted boundary intersection assigns infinite cost ($\infty$) and diverts path.
* **Integration Tests**:
  * Verify full LangGraph execution turn with user query: *"Find me a safe route from Mumbai to Goa"*.
  * Verify `route_map` artifact generation with complete provenance & disclaimers.
  * Verify missing naval/MPA data triggers explicit missing data warnings in final response.

---

## 14. Known Limitations

1. **Nautical Chart Bathymetry**: High-resolution depth bathymetry (water depth contours) is not currently integrated; routing assumes open offshore waters and standard coastal channels.
2. **Dynamic Vessel Dynamics**: Routing assumes standard medium-sized coastal vessel (10–12 knots cruising speed); vessel-specific hydrodynamic polar curves are planned for Phase 6.

---

## 15. Explicit List of Things NOT to Implement (Data Gap Boundaries)

* **DO NOT** fabricate naval restricted zones or military polygon coordinates.
* **DO NOT** fabricate Marine Protected Area (MPA) polygon boundaries.
* **DO NOT** claim routes are cleared of military restrictions or MPAs.
* **DO NOT** use LLMs to calculate waypoint coordinates or path geometry.
* **DO NOT** claim modelled sea-level data (`sea_level_height_msl`) represents official nautical chart tide tables.

---

## Summary & Recommendations

### Recommended Phase 2.6 Architecture
Deterministic Python Maritime Waypoint Graph + Dynamic A* Search, integrated into LangGraph parallel data collection, validated by Anti-Hallucination Gate and Marine Risk Engine, and rendered via `route_map` UI artifact.

### Exact Files Needing Modification
1. [`tools/artifact_factory.py`](file:///d:/Oscorp/sih/tools/artifact_factory.py) — Add `create_route_map_artifact()`.
2. [`tools/marine_risk.py`](file:///d:/Oscorp/sih/tools/marine_risk.py) — Add route risk scoring helper (`evaluate_route_risk`).
3. [`graph/nodes/translate_out.py`](file:///d:/Oscorp/sih/graph/nodes/translate_out.py) — Add `route_map` artifact emission logic.
4. [`graph/graph.py`](file:///d:/Oscorp/sih/graph/graph.py) — Wire route data node into graph routing logic.
5. [`DEVELOPMENT_ROADMAP.md`](file:///d:/Oscorp/sih/DEVELOPMENT_ROADMAP.md) — Clarify Phase 2.6 milestone title.

### Exact New Files Needing Creation
1. [`tools/route_service.py`](file:///d:/Oscorp/sih/tools/route_service.py) — Core spatial route engine & A* graph search.
2. [`graph/nodes/data_route.py`](file:///d:/Oscorp/sih/graph/nodes/data_route.py) — LangGraph data collection node for navigation/routing queries.
3. [`tests/test_route_intelligence.py`](file:///d:/Oscorp/sih/tests/test_route_intelligence.py) — Unit and integration tests for route intelligence.

### Data Dependencies
All required environmental (weather, waves, currents, tides) and spatial (EEZ GeoJSON) data sources are **already available and functional** in the repository. Naval & MPA datasets remain `UNAVAILABLE` and will be handled via explicit missing data disclaimers.

### Implementation Readiness
**READY FOR IMPLEMENTATION**. No additional external data API procurement is required prior to building Phase 2.6. The deterministic spatial engine and existing environmental feeds provide a complete foundation for Phase 2.6 Marine Route Intelligence.
