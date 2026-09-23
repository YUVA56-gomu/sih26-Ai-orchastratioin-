# PHASE 3 — SAMUDRA AI WEB PRODUCT AUDIT

## 1. Overview
This audit evaluates the architectural state of the SAMUDRA AI Phase 3 web application before and after upgrading it into a ChatGPT/Gemini-quality conversational product.

---

## 2. Core Architecture Audit Questions & Findings

### Q1: How are conversations currently represented?
- **Backend**: Represented in `samudra_storage.db` using two complementary tables:
  1. `conversations`: Stores metadata (`conversation_id`, `thread_id`, `title`, `created_at`, `updated_at`).
  2. `checkpoints` / `checkpoint_blobs` / `checkpoint_writes`: Managed by LangGraph `SqliteSaver` to store full graph state and turn history keyed by `thread_id`.
- **Frontend**: Represented by `ConversationSummary` and `ConversationDetail` interfaces in `web/src/api/types.ts`.

### Q2: Do conversation IDs exist?
- **Yes**. `conversation_id` serves as the public thread identifier and aligns 1-to-1 with `thread_id` in `SqliteSaver`.

### Q3: Are messages associated with conversations?
- **Yes**. `SqliteSaver` serializes message history inside the state object for the given `thread_id`. When retrieving `GET /conversations/{conversation_id}`, the backend returns all deserialized messages.

### Q4: Does the frontend store history only in local React state?
- **No**. The frontend fetches persistent conversation summaries via `GET /conversations` on mount and reloads detail (`GET /conversations/{conversation_id}`) whenever a thread is selected.

### Q5: Does the backend already support conversation retrieval?
- **Yes**.
  - `GET /conversations`: Returns lightweight list of metadata records sorted by `updated_at` descending. Supports optional `?q=` search query.
  - `GET /conversations/{conversation_id}`: Returns metadata, message history, active context, and associated artifacts.

### Q6: Does a conversation list/history endpoint exist?
- **Yes**. `GET /conversations?q={query}` is available.

### Q7: Are artifacts associated with messages/conversations?
- **Yes**. Artifacts generated during execution turns are stored in the state checkpoint by `SqliteSaver` and returned in `ConversationDetail.artifacts`.

### Q8: Does creating a new chat actually create a new backend conversation?
- **Yes**. Clicking **+ New Chat** resets active conversation ID to `undefined`. On the user's next message, a new `conversation_id` UUID is generated, stored in `samudra_storage.db`, and populated with initial messages and artifacts.

---

## 3. Web UI Component Audit

| Component | Responsibility | Audit Result | Status |
|---|---|---|---|
| `AppLayout.tsx` | Main application shell & layout state | Supports responsive drawer, stream handling, conversation selection, rename, delete, and search. | UPGRADED & VERIFIED |
| `Sidebar.tsx` | Thread navigation & conversation management | Redesigned with date grouping (`Today`, `Yesterday`, `Previous 7 Days`, `Older`), live search, inline title rename, deletion popover, active highlighting, and user footer. | UPGRADED & VERIFIED |
| `ChatMessageList.tsx` | Central message stream viewport | Auto-scrolls, renders messages, streaming steps, artifacts, and contextual action chips. | VERIFIED |
| `ChatMessageItem.tsx` | Single message bubble & agent trace | Formats user queries, assistant responses, markdown tables, code blocks, agent reasoning traces, and risk badges. | VERIFIED |
| `InputComposer.tsx` | Floating multiline text composer | Glassmorphism card with auto-resizing textarea, mic placeholder button, send/stop controls, and keybindings (`Enter`/`Shift+Enter`). | UPGRADED & VERIFIED |
| `WelcomeScreen.tsx` | Initial empty chat hero screen | SAMUDRA AI brand hero with capabilities grid and 4 clickable example prompt cards. | UPGRADED & VERIFIED |
| `EvidencePanel.tsx` | Anti-hallucination provenance inspector | Displays dataset, provider, freshness, confidence, location, and disclaimers. | VERIFIED |
| `ArtifactRenderer.tsx` | Polymorphic container for 10 artifacts | Dispatches rendering to specific card components. | VERIFIED |

---

## 4. Artifact Components Audit

1. **`PFZMapCard.tsx`**: Uses Leaflet tile layer & GeoJSON parsing for Potential Fishing Zones.
2. **`RouteMapCard.tsx`**: Renders safe sea route polyline, waypoints, and hazard zones on CartoDB dark tiles.
3. **`MarineConditionsCard.tsx`**: Displays SST, current speed/direction, wave height, wave period, and sea state.
4. **`WeatherCard.tsx`**: Displays temperature, humidity, wind, and forecast.
5. **`OceanCard.tsx`**: Displays ocean hydrodynamics metrics.
6. **`TideCard.tsx`**: Displays tide levels and surge forecasts.
7. **`RiskSummaryCard.tsx`**: Displays risk score, risk level, and environmental factor breakdown.
8. **`GeofenceAlertCard.tsx`**: Displays marine protected area / EEZ boundary alerts.
9. **`HazardAlertCard.tsx`**: Displays cyclone / storm wave warnings.
10. **`LocationCard.tsx`**: Displays resolved geographic location coordinates.
