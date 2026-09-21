# DEVELOPMENT_ROADMAP.md — SAMUDRA AI Master Development Roadmap

This document outlines the phased roadmap for building the target SAMUDRA AI platform.

---

## PHASE 1 — FOUNDATION & CONVERSATIONAL CORE
1. **Architecture Constitution**: Repository guidelines, state audits, ADRs, and agent rules (*Completed in Phase 1.1*).
2. **Conversation State**: Expand state schema to track active context (location, activity, timeframe, active artifacts).
3. **Conversation API**: Standardize FastAPI REST endpoints for conversation session creation and turn management.
4. **Fast/Deep Router**: Implement intent-driven routing logic to bypass full multi-agent fan-out for simple queries.
5. **Context Management**: Implement rolling context summarization to maintain long-term memory without token ballooning.
6. **Artifact Protocol**: Define structured JSON Artifact output schema (`map`, `pfz_map`, `weather_card`, `risk_summary`, `route_map`).
7. **Streaming Pipeline**: Enhance Server-Sent Events (SSE) streaming for real-time agent execution thoughts and incremental response rendering.

---

## PHASE 2 — MARINE INTELLIGENCE ENHANCEMENT
1. **Weather Service Integration**: Enhance Open-Meteo atmospheric forecast coverage.
2. **Ocean Hydrodynamics**: Expand Copernicus Marine datasets (*Completed in Phase 2.2*).
3. **PFZ Bulletins**: Connect official INCOIS / MOSDAC Potential Fishing Zone bulletins alongside SST/chlorophyll heuristics (*Completed in Phase 2.3*).
4. **Tide Dynamics**: Incorporate tide level forecast models (*Completed in Phase 2.4*).
5. **Hazard Alerts**: Integrate active weather advisories & warnings (*Completed in Phase 2.4*).
6. **Geospatial Boundaries**: Replace demo circle geofencing with pure Python GIS spatial engine, EEZ boundary layers, proximity buffer math, and 3-tier provenance tracking (*Completed in Phase 2.5*).
7. **Evidence Layer**: Implement explicit dataset metadata, observation timestamps, confidence scoring, and data provenance tracking.
8. **Deterministic Risk Engine**: Refine risk assessment scoring algorithms against vessel type and environmental constraints.
9. **Marine Route Intelligence**: Implement weather- and wave-aware spatial route calculation with boundary avoidance.


---

## PHASE 3 — WEB INTERFACE (CHATGPT-LIKE EXPERIENCE)
1. **Conversational Dashboard**: Build a modern web interface with sidebar chat history, thread management, and responsive layout.
2. **Real-time SSE Streaming UI**: Render live thinking stream tiles as AI agents execute.
3. **Markdown & Code Rendering**: Support markdown formatting, tables, and LaTeX math.
4. **Interactive Map Artifacts**: Embed dynamic Leaflet/Mapbox maps displaying PFZ zones, weather overlays, and routes.
5. **Expandable Evidence Traces**: Allow users to toggle detailed scientific readings and data provenance.
6. **Suggested Follow-up Chips**: Render interactive action chips for one-click follow-up queries.

---

## PHASE 4 — FLUTTER MOBILE APPLICATION
1. **Shared Client SDK**: Implement HTTP/SSE client consuming the unified Conversation API.
2. **Artifact Rendering Components**: Build native Flutter widgets for maps, PFZ lists, weather dials, and risk gauges.
3. **Mobile Spatial UI**: Incorporate mobile GPS position auto-resolution for localized marine queries.
4. **Offline Capability**: Cache recent advisories, emergency contact guidelines, and saved maps for offline access.

---

## PHASE 5 — VOICE INTERACTION LAYER
1. **Speech-to-Text (STT)**: Integrate streaming STT (e.g. Whisper / Web Speech API) feeding directly into Conversation Engine.
2. **Text-to-Speech (TTS)**: Integrate low-latency natural TTS for audio response playback.
3. **Voice Activity Detection & Interruption**: Implement client-side VAD with barge-in support to pause TTS playback when user speaks.

---

## PHASE 6 — IDENTITY & ACCOUNT MIGRATION
1. **Anonymous Sessions**: Allow users to explore, query, and view maps instantly without login.
2. **Authentication**: Add secure user signup/login (OAuth / Email).
3. **Session Migration**: Seamlessly transfer anonymous conversation history, saved spots, and routes into user's account upon login.
4. **User Preferences**: Store default operating harbor, vessel characteristics, and preferred language.

---

## PHASE 7 — PROACTIVE MARINE INTELLIGENCE
1. **Background Monitoring**: Monitor saved user locations against cyclone feeds, high wave alerts, and weather shifts.
2. **Proactive Advisories**: Push automated marine advisories and geofence breach warnings to Web and Flutter clients.

---

## PHASE 8 — PRODUCTION HARDENING & DEPLOYMENT
1. **Caching & Rate Limiting**: Implement Redis caching for static GIS and marine API queries; apply client rate limiting.
2. **Observability**: Implement tracing for LLM latency, tool execution times, and graph node errors.
3. **Security & Validation**: Apply strict request validation and sanitized database access.
4. **Production Deployment**: Containerize application (Docker) and deploy with uvicorn/gunicorn behind reverse proxy.
