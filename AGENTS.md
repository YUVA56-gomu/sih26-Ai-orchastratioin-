# AGENTS.md — SAMUDRA AI Agent Constitution

This document contains mandatory operational rules and architectural boundaries for all AI coding agents working on the SAMUDRA AI repository.

---

## 1. MANDATORY CONTEXT CHECKING

Before proposing, planning, or executing any modifications to this repository:

1. **Read `AGENTS.md`** — Ensure strict adherence to coding guidelines, architectural boundaries, and safety constraints.
2. **Read `ARCHITECTURE.md`** — Review the target system design, including the Fast/Deep path routing, Conversation Engine, and Artifact Protocol.
3. **Read `CURRENT_STATE.md`** — Understand what subsystems are implemented, partial, prototype, heuristic, demo, or missing today.
4. **Read `DECISIONS.md`** — Check existing Architectural Decision Records (ADR-001 through ADR-010) before modifying core technologies or abstractions.
5. **Read `DEVELOPMENT_ROADMAP.md`** — Ensure work aligns with the active development phase.

---

## 2. GENERAL ARCHITECTURAL RULES

1. **Never redesign the architecture without explicit instruction.** Do not refactor established pipelines or replace framework components unless explicitly tasked.
2. **Never delete working functionality** merely because an alternative implementation is preferred.
3. **Never create duplicate systems** when an existing subsystem can be cleanly extended.
4. **Never claim demo/synthetic/heuristic data is authoritative.** Always maintain clear provenance (`OBSERVED`, `MODELLED`, `HEURISTIC`, `DEMO`).
5. **Never invent or hallucinate marine data.** If external data is unavailable, return explicit missing/error status.
6. **Deterministic calculations must remain deterministic.** Calculations (distance, geofencing, risk scoring, spatial intersections) must be handled by python code, not delegated to LLM prompts.
7. **Preserve existing contracts.** Maintain API signatures, state schema contracts, and frontend response schemas.
8. **Include automated tests** for all new features or bug fixes where practical.
9. **No secret exposures.** Never hardcode credentials, API keys, or tokens in source code or documentation.

---

## 3. PRODUCT VISION & BOUNDARIES

SAMUDRA AI is designed as a **conversational marine intelligence platform** ("ChatGPT for the ocean"):

* **One Conversation / One AI Brain**: Text and Voice share the same conversation state, context manager, memory, and tools.
* **Unified Clients**: Web (HTML/JS) and Mobile (Flutter) consume the same backend Conversation API and Artifact Protocol.
* **Fast Path ⚡ & Deep Path 🧠**: Simple queries bypass multi-agent orchestration for speed; complex queries invoke multi-agent planning and evidence correlation.
* **First-Class Artifacts**: Maps, PFZ layers, weather cards, route graphics, and risk summaries are rendered via structured response artifacts.

---

## 4. REPORTING PROTOCOL

After completing any task, agents must report:
1. Exact files created or modified.
2. Automated test execution results (passed, failed, unrunnable).
3. Any unhandled edge cases, environment limitations, or remaining risks.
4. `git status` verification.
5. **DO NOT commit** changes unless explicitly instructed by the user.
