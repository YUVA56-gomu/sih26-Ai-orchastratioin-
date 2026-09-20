# ARCHITECTURE.md — SAMUDRA AI Target Architecture Specification

This document defines the target system architecture for SAMUDRA AI, a conversational marine intelligence platform ("ChatGPT for the Ocean").

---

## 1. TARGET SYSTEM OVERVIEW

```text
                         USER
                           │
                 ┌─────────┴─────────┐
                 │                   │
                WEB               FLUTTER
                 │                   │
                 └─────────┬─────────┘
                           │
                    Conversation API
                           │
                    Conversation Core
                           │
                  Context / Session
                           │
                    Fast / Deep Router
                       /          \
                      /            \
                   FAST            DEEP
                    │               │
                    │             Planner
                    │               │
                    │        Tool / Agent Selection
                    │               │
                    │        Parallel Execution
                    │               │
                    └───────┬───────┘
                            │
                     Evidence Layer
                            │
                     Reasoning Layer
                            │
                   Response Synthesizer
                            │
                   Artifact Generation
                            │
                ┌───────────┴───────────┐
                │                       │
              TEXT                 ARTIFACTS
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                       MAP          PFZ         CHART
                         │            │            │
                       RISK        WEATHER      ROUTE
```

---

## 2. FAST PATH ⚡ vs DEEP PATH 🧠

### 2.1 Fast Path ⚡
Designed for simple, direct queries where multi-agent planning and parallel domain gathering introduce unnecessary latency.

* **Trigger Examples**:
  * *"What is the sea surface temperature near Karwar?"*
  * *"What is the weather in Goa tomorrow?"*
  * *"What does PFZ mean?"*
* **Execution Flow**: Intent Router -> Direct Tool/Service call -> Response Synthesizer.
* **Latency Goal**: Sub-second / immediate response.

### 2.2 Deep Path 🧠
Invoked for complex requests requiring multi-dataset correlation, spatial/temporal reasoning, hazard validation, and deterministic risk evaluation.

* **Trigger Examples**:
  * *"Can I go fishing tomorrow morning near Karwar, and which nearby PFZ is safest considering weather, waves, lightning, and restricted zones?"*
* **Execution Flow**: Intent Router -> Multi-Agent Planner -> Parallel Data Collectors -> Anti-Hallucination Safety Gate -> Deterministic Risk Engine -> Parallel Specialist Reasoners -> Multi-Agent Synthesizer -> Output Translator.

---

## 3. CONVERSATION ENGINE & MULTI-TURN CONTEXT

The Conversation Engine manages active conversation memory and enables natural follow-up queries without forcing users to re-specify locations or activities:

```text
User turn: "Find PFZ near Karwar."
  ↳ Context stored: { location: "Karwar (14.81°N, 74.13°E)", topic: "PFZ" }

User turn: "Which one is closest?"
  ↳ Context resolved: "Which [PFZ] is closest [to Karwar (14.81°N, 74.13°E)]?"

User turn: "What about tomorrow morning?"
  ↳ Context resolved: "What are the marine conditions [at nearest PFZ near Karwar] on [tomorrow morning]?"
```

### 3.1 Persistent Storage Architecture (M1.5)

SAMUDRA AI uses a local durable persistence layer (`storage/`) sitting below the client layer and around the LangGraph state machine:

```text
             WEB / FLUTTER / VOICE
                       │
                       ▼
       SAMUDRA API / Conversation Engine
                       │
                conversation_id
                       │
                       ▼
         Conversation Metadata Store
         (storage/conversation_store.py)
                       │
                       ▼
        SQLite Checkpointer (SqliteSaver)
          (storage/sqlite_saver.py)
                       │
                       ▼
               LangGraph State
           /                     \
       FAST ⚡                 DEEP 🧠
           \                     /
                  Response
                     +
                 Artifacts
```

