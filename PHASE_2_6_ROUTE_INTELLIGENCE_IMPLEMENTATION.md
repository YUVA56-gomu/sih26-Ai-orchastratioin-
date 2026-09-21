# PHASE 2.6 — MARINE ROUTE INTELLIGENCE IMPLEMENTATION

This document serves as the authoritative technical record for **Phase 2.6 — Marine Route Intelligence & Safety Optimizer** in SAMUDRA AI.

---

## 1. Objective

Phase 2.6 implements a deterministic decision-support route planning engine capable of computing safe maritime paths between an origin and destination across Indian coastal and offshore waters.

### Key Principles Enforced:
* **Deterministic Geometry & Graph Search**: All waypoint selections, path coordinates, segment distances, bearings, and edge costs originate exclusively from deterministic Python code (`tools/route_service.py`).
* **LLM Non-Hallucination**: The LLM never invents route coordinates, waypoints, restricted zones, distances, or environmental measurements.
* **EEZ Non-Restriction Semantics**: Marine Regions EEZ membership is treated as `INFORMATIONAL_GIS` / `RESEARCH_INSTITUTION` context. Being inside the EEZ adds **0 risk penalty points** and does not block routes.
* **Explicit Missing Data Handling**: Unmapped Marine Protected Area (MPA) and Naval/Defence restriction layers return `status = UNAVAILABLE` (`verification: {"mpa": "UNAVAILABLE", "naval": "UNAVAILABLE"}`). SAMUDRA AI never assumes missing data means safe waters or absence of restrictions.

---

## 2. Architecture

```text
                    Origin & Destination Coordinates
                                  │
                                  ▼
                        Dynamic Graph Attacher
             (Links endpoints to maritime waypoint network)
                                  │
                                  ▼
                      Deterministic A* Engine
             (Heuristic h(n) = Haversine distance to dest)
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   Weather Inputs           Ocean Hydrodynamics       Spatial Geofences
(Wind speed/dir/gusts)     (Waves & Ocean Currents)  (EEZ & Geofence math)
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  ▼
                   Inspectable Edge Cost Evaluator
      (Distance × [1 + Wind + Wave + Current + Tide + Hazard + Spatial])
                                  │
                                  ▼
                       Route Risk Evaluator
              (evaluate_route_risk in marine_risk.py)
                                  │
                                  ▼
                         route_map Artifact
            (Typed UI JSON payload with GeoJSON LineString)
```

---

## 3. Data Sources

| Data Source | Provider | Data Class | Purpose in Phase 2.6 | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Open-Meteo Weather API** | Open-Meteo | `FORECAST` | Atmospheric wind speed, wind direction, gusts, visibility | Modelled atmospheric forecast (~11 km grid) |
| **Copernicus Marine (CMEMS)** | Copernicus | `MODELLED` | Surface & profile ocean current velocity (`uo`, `vo`), wave height (`VHM0`), wave period (`VTM02`), wave direction (`VMDR`) | Modelled hydrodynamic snapshot |
| **Open-Meteo Marine API** | Open-Meteo Marine | `MODELLED` | Marine wave dynamics & modelled sea-level height (`sea_level_height_msl`) | Modelled MSL datum, non-nautical almanac |
| **Tide Dynamics Service** | Open-Meteo / SAMUDRA | `MODELLED` | Hourly sea-level extrema & tidal phase (`FLOODING` / `EBBING`) | Modelled tidal model, not authoritative tide-gauge |
| **Hazard Alert Service** | INCOIS / IMD | `OFFICIAL_BULLETIN` | Active weather advisories, cyclone warnings, high wave alerts | Structure returns `UNAVAILABLE` when live feeds unconfigured |
| **Indian EEZ Layer** | VLIZ Marine Regions v12 | `INFORMATIONAL_GIS` | Geographic location context & EEZ membership identification | `RESEARCH_INSTITUTION` classification; non-navigation-authoritative |

---

## 4. Missing Data & Data Gap Boundaries

The following spatial layers are intentionally classified as **UNAVAILABLE**:

```json
{
  "verification": {
    "eez": "INFORMATIONAL",
    "mpa": "UNAVAILABLE",
    "naval": "UNAVAILABLE"
  }
}
```

* **Marine Protected Areas (MPA)**: `status = UNAVAILABLE`. No open vector polygon dataset for Indian MPAs is loaded. SAMUDRA AI does NOT fabricate MPA polygons or assume open waters are free of MPAs.
* **Naval / Defence Restrictions**: `status = UNAVAILABLE`. Military restricted zones are not publicly published as vector GIS layers. SAMUDRA AI does NOT fabricate military geometry, firing zones, or naval boundaries.
* **Data Policy Enforcement**: Missing dataset $\neq$ safe condition. Route responses explicitly state that verification against military restricted areas and local MPAs is incomplete and advise mariners to consult active NHO NAVAREA VIII notices.

---

## 5. Safety Model & Claim Boundaries

### What SAMUDRA AI Claims:
* Deterministic calculation of candidate marine route geometry and waypoints over documented maritime transit graphs.
* Multi-factor edge cost optimization factoring in distance, wind vector alignment, significant wave height, ocean current assistance/resistance, tide phase, active hazard advisories, and EEZ boundary context.
* Transparency of data completeness, provenance, and spatial layer disclaimers.

