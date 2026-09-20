"""
graph/graph.py
───────────────
SAMUDRA.AI — LangGraph execution graph

Full pipeline:

  language_detection
       │
  intent_router
       │
  planner
       │
  location_resolver
       │
  ┌────┴─────────────────────────────┐
  │  parallel_data_collection        │
  │  ├── ocean_data_collector        │
  │  ├── weather_data_collector      │
  │  ├── marine_data_collector       │
  │  ├── fishery_data_collector      │
  │  └── geofence_data_collector     │
  └────┬─────────────────────────────┘
       │
  anti_hallucination_gate ──RECHECK──► [back to parallel data]
       │ PASS / BLOCKED
  risk_assessment  (deterministic, no LLM)
       │
  ┌────┴─────────────────────────────┐
  │  parallel_reasoning              │
  │  ├── ocean_reasoner              │
  │  ├── weather_reasoner            │
  │  ├── fishery_reasoner            │
  │  └── safety_reasoner            │
  └────┬─────────────────────────────┘
       │
  synthesizer
       │
  translate_out
       │
  END
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state.schema import SamudraState
from graph.nodes.language import language_detection_node
from graph.nodes.intent import intent_router_node
from graph.nodes.planner import planner_node
from graph.nodes.location import location_node
from graph.nodes.data_ocean import ocean_data_node
from graph.nodes.data_weather import weather_data_node
from graph.nodes.data_marine import marine_data_node
from graph.nodes.data_fishery import fishery_data_node
from graph.nodes.data_geofence import geofence_data_node
from graph.nodes.gate import anti_hallucination_gate_node
from graph.nodes.reason_ocean import ocean_reasoning_node
from graph.nodes.reason_weather import weather_reasoning_node
from graph.nodes.reason_fishery import fishery_reasoning_node
from graph.nodes.reason_safety import safety_reasoning_node
from graph.nodes.risk import risk_assessment_node
from graph.nodes.synthesizer import synthesizer_node
from graph.nodes.translate_out import translate_out_node


# ── Conditional edge: gate decision ──────────────────────────────────────────

def route_after_gate(state: SamudraState) -> str:
    """
    After the anti-hallucination gate:
    - RECHECK  → go back to parallel data collection for re-fetch
    - PASS     → proceed to risk + reasoning
    - BLOCKED  → skip reasoning, go straight to synthesizer
    """
    decision = state.get("gate_decision", "PASS")
    if decision == "RECHECK":
        return "recheck"
    if decision == "BLOCKED":
        return "blocked"
    return "pass"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Build and return the compiled SAMUDRA.AI LangGraph."""

    g = StateGraph(SamudraState)

    # ── Sequential pipeline ───────────────────────────────────────────────────
    g.add_node("language_detection",       language_detection_node)
    g.add_node("intent_router",            intent_router_node)
    g.add_node("planner",                  planner_node)
    g.add_node("location_resolver",        location_node)

    # ── Parallel data collection ───────────────────────────────────────────────
    g.add_node("ocean_data_collector",     ocean_data_node)
    g.add_node("weather_data_collector",   weather_data_node)
    g.add_node("marine_data_collector",    marine_data_node)
    g.add_node("fishery_data_collector",   fishery_data_node)
    g.add_node("geofence_data_collector",  geofence_data_node)

    # ── Gate ───────────────────────────────────────────────────────────────────
    g.add_node("anti_hallucination_gate",  anti_hallucination_gate_node)

    # ── Deterministic risk ─────────────────────────────────────────────────────
    g.add_node("risk_assessment",          risk_assessment_node)

    # ── Parallel specialist reasoning ──────────────────────────────────────────
    g.add_node("ocean_reasoner",           ocean_reasoning_node)
    g.add_node("weather_reasoner",         weather_reasoning_node)
    g.add_node("fishery_reasoner",         fishery_reasoning_node)
    g.add_node("safety_reasoner",          safety_reasoning_node)

    # ── Final synthesis & translation ──────────────────────────────────────────
    g.add_node("synthesizer",              synthesizer_node)
    g.add_node("translate_out",            translate_out_node)

    # ── Edges: sequential head ────────────────────────────────────────────────
    g.add_edge(START,                "language_detection")
    g.add_edge("language_detection", "intent_router")
    g.add_edge("intent_router",      "planner")
    g.add_edge("planner",            "location_resolver")

    # ── Fan-out: location → 5 parallel data collectors ────────────────────────
    g.add_edge("location_resolver",  "ocean_data_collector")
    g.add_edge("location_resolver",  "weather_data_collector")
    g.add_edge("location_resolver",  "marine_data_collector")
    g.add_edge("location_resolver",  "fishery_data_collector")
    g.add_edge("location_resolver",  "geofence_data_collector")

    # ── Fan-in: all 5 collectors → gate ───────────────────────────────────────
    g.add_edge("ocean_data_collector",    "anti_hallucination_gate")
    g.add_edge("weather_data_collector",  "anti_hallucination_gate")
    g.add_edge("marine_data_collector",   "anti_hallucination_gate")
    g.add_edge("fishery_data_collector",  "anti_hallucination_gate")
    g.add_edge("geofence_data_collector", "anti_hallucination_gate")

    # ── Conditional edge: gate decision ───────────────────────────────────────
    g.add_conditional_edges(
        "anti_hallucination_gate",
        route_after_gate,
        {
            # RECHECK: re-run only the data collectors (state already has
            # recheck_domains set by the gate; collectors check it themselves)
            "recheck":  "ocean_data_collector",

            # PASS: deterministic risk first, then parallel reasoning
            "pass":     "risk_assessment",

            # BLOCKED: skip reasoning, go straight to synthesis
            "blocked":  "synthesizer",
        },
    )

    # ── risk → fan-out to 4 parallel reasoners ─────────────────────────────────
    g.add_edge("risk_assessment",    "ocean_reasoner")
    g.add_edge("risk_assessment",    "weather_reasoner")
    g.add_edge("risk_assessment",    "fishery_reasoner")
    g.add_edge("risk_assessment",    "safety_reasoner")

    # ── Fan-in: all 4 reasoners → synthesizer ─────────────────────────────────
    g.add_edge("ocean_reasoner",     "synthesizer")
    g.add_edge("weather_reasoner",   "synthesizer")
    g.add_edge("fishery_reasoner",   "synthesizer")
    g.add_edge("safety_reasoner",    "synthesizer")

    # ── Final: synthesizer → translate → END ──────────────────────────────────
    g.add_edge("synthesizer",        "translate_out")
    g.add_edge("translate_out",      END)

    return g


# ── Compiled singleton with in-memory checkpointer ────────────────────────────
# MemorySaver enables multi-turn conversation memory via thread_id.

_compiled = None


def get_compiled_graph():
    """Return the compiled graph (singleton, thread-safe for single process)."""
    global _compiled
    if _compiled is None:
        checkpointer = MemorySaver()
        _compiled = build_graph().compile(checkpointer=checkpointer)
    return _compiled