* **`SqliteSaver` Checkpointer**: Safely persists and restores LangGraph state checkpoints (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`), keeping message history, `active_context` (location, selected artifact, active artifacts), `artifacts`, and `route_path` durable across backend process restarts.
* **`ConversationStore` Repository**: Manages lightweight conversation index metadata (`conversations` table: `conversation_id`, `thread_id`, `title`, `created_at`, `updated_at`).
* **Deterministic Title Generation**: Generates clean conversation titles directly from the initial user query without incurring additional LLM latency or cost.

### 3.2 Context Management & Rolling Summarization (M1.6)

SAMUDRA AI implements threshold-triggered rolling context summarization (`graph/nodes/summarizer.py`) to prevent prompt token ballooning across long multi-turn conversations:

* **Trigger Threshold**: Summarization executes conditionally only when message history exceeds `SUMMARY_THRESHOLD_MESSAGES` (6 messages / 3 turns). Short conversations and simple Fast Path greetings below threshold execute with 0 summarization overhead.
* **Rolling Summarization**: Condenses turns prior to `RECENT_MESSAGES_WINDOW` into a persistent `context_summary` field in `SamudraState`, merging new turns into any existing summary.
* **Bounded Recent Window**: Preserves the last 4 raw messages intact alongside `context_summary` for LLM prompt context formatting.
* **`active_context` Independence**: `context_summary` focuses on conversational background and user preferences. Deterministic structured state (`location`, `latitude`, `longitude`, `time_request`, `topic`, `artifacts`) remains managed by `active_context` as the explicit source of truth.

### 3.3 Real-Time SSE Streaming Pipeline (M1.7)

SAMUDRA AI exposes a real-time Server-Sent Events (SSE) streaming architecture at `GET /chat/stream` and `POST /chat/stream` for live agent execution feedback, incremental response rendering, and immediate artifact delivery:

```text
User Request (GET / POST /chat/stream)
  │
  ├── 1. Persist Initial Conversation Metadata (ConversationStore)
  ├── 2. Emit event: start (conversation_id, thread_id, query)
  │
  ├── 3. Graph Execution via graph.astream(stream_mode="updates")
  │     ├── Node execution ──► Emit event: node (status, thought, icon, label, path, summary)
  │     ├── Artifact generated ─► Emit event: artifact (incremental structured artifact payload)
  │     └── Response snippet ──► Emit event: response (incremental natural-language chunk)
  │
  ├── 4. Touch Conversation Metadata & Checkpoint (SqliteSaver)
  │
  └── 5. Emit event: done (final response, artifacts, route_path, risk_level, context, node_trace)
```

* **Standard Event Protocol**:
  1. `start` — Emitted immediately on connection (`conversation_id`, `thread_id`, `query`).
  2. `node` — Emitted as each agent node executes (`node`, `status`, `message`, `thought`, `icon`, `label`, `summary`, `path`).
  3. `response` — Emitted when response text becomes available (`content`, `incremental`: `true`).
  4. `artifact` — Emitted incrementally as UI artifacts are generated (`artifact` payload).
  5. `done` — Emitted on turn completion with complete `ChatResponse` payload.
  6. `error` — Emitted if an unhandled exception occurs (`error` message, avoiding stack trace exposure).
* **Protocol Decoupling**: Clients consume the stream without knowledge of internal LangGraph objects.
* **Storage & Context Compatibility**: Integrates seamlessly with persistent `SqliteSaver` checkpoints and `ConversationStore` metadata.

### 3.4 Ocean Hydrodynamics Architecture (Phase 2.2)

SAMUDRA AI implements comprehensive ocean hydrodynamics data collection and risk reasoning:

* **5-Parameter Parallel Collector**: `get_copernicus_marine_snapshot()` queries 5 parameter tasks in parallel (`temperature`, `salinity`, `currents`, `current_profile`, `waves`).
* **Sea-Water Salinity (`so`)**: Fetched via `get_salinity()` from CMEMS dataset `cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m` (unit `psu`).
* **Multi-Depth Current Profiles**: `get_current_profile()` resolves velocity vectors (`u_ms`, `v_ms`, `speed_ms`, `direction_deg`) across target depth coordinates (`[0.49m, 9.57m, 21.6m, 51.9m]`) using nearest-depth selection.
* **Hydrodynamics Risk Scoring**: `calculate_marine_risk()` deterministically evaluates strong ocean current velocity ($\ge 1.5$ m/s) and steep short-period wave hazards ($VHM0 \ge 1.5$ m AND $VTM02 \le 5.0$ s).
* **`ocean_card` Artifact**: `create_ocean_conditions_artifact()` produces structured UI cards containing location, SST, salinity, surface currents, multi-depth current profile array, wave spectrum, and ISO-8601 provenance entries.

---

## 4. ARTIFACT PROTOCOL

SAMUDRA AI responses deliver structured conversation artifacts alongside natural text explanations.

### 4.1 Response Schema
```json
{
  "message": {
    "role": "assistant",
    "text": "I found three potential fishing zones near Karwar. The nearest zone is 14 km offshore with favorable SST gradients."
  },
  "artifacts": [
    {
      "id": "art_pfz_881",
      "type": "pfz_map",
      "title": "Karwar Offshore PFZ Candidates",
      "payload": {
        "center": [14.81, 74.13],
        "candidates": [
          { "lat": 14.85, "lon": 74.25, "distance_km": 14.2, "heuristic_score": 0.88 }
        ]
      }
    },
    {
      "id": "art_risk_102",
      "type": "risk_summary",
      "title": "Marine Safety Risk Assessment",
      "payload": {
        "risk_level": "MODERATE",
        "risk_score": 42,
        "reasons": ["Significant wave height 1.8m", "Wind gusts up to 18 knots"]
      }
    }
  ],
  "actions": [
    { "type": "query_followup", "label": "Is it safe tomorrow morning?" },
    { "type": "show_data", "label": "View raw satellite readings" }
  ]
}
```

### 4.2 Supported Artifact Categories
* `map` — Interactive map with points/polygons
* `pfz_map` — Potential Fishing Zone layers and candidates
* `weather_card` — Atmospheric forecasts & wind direction dials
* `ocean_card` — SST, current vectors, wave dynamics
* `risk_summary` — Deterministic risk score meter & warnings
* `chart` — Time-series parameter trends (e.g. wave height over 72h)
* `route_map` — Safe navigation route avoiding geofenced areas
* `data_table` — Expandable numerical evidence table

---

## 5. VOICE ARCHITECTURE

Voice and Text are alternative interfaces to the **same underlying intelligence layer**. Voice must NOT use a separate AI system.

```text
VOICE INPUT ──► Speech-to-Text (STT) ──┐
                                       ├──► Conversation Engine ──► Fast/Deep Router ──► Response Synthesizer ──┬──► Text Output
TEXT INPUT  ───────────────────────────┘                                                                         └──► Text-to-Speech (TTS) ──► VOICE OUTPUT
```

* Both interfaces share: Conversation State, Context Manager, Tools, Agents, Evidence, and Artifact Generation.
* Supports voice activity detection (VAD) and barge-in / interruption handling.

---

## 6. ANONYMOUS TO AUTHENTICATED SESSION ARCHITECTURE

SAMUDRA AI provides an anonymous-first user experience. Users can start exploring without creating an account.

```text
Anonymous User
  │
  ├── Anonymous Session Token generated
  ├── Short-term Conversation & Artifact History in local session
  │
  ▼
User triggers Auth (Login / Sign up)
  │
  ├── Authentication verified
  ├── Backend automatically migrates anonymous session data to new User Account
  │
  ▼
Persistent Account (Cross-device history, saved routes, saved PFZ spots)
```

---

## 7. WEB + FLUTTER UNIFIED CLIENT ARCHITECTURE

Both the Web application and Mobile (Flutter) application are presentation layers communicating with the exact same Conversation REST/SSE API:

```text
                        ┌─────────────────────────┐
                        │    Conversation API     │
                        │   (FastAPI REST + SSE)  │
                        └────────────┬────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         ┌─────────────────────┐           ┌─────────────────────┐
         │   Web Client (UI)   │           │ Flutter Client (UI) │
         │ HTML5 / Leaflet / JS│           │  Flutter Mobile App │
         └─────────────────────┘           └─────────────────────┘
```

Neither client contains duplicate marine intelligence logic. Both render response text and standard conversation artifacts (`map`, `pfz_map`, `risk_summary`, `weather_card`).
