"""
state/schema.py
───────────────
Central LangGraph state for SAMUDRA.AI.

Every node reads from and writes to this TypedDict.
All keys are optional so nodes can be added or skipped
without breaking the graph.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from typing_extensions import TypedDict, Annotated
import operator


# ── Enumerations ──────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    SAFETY       = "safety"        # Is it safe to go to sea?
    FISHERY      = "fishery"       # PFZ, best fishing zones
    WEATHER      = "weather"       # Weather / cyclone / lightning
    NAVIGATION   = "navigation"    # Route optimisation, safe path
    OCEAN        = "ocean"         # SST, currents, waves, tides
    GEOSPATIAL   = "geospatial"    # Boundary, geofence, MPA queries
    GENERAL      = "general"       # Catch-all / multi-domain


class ArtifactType(str, Enum):
    MAP                = "map"
    PFZ_MAP            = "pfz_map"
    WEATHER_CARD       = "weather_card"
    MARINE_CONDITIONS  = "marine_conditions"
    OCEAN_CARD         = "ocean_card"
    RISK_SUMMARY       = "risk_summary"
    ROUTE_MAP          = "route_map"
    CHART              = "chart"
    DATA_TABLE         = "data_table"
    GEOFENCE_ALERT     = "geofence_alert"
    ADVISORY           = "advisory"
    LOCATION_CARD      = "location_card"
    TIDE_CARD          = "tide_card"
    HAZARD_ALERT       = "hazard_alert"


class RiskLevel(str, Enum):
    LOW       = "LOW"
    MODERATE  = "MODERATE"
    HIGH      = "HIGH"
    VERY_HIGH = "VERY HIGH"
    UNKNOWN   = "UNKNOWN"


class ActiveContext(TypedDict, total=False):
    location: Optional[dict[str, Any]]        # Last resolved location {name, latitude, longitude, status}
    time_request: Optional[str]               # Last requested timeframe ("now", "tomorrow morning", etc.)
    forecast_days: Optional[int]              # Last requested forecast days
    topic: Optional[str]                      # Active domain topic ("pfz", "weather", "ocean", "safety")
    selected_entity: Optional[dict[str, Any]] # Entity referenced in previous turn (e.g. PFZ candidates)
    active_artifacts: Optional[list[dict[str, Any]]] # Persistent list of artifacts generated in conversation
    selected_artifact: Optional[dict[str, Any]]      # Specific artifact active in current turn


# ── Main state ────────────────────────────────────────────────────────────────

class SamudraState(TypedDict, total=False):

    # ── 1. Raw user input & Conversation Identity ─────────────────────────────
    conversation_id: str             # Public conversation identifier
    thread_id: str                   # Internal LangGraph thread identifier
    user_query: str                  # Original text from user for current turn
    messages: Annotated[
        list[dict[str, Any]],
        operator.add                 # Append structured message turns: [{role, content, timestamp}]
    ]
    conversation_history: Annotated[
        list[dict],
        operator.add                 # Append across turns (backward compatibility)
    ]
    active_context: ActiveContext     # Persistent active context across conversation turns
    context_summary: Optional[str]   # Persistent rolling summary of older conversation turns
    route_path: str                  # Execution path taken: "FAST" | "DEEP"
    artifacts: Annotated[
        list[dict[str, Any]],
        operator.add                 # Accumulate UI rendering artifacts generated during turn
    ]

    # ── 2. Language layer ─────────────────────────────────────────────────────
    detected_language: str           # ISO 639-1 code e.g. "ta", "en", "hi"
    query_in_english: str            # translated query (or same as user_query)

    # ── 3. Intent & plan ─────────────────────────────────────────────────────
    intent: IntentType               # classified intent
    plan: dict[str, Any]             # structured plan from planner node
    # plan shape:
    # {
    #   "intent": str,
    #   "location_text": str,
    #   "coordinates_provided": bool,
    #   "latitude": float | None,
    #   "longitude": float | None,
    #   "time_request": str,         # "now" | "tomorrow" | "next 3 days" etc.
    #   "forecast_days": int,
    #   "domains_needed": list[str], # ["ocean","weather","fishery","geofence"]
    #   "needs_safety": bool,
    #   "needs_fishery": bool,
    #   "needs_navigation": bool,
    # }

    # ── 4. Location resolution ────────────────────────────────────────────────
    location: dict[str, Any]
    # shape: { status, name, latitude, longitude, country, admin1, source }

    # ── 5. Raw evidence (parallel data collection) ────────────────────────────
    ocean_data:    dict[str, Any]    # Copernicus Marine snapshot
    weather_data:  dict[str, Any]    # Open-Meteo forecast
    marine_data:   dict[str, Any]    # Open-Meteo Marine (MODELLED waves/currents/SST/sea-level)
    geofence_data: dict[str, Any]    # Geofence / MPA check
    fishery_data:  dict[str, Any]    # PFZ heuristic / INCOIS
    tide_data:     dict[str, Any]    # Phase 2.4 Tide dynamics
    hazard_data:   dict[str, Any]    # Phase 2.4 Official hazard alert feed
    route_data:    dict[str, Any]    # Phase 2.6 Marine route intelligence

    # ── Phase 2.7 Evidence & Provenance Collection ───────────────────────────
    evidence: Annotated[
        list[dict[str, Any]],
        operator.add                 # Safely merge evidence records from parallel data collectors
    ]
    evidence_summary: dict[str, Any] # Aggregated evidence completeness report


    # ── 6. Anti-hallucination gate ────────────────────────────────────────────
    confidence_score: float          # 0.0 – 1.0
    gate_decision: str               # "PASS" | "RECHECK" | "BLOCKED"
    gate_reasons: list[str]          # what the gate found
    recheck_domains: list[str]       # domains to re-fetch if RECHECK
    recheck_count: int               # loop guard (max 2)

    # ── 7. Specialist reasoning (parallel) ───────────────────────────────────
    ocean_reasoning:   str
    weather_reasoning: str
    fishery_reasoning: str
    safety_reasoning:  str

    # ── 8. Deterministic risk ─────────────────────────────────────────────────
    risk_assessment: dict[str, Any]
    # shape from marine_risk.calculate_marine_risk:
    # { risk_level, risk_score, reasons, evaluated_parameters }

    # ── 9. Synthesis ─────────────────────────────────────────────────────────
    final_response_english: str      # synthesised answer in English

    # ── 10. Output translation ────────────────────────────────────────────────
    final_response: str              # translated back to user's language

    # ── 11. Errors & metadata ─────────────────────────────────────────────────
    errors: Annotated[
        list[str],
        operator.add                 # accumulate errors from any node
    ]
    node_trace: Annotated[
        list[str],
        operator.add                 # track which nodes fired
    ]