### What SAMUDRA AI Deliberately Does NOT Claim:
* SAMUDRA AI does **NOT** claim that calculated routes are officially cleared for navigation by maritime authorities.
* SAMUDRA AI does **NOT** claim that absence of hazard alerts or GIS polygons guarantees absence of real-world hazards, reefs, shallow bathymetry, or military exercises.
* SAMUDRA AI does **NOT** replace official nautical almanacs, hydrographic charts, or NHO NAVAREA VIII notices.

---

## 6. Algorithms & Formulations

### A. Great Circle Haversine Distance
$$d = 2 R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
where $R = 6371.0$ km.

### B. Compass Bearing Calculation
$$\theta = \text{atan2}\left(\sin(\Delta \lambda)\cos(\phi_2), \cos(\phi_1)\sin(\phi_2) - \sin(\phi_1)\cos(\phi_2)\cos(\Delta \lambda)\right)$$
Normalized to $0^\circ \le \theta < 360^\circ$.

### C. A* Graph Search
* **Cost Function**: $f(n) = g(n) + h(n)$
* **Admissible Heuristic**: $h(n) = \text{haversine\_distance\_km}(n, \text{destination})$
* **Path Reconstruction**: Dynamic endpoint attachment linking origin and destination to nearest maritime waypoints.

### D. Multi-Factor Edge Cost Function
$$\text{Cost}(e) = d_{uv} \times \left(1.0 + C_{\text{wind}} + C_{\text{wave}} + C_{\text{curr}} + C_{\text{tide}} + C_{\text{hazard}} + C_{\text{spatial}}\right)$$
* **Wind Cost ($C_{\text{wind}}$)**: Headwind ($\theta \approx 180^\circ$ relative to wind) adds penalty proportional to wind speed; gusts $> 40$ km/h add $+0.2$.
* **Wave Cost ($C_{\text{wave}}$)**: Penalty proportional to significant wave height $H_s$; steep waves ($H_s \ge 2.0$m, $T_p \le 5.0$s) add $+0.25$.
* **Current Cost ($C_{\text{curr}}$)**: Vector dot product of vessel heading vs ocean current direction. Assisting current reduces cost up to $-0.25$; opposing current increases cost $+0.3 \times v_{\text{curr}}$.
* **Hazard Cost ($C_{\text{hazard}}$)**: $+0.50$ penalty if segment intersects active hazard advisory region.
* **Spatial Cost ($C_{\text{spatial}}$)**: $+0.0$ for EEZ membership; $+0.15$ for boundary proximity buffer ($\le 10$ km); $\infty$ (blocked edge) if segment mid-point falls inside a restricted zone polygon.

---

## 7. Test Results

The full automated regression suite was executed via `pytest`:

```text
================= 120 passed, 1 warning in 715.51s (0:11:55) ==================
```

* **Total Tests**: **120 passed** (108 existing baseline + 12 new Phase 2.6 tests).
* **Failures**: **0 failures**.
* **Warnings**: **1 warning** (Pydantic v1 compatibility warning on Python 3.14).

---

## 8. Files Changed

### Created Files
* [`tools/route_service.py`](file:///d:/Oscorp/sih/tools/route_service.py) — Core spatial route engine, maritime waypoint graph, & A* search.
* [`graph/nodes/data_route.py`](file:///d:/Oscorp/sih/graph/nodes/data_route.py) — LangGraph data collection node for navigation/routing queries.
* [`tests/test_route_intelligence.py`](file:///d:/Oscorp/sih/tests/test_route_intelligence.py) — Comprehensive unit & integration test suite.
* [`PHASE_2_6_ROUTE_INTELLIGENCE_IMPLEMENTATION.md`](file:///d:/Oscorp/sih/PHASE_2_6_ROUTE_INTELLIGENCE_IMPLEMENTATION.md) — Authoritative Phase 2.6 implementation record.

### Modified Files
* [`state/schema.py`](file:///d:/Oscorp/sih/state/schema.py) — Added `route_data` dictionary key to `SamudraState`.
* [`tools/marine_risk.py`](file:///d:/Oscorp/sih/tools/marine_risk.py) — Added `evaluate_route_risk()` route risk evaluation helper.
* [`tools/artifact_factory.py`](file:///d:/Oscorp/sih/tools/artifact_factory.py) — Added `create_route_map_artifact()` helper.
* [`graph/nodes/translate_out.py`](file:///d:/Oscorp/sih/graph/nodes/translate_out.py) — Added `route_map` artifact emission logic.
* [`graph/graph.py`](file:///d:/Oscorp/sih/graph/graph.py) — Wired `route_data_collector` node into parallel fan-out/fan-in graph execution.

---

## 9. Known Limitations

1. **Graph Resolution**: The maritime waypoint network uses 27 representative coastal and offshore nodes for Indian waters; local harbor maneuver routing requires higher resolution bathymetric meshes.
2. **Bathymetry & Water Depth**: High-resolution depth bathymetry is not yet integrated; routing assumes open offshore waters or established coastal channels.
3. **Vessel Dynamics**: Cost function assumes standard medium-sized coastal vessel (10–12 knots); vessel-specific hydrodynamic polar curves are planned for Phase 6.

---

## 10. Future Improvements

1. Integration of official Indian Navy / MoEFCC GIS vector polygon layers when publicly available.
2. Dynamic bathymetric depth mesh filtering to prevent routing across shallow shoals or coral reefs.
3. Real-time vessel AIS integration and vessel-specific fuel/speed optimization curves.
