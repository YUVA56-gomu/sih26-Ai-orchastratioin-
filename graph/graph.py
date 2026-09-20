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
  summarizer (conditional rolling context management)
       │
  translate_out
       │
  END
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state.schema import SamudraState, IntentType
from graph.nodes.language import language_detection_node
from graph.nodes.intent import intent_router_node
from graph.nodes.fast_responder import fast_responder_node
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
from graph.nodes.summarizer import summarizer_node
from graph.nodes.translate_out import translate_out_node


# ── Conditional edge: Fast / Deep Router ────────────────────────────────────

def route_fast_or_deep(state: SamudraState) -> str:
    """
    Decide whether query executes via FAST ⚡ path or DEEP 🧠 path.
    Returns: "fast" | "deep"
    Conservative default: "deep"
    """
    raw_query = state.get("user_query", "")
    query = state.get("query_in_english") or raw_query
    lower_q = query.lower().strip().rstrip("?.!")
    intent = state.get("intent", IntentType.GENERAL)

    # DEEP CRITERIA (Safety, Navigation, Risk, Multi-domain, Recommendations, Route, Complex Reasoning)
    if intent in (IntentType.SAFETY, IntentType.NAVIGATION):
        return "deep"

    safety_risk_keywords = [
        "safe", "safety", "risk", "hazard", "warning", "caution",
        "can i go", "can we go", "should i go", "is it safe", "able to fish",
        "route", "path", "navigate", "navigation", "avoid",
        "nearest pfz", "best zone", "which zone", "which spot", "recommend",
        "why", "how does it affect", "compare", "decline", "cause"
    ]
    if any(kw in lower_q for kw in safety_risk_keywords):
        return "deep"

    # Multi-condition temporal requests with action
    if any(t in lower_q for t in ["tomorrow", "next 3 days", "forecast"]):
        if any(w in lower_q for w in ["go", "fish", "fishing", "sail", "voyage"]):
            return "deep"

    # FAST CRITERIA
    greetings = {"hi", "hello", "hey", "good morning", "good evening", "good day", "greetings", "namaste"}
    identity = {"who are you", "what can you do", "how can you help", "what is samudra", "who made you"}
    chitchat = {"thanks", "thank you", "okay", "ok", "got it", "goodbye", "bye", "cool", "great"}

    if lower_q in greetings or lower_q in identity or lower_q in chitchat:
        return "fast"
    if any(lower_q.startswith(g) for g in ["hi ", "hello ", "hey ", "thanks"]):
        return "fast"

    # Simple definitions ("what is pfz", "what is sst", "what is wave height", "explain chlorophyll")
    if any(lower_q.startswith(prefix) for prefix in ["what is ", "what are ", "explain ", "tell me about ", "define "]):
        return "fast"

    # Simple single-tool inquiries ("what is the weather near karwar?", "what are the waves near karwar?", "what is the sst near karwar?")
    single_tool_keywords = ["weather", "wind", "waves", "wave", "sst", "temperature"]
    if any(kw in lower_q for kw in single_tool_keywords) and not any(kw in lower_q for kw in ["safe", "safety", "recommend", "best", "which", "should"]):
        return "fast"

    # Conservative default
    return "deep"


# ── Conditional edge: gate decision ──────────────────────────────────────────

def route_after_gate(state: SamudraState) -> str:
    """
    After the anti-hallucination gate:
    - RECHECK  → go back to parallel data collection for re-fetch
    - PASS     → proceed to risk + reasoning
    - BLOCKED  → skip reasoning, go straight to synthesis
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
    g.add_node("fast_responder",           fast_responder_node)
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

    # ── Final synthesis, summarization & translation ──────────────────────────
    g.add_node("synthesizer",              synthesizer_node)
    g.add_node("summarizer",               summarizer_node)
    g.add_node("translate_out",            translate_out_node)

    # ── Edges: sequential head & Fast/Deep router ──────────────────────────────
    g.add_edge(START,                "language_detection")
    g.add_edge("language_detection", "intent_router")

    # Fast/Deep router decision
    g.add_conditional_edges(
        "intent_router",
        route_fast_or_deep,
        {
            "fast": "fast_responder",
            "deep": "planner",
        }
    )

    # Fast Path -> Summarizer -> Translate Out
    g.add_edge("fast_responder",     "summarizer")

    # Deep Path -> Location Resolver -> ...
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

    # ── Final: synthesizer → summarizer → translate → END ──────────────────────
    g.add_edge("synthesizer",        "summarizer")
    g.add_edge("summarizer",         "translate_out")
    g.add_edge("translate_out",      END)

    return g


# ── Compiled singleton with persistent SQLite checkpointer ────────────────────
# SqliteSaver enables durable multi-turn conversation memory surviving restarts.

_compiled = None
_saver = None


def get_compiled_graph(db_path: str = "samudra_storage.db"):
    """Return the compiled graph with persistent SqliteSaver checkpointer."""
    global _compiled, _saver
    if _compiled is None or (_saver and getattr(_saver, "db_path", None) != db_path):
        if _saver is not None:
            try:
                _saver.close()
            except Exception:
                pass
        from storage.sqlite_saver import SqliteSaver
        _saver = SqliteSaver(db_path=db_path)
        _compiled = build_graph().compile(checkpointer=_saver)
    return _compiled
