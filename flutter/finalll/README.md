# ORCA Marine Intelligence Backend — Final Backend

## What this provides

- Natural-language conversational input
- Language detection by Gemini
- Contextual multi-turn sessions with SQLite
- Deterministic task planning and orchestration
- Open-Meteo marine + weather data
- NOAA NDBC nearest-buoy observation fallback
- INCOIS ERDDAP point enrichment for chlorophyll and mixed-layer depth
- INCOIS official PFZ/advisory evidence layer
- IMD district warning and nowcast API integration
- IMD cyclone information source
- Configurable geofence GeoJSON checking
- Route-risk analysis endpoint
- Parameter-level source, URL, timestamp and confidence
- Completeness and safety-state calculation
- Final same-language Gemini response from validated JSON only
- REST chat endpoint and WebSocket endpoint for frontend integration

## Gemini usage

Only Level 1 and Level 5 call Gemini. No Gemini Google Search grounding is used.

## Install

```powershell
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

## `.env`

```env
GEMINI_API_KEY=YOUR_KEY
GEMINI_MODEL_L1=gemini-2.5-flash-lite
GEMINI_MODEL_L5=gemini-2.5-flash
```

## Run

```powershell
uvicorn main:app --reload
```

Then open:

`http://127.0.0.1:8000/docs`

## Chat request

POST `/api/chat`

```json
{
  "message": "Where is the nearest Potential Fishing Zone today?",
  "conversation_id": "demo-1",
  "location": {
    "name": "Visakhapatnam"
  }
}
```

## WebSocket

`ws://127.0.0.1:8000/api/chat/ws/demo-1`

Send:

```json
{"message":"What about tomorrow morning?"}
```

## Direct endpoints

- `GET /api/location/search?q=Visakhapatnam`
- `GET /api/ocean/current?latitude=17.69&longitude=83.29`
- `GET /api/weather/current?latitude=17.69&longitude=83.29`
- `GET /api/hazards?location=Visakhapatnam`
- `GET /api/pfz/nearest?latitude=17.69&longitude=83.29`
- `GET /api/geofence/check?latitude=17.69&longitude=83.29`
- `POST /api/route/safe`

## Geofencing

Put real, licensed GeoJSON operational boundaries in `data/geofences.geojson`. The repository intentionally ships an empty file instead of pretending demo polygons are real maritime restrictions.

## PFZ

The official INCOIS PFZ WebGIS exposes current geo-referenced PFZ information at coastal nodes. The backend keeps that official advisory provenance, but it will not fabricate exact PFZ coordinates from prose. For an exact nearest-PFZ response, connect the INCOIS PFZ GIS/WMS/feature layer when its machine-readable endpoint is available to your deployment.

## Satellite EO

INCOIS ERDDAP is used directly for satellite/oceanographic enrichment where the public dataset exposes a point query. MOSDAC is documented as an additional ISRO satellite source; some downloads require an authenticated MOSDAC account, so credentials should be added only when you have authorized access.

## Important safety limitation

This is a decision-support platform, not a navigation system. Official maritime warnings, nautical charts, port advisories and vessel-specific procedures remain authoritative.
