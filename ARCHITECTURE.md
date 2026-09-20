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

Conversation state tracks:
* **Active Location & Coordinates**
* **Active Activity (e.g. fishing, commercial navigation, diving)**
* **Active Timeframe**
* **Last Generated Artifact References**

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
