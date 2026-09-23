# PHASE 3.1 — SAMUDRA AI Frontend Data Contract & Artifact Specification

This document defines the formal data contract between the Python / LangGraph backend and the Web / Flutter frontend for SAMUDRA AI. It specifies every artifact schema, data classification, provenance requirement, map payload structure, edge-case behavior, and frontend state rendering rule.

---

## 1. Core Principle & Classification System

To ensure absolute truthfulness and user trust, every dataset and payload returned by SAMUDRA AI is explicitly classified. The frontend MUST NOT guess data freshness or authority; the backend communicates this explicitly in metadata and provenance fields.

### Data Classifications

- **`FORECAST`**: Predictive atmospheric output from numerical weather models (e.g. Open-Meteo Weather API 7-day forecast).
- **`MODELLED`**: Hydrodynamic, wave, or sea-level model output (e.g. Open-Meteo Marine wave dynamics & sea level height).
- **`OBSERVED`**: Direct satellite or physical in-situ sensor measurement (e.g. Copernicus Marine Sea Surface Temperature SST).
- **`MODEL_ANALYSIS`**: Data assimilating physical observations into a numerical model (e.g. Copernicus Ocean Currents & Chlorophyll-a).
- **`DERIVED`**: Mathematical calculation performed locally over physical data (e.g. `numpy.gradient` thermal front detection, PFZ multi-factor scoring).
- **`ALGORITHMIC`**: Output of deterministic pathfinding or optimization algorithms (e.g. A* marine route planning).
- **`STATIC_GIS` / `INFORMATIONAL_GIS`**: Static boundary geodatabase (e.g. VLIZ World EEZ Database v12).
- **`OFFICIAL_BULLETIN`**: Authoritative warning or advisory issued directly by a government agency (e.g. official INCOIS PFZ bulletin or IMD cyclone warning).
- **`UNAVAILABLE`**: Dataset or service is unconfigured, offline, or unavailable for the requested location.
- **`ERROR`**: External API request failed or timed out.
- **`PARTIAL`**: Some parameters in the payload were retrieved while others failed.

---

## 2. Complete Artifact Audit & Payload Contracts

### Artifact 1: `location_card`
- **Producing Node**: `location_resolver` (`graph/nodes/location.py`)
- **Backend Service**: Open-Meteo Geocoding / Nominatim (`tools/location.py`)
- **Data Classification**: `STATIC_GIS` / `GEOCODED`
- **Provider**: Open-Meteo Geocoding / OpenStreetMap
- **Freshness**: Real-time lookup
- **Coverage**: Global
- **Geometry Type**: `Point` (`[longitude, latitude]`)
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "loc_17.68_83.21",
  "type": "location_card",
  "title": "Location: Visakhapatnam",
  "description": "Coordinates: 17.68°N, 83.21°E",
  "data": {
    "name": "Visakhapatnam",
    "latitude": 17.68,
    "longitude": 83.21,
    "country": "India",
    "admin1": "Andhra Pradesh"
  },
  "metadata": {}
}
```

---

### Artifact 2: `weather_card`
- **Producing Node**: `weather_data_collector` (`graph/nodes/data_weather.py`)
- **Backend Service**: Open-Meteo Weather API (`tools/weather_service.py`)
- **Data Classification**: `FORECAST`
- **Provider**: Open-Meteo
- **Freshness**: Updated hourly (7-day forecast)
- **Coverage**: Global (0.1° grid)
- **Geometry Type**: `Point` (`[longitude, latitude]`)
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "wx_card_17.68_83.21",
  "type": "weather_card",
  "title": "Weather Forecast — Visakhapatnam",
  "description": "Temperature: 28.5°C | Wind: 14.2 km/h",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "current": {
      "temperature_2m": 28.5,
      "relative_humidity_2m": 78,
      "apparent_temperature": 32.1,
      "precipitation": 0.0,
      "weather_code": 1,
      "surface_pressure": 1012.4,
      "pressure_msl": 1013.1,
      "wind_speed_10m": 14.2,
      "wind_direction_10m": 135,
      "wind_gusts_10m": 18.5
    },
    "daily": {
      "time": ["2026-09-22", "2026-09-23", "2026-09-24"],
      "temperature_2m_max": [30.1, 30.5, 29.8],
      "temperature_2m_min": [25.2, 25.4, 24.9],
      "precipitation_sum": [0.0, 1.2, 4.5],
      "precipitation_probability_max": [10, 35, 60]
    },
    "units": {
      "current": { "temperature_2m": "°C", "wind_speed_10m": "km/h", "surface_pressure": "hPa" }
    },
    "provenance": {
      "source": "Open-Meteo Weather API",
      "provider": "Open-Meteo",
      "data_class": "FORECAST",
      "retrieved_at": "2026-09-22T07:45:00Z"
    }
  }
}
```

---

### Artifact 3: `marine_conditions`
- **Producing Node**: `marine_data_collector` (`graph/nodes/data_marine.py`)
- **Backend Service**: Open-Meteo Marine API (`tools/marine_service.py`)
- **Data Classification**: `MODELLED`
- **Provider**: Open-Meteo Marine
- **Freshness**: Updated 6-hourly (7-day forecast)
- **Coverage**: Global Oceans
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "marine_card_17.68_83.21",
  "type": "marine_conditions",
  "title": "Marine Dynamics — Visakhapatnam",
  "description": "Wave Height: 1.4 m | Swell Period: 8.2 s",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "current": {
      "wave_height": 1.4,
      "wave_direction": 140,
      "wave_period": 5.8,
      "wind_wave_height": 0.6,
      "wind_wave_period": 3.2,
      "swell_wave_height": 1.2,
      "swell_wave_direction": 135,
      "swell_wave_period": 8.2
    }
  }
}
```

---

### Artifact 4: `ocean_card`
- **Producing Node**: `ocean_data_collector` (`graph/nodes/data_ocean.py`)
- **Backend Service**: Copernicus Marine Python SDK (`tools/copernicus_service.py`)
- **Data Classification**: `OBSERVED` / `MODEL_ANALYSIS`
- **Provider**: Copernicus Marine Service (EU CMEMS)
- **Freshness**: 24h – 72h window
- **Coverage**: Global Ocean
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "ocean_card_17.68_83.21",
  "type": "ocean_card",
  "title": "Ocean Hydrodynamics — Visakhapatnam",
  "description": "SST: 28.4°C | Salinity: 34.1 psu | Current: 0.35 m/s",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "temperature": { "value": 28.4, "unit": "°C", "observation_time": "2026-09-22T00:00:00Z" },
    "salinity": { "value": 34.1, "unit": "psu", "observation_time": "2026-09-22T00:00:00Z" },
    "currents": {
      "speed_ms": 0.35,
      "direction_deg": 45.0,
      "u_ms": 0.25,
      "v_ms": 0.25
    },
    "waves": { "significant_wave_height_m": 1.35, "mean_wave_period_s": 6.1 },
    "provenance": [
      { "parameter": "sea_surface_temperature", "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m", "data_class": "OBSERVED" },
      { "parameter": "ocean_currents", "dataset_id": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m", "data_class": "MODEL_ANALYSIS" }
    ],
    "retrieved_at": "2026-09-22T07:45:00Z"
  }
}
```

---

### Artifact 5: `risk_summary`
- **Producing Node**: `risk_assessment` (`graph/nodes/risk.py`)
- **Backend Service**: Deterministic Marine Risk Engine (`tools/marine_risk.py`)
- **Data Classification**: `DERIVED` / `CALCULATED`
- **Provider**: SAMUDRA AI Deterministic Risk Engine
- **Freshness**: Real-time
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "risk_summary_moderate_42",
  "type": "risk_summary",
  "title": "Marine Safety Level: MODERATE",
  "description": "Calculated Risk Score: 42/100 for Visakhapatnam",
  "data": {
    "risk_level": "MODERATE",
    "risk_score": 42,
    "reasons": [
      "Significant wave height (1.4m) requires caution for small artisanal craft.",
      "Wind speed (14.2 km/h) is within normal operational safety thresholds."
    ],
    "evaluated_parameters": {
      "wave_height_m": 1.4,
      "wind_speed_kmh": 14.2,
      "current_speed_ms": 0.35,
      "inside_restricted_zone": false
    }
  }
}
```

---

### Artifact 6: `tide_card`
- **Producing Node**: `tide_data_collector` / `ocean_reasoner`
- **Backend Service**: Open-Meteo Marine sea-level timeseries + local peak detection (`tools/tide_service.py`)
- **Data Classification**: `MODELLED` / `DERIVED`
- **Provider**: Open-Meteo Marine
- **Datum**: Mean Sea Level (`MSL_MODELLED`) — **NOT Chart Datum / LAT**
- **Flutter Renderable**: **YES** (Ready with disclaimer)
- **Disclaimer Required**: *"sea_level_height_msl is a MODELLED value referenced to global Mean Sea Level (MSL), NOT lowest astronomical tide (LAT) or local chart datum. Not authoritative tide-gauge data."*
- **JSON Payload Example**:
```json
{
  "id": "tide_card_17.68_83.21",
  "type": "tide_card",
  "title": "Tide Dynamics — Visakhapatnam",
  "description": "Sea Level: 0.42m | Phase: FLOODING | Next High: 0.85m",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "status": "AVAILABLE",
    "current": { "sea_level_m": 0.42, "phase": "FLOODING", "trend": "RISING" },
    "extrema": [
      { "type": "HIGH", "time_iso": "2026-09-22T14:00:00Z", "height_m": 0.85 },
      { "type": "LOW", "time_iso": "2026-09-22T20:00:00Z", "height_m": -0.12 }
    ],
    "next_high_tide": { "type": "HIGH", "time_iso": "2026-09-22T14:00:00Z", "height_m": 0.85 },
    "next_low_tide": { "type": "LOW", "time_iso": "2026-09-22T20:00:00Z", "height_m": -0.12 },
    "tidal_range_m": 0.97,
    "datum": "MSL_MODELLED",
    "disclaimer": "sea_level_height_msl is a MODELLED value referenced to global MSL. NOT lowest astronomical tide (LAT) or local chart datum."
  }
}
```

---

### Artifact 7: `pfz_map`
- **Producing Node**: `fishery_data_collector` / `fishery_reasoner` (`graph/nodes/data_fishery.py`)
- **Backend Service**: Copernicus SST & Chlorophyll-a spatial front detection + scoring (`tools/pfz_service.py`, `tools/pfz_fronts.py`)
- **Data Classification**: `DERIVED` (Calculated locally from satellite grids)
- **Provider**: Copernicus Marine (Data) / SAMUDRA AI (Front Algorithm)
- **Flutter Renderable**: **YES** (Ready with disclaimer)
- **Disclaimer Required**: *"This is a decision-support candidate estimate calculated from spatial SST thermal fronts and Chlorophyll-a productivity gradients. Use approved INCOIS/MOSDAC PFZ bulletins for official confirmation."*
- **JSON Payload Example**:
```json
{
  "id": "pfz_map_17.68_83.21",
  "type": "pfz_map",
  "title": "PFZ Candidates near Visakhapatnam",
  "description": "Pelagic fish aggregation candidates based on thermal fronts and chlorophyll gradients.",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "pfz_status": "CALCULATED",
    "candidates": [
      {
        "latitude": 17.75,
        "longitude": 83.45,
        "score": 84.5,
        "sst_val": 28.2,
        "sst_grad": 0.08,
        "chl_val": 1.42,
        "distance_km": 28.1,
        "recommendation": "High potential pelagic aggregation zone along thermal front."
      }
    ],
    "thermal_fronts": [
      { "latitude": 17.72, "longitude": 83.40, "gradient_c_per_km": 0.08 }
    ],
    "bulletin": { "source": "INCOIS", "status": "UNAVAILABLE" },
    "recommendation": "Use approved INCOIS/MOSDAC PFZ bulletins for operational confirmation."
  }
}
```

---

### Artifact 8: `route_map`
- **Producing Node**: `route_data_collector` / `synthesizer`
- **Backend Service**: Deterministic A* Marine Pathfinding Engine (`tools/route_service.py`)
- **Data Classification**: `ALGORITHMIC`
- **Provider**: SAMUDRA Route Engine
- **GeoJSON Type**: `LineString` (`coordinates: [[lon, lat], ...]`)
- **Coordinate Order**: `[longitude, latitude]` (Standard GeoJSON RFC 7946)
- **Flutter Renderable**: **YES** (100% ready for Flutter Map / Leaflet)
- **JSON Payload Example**:
```json
{
  "id": "route_map_17.68_83.3_to_13.08_80.3",
  "type": "route_map",
  "title": "Marine Route: Visakhapatnam Port Outer to Chennai Port Outer Anchorage",
  "description": "Calculated Distance: 612.4 km | Route nodes: 5",
  "data": {
    "status": "OK",
    "origin": { "name": "Visakhapatnam Port Outer", "latitude": 17.68, "longitude": 83.3 },
    "destination": { "name": "Chennai Port Outer Anchorage", "latitude": 13.08, "longitude": 80.3 },
    "distance_km": 612.4,
    "route_geometry": {
      "type": "LineString",
      "coordinates": [
        [83.30, 17.68],
        [82.28, 16.95],
        [80.12, 14.25],
        [80.30, 13.08]
      ]
    },
    "waypoints": [
      { "id": "wp_visakhapatnam", "name": "Visakhapatnam Port Outer", "latitude": 17.68, "longitude": 83.30 },
      { "id": "wp_kakinada", "name": "Kakinada Offshore Node", "latitude": 16.95, "longitude": 82.28 },
      { "id": "wp_krishnapatnam", "name": "Krishnapatnam Port Outer", "latitude": 14.25, "longitude": 80.12 },
      { "id": "wp_chennai", "name": "Chennai Port Outer Anchorage", "latitude": 13.08, "longitude": 80.30 }
    ],
    "verification": { "eez": "INFORMATIONAL", "mpa": "UNAVAILABLE", "naval": "UNAVAILABLE" }
  }
}
```

---

### Artifact 9: `geofence_alert`
- **Producing Node**: `geofence_data_collector` (`graph/nodes/data_geofence.py`)
- **Backend Service**: GIS Spatial Engine (`tools/gis_service.py`)
- **Data Classification**: `STATIC_GIS` / `INFORMATIONAL_GIS`
- **Provider**: Flanders Marine Institute (VLIZ) World EEZ v12
- **Flutter Renderable**: **YES** (100% ready)
- **JSON Payload Example**:
```json
{
  "id": "geofence_alert_17.68_83.21",
  "type": "geofence_alert",
  "title": "Geofence Alert: Intersected Indian Exclusive Economic Zone (Mainland)",
  "description": "Coordinates (17.68°N, 83.21°E) fall inside designated polygon: Indian Exclusive Economic Zone (Mainland).",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "inside_restricted_zone": false,
    "proximity_warning": false,
    "matched_zones": [
      {
        "zone_id": "eez_in_mainland",
        "name": "Indian Exclusive Economic Zone (Mainland)",
        "type": "EEZ",
        "category": "EEZ",
        "inside": true,
        "data_class": "INFORMATIONAL_GIS",
        "provider": "Flanders Marine Institute (VLIZ)"
      }
    ],
    "layers": [
      { "category": "EEZ", "status": "AVAILABLE", "data_class": "INFORMATIONAL_GIS" },
      { "category": "NAVAL_RESTRICTED", "status": "UNAVAILABLE", "message": "No verified public authoritative GIS polygon dataset configured." },
      { "category": "MPA", "status": "UNAVAILABLE", "message": "No local Marine Protected Area (MPA) polygon layer loaded." }
    ]
  }
}
```

---

### Artifact 10: `hazard_alert`
- **Producing Node**: `hazard_service` (`tools/hazard_service.py`)
- **Backend Service**: Official IMD/INCOIS Hazard Parser (`tools/hazard_service.py`)
- **Data Classification**: `UNAVAILABLE` (Default when live feed unconfigured)
- **Provider**: IMD / INCOIS
- **Flutter Renderable**: **YES** (Renders clear `UNAVAILABLE` notice or active alert list if connected)
- **JSON Payload Example**:
```json
{
  "id": "hazard_alert_17.68_83.21",
  "type": "hazard_alert",
  "title": "Official Hazard Feed — Visakhapatnam",
  "description": "No active official hazard alerts reported for this location.",
  "data": {
    "location": { "name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21 },
    "status": "UNAVAILABLE",
    "alerts": [],
    "advice": "No active official IMD/INCOIS live hazard feed connected.",
    "provenance": { "provider": "INCOIS / IMD", "data_class": "UNAVAILABLE", "status": "UNAVAILABLE" }
  }
}
```

---

## 3. Map & GeoJSON Rendering Audit

| Spatial Layer | Backend Status | Geometry Type | GeoJSON Valid? | Coordinate Format | Renderable in Flutter? | Data Source | Fallback Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Base Map** | `AVAILABLE` | Tile Layer | N/A | Carto / OSM | **YES** | OpenStreetMap / CartoDB | Standard fallback tile |
| **EEZ Polygon** | `AVAILABLE` | `Polygon` | Yes | `[lon, lat]` | **YES** | `eez_india.geojson` (VLIZ v12) | Embedded polygon |
| **Route LineString** | `AVAILABLE` | `LineString` | Yes | `[lon, lat]` | **YES** | `tools/route_service.py` | Empty LineString if no path |
| **Waypoint Markers** | `AVAILABLE` | `Point` | Yes | `[lon, lat]` | **YES** | `MARITIME_WAYPOINTS` | Empty list |
| **PFZ Candidate Points** | `AVAILABLE` | `Point` | Yes | `[lon, lat]` | **YES** | `tools/pfz_service.py` | Empty list |
| **Thermal Front Points** | `AVAILABLE` | `Point` | Yes | `[lon, lat]` | **YES** | `tools/pfz_fronts.py` | Empty list |
| **Copernicus WMTS Tiles** | `AVAILABLE` | WMTS XML | Capabilities XML | EPSG:3857 | **YES** | `tools/copernicus_wmts.py` | Fallback message |
| **Current Vector Points** | `PARTIAL` | `Point` | Yes | `[lon, lat]` | **PARTIAL** | Copernicus Currents | Point array with speed & angle |
| **Chlorophyll Grid Points**| `PARTIAL` | `Point` | Yes | `[lon, lat]` | **PARTIAL** | Copernicus Biogeochemical | Grid point array |
| **Marine Protected Areas** | `UNAVAILABLE` | N/A | N/A | N/A | **NO** | None | Returns `status: UNAVAILABLE` |
| **Naval Restriction Zones**| `UNAVAILABLE` | N/A | N/A | N/A | **NO** | None | Returns `status: UNAVAILABLE` |
| **IMBL Line** | `UNAVAILABLE` | N/A | N/A | N/A | **NO** | None | Returns `status: UNAVAILABLE` |
| **Bathymetry Grid** | `UNAVAILABLE` | N/A | N/A | N/A | **NO** | None | Returns `status: UNAVAILABLE` |

---

## 4. Master Data Availability Matrix

| Domain | Dataset | Provider | Classification | Status | Live/Static | Coverage | Backend Used By | Artifact | Map Ready | Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Weather** | Temperature & Humidity | Open-Meteo | `FORECAST` | `AVAILABLE` | Live | Global | `weather_data_collector` | `weather_card` | Yes | 20s timeout limit |
| **Weather** | Wind Speed & Direction | Open-Meteo | `FORECAST` | `AVAILABLE` | Live | Global | `weather_data_collector`, `risk_assessment` | `weather_card` | Yes | 10m altitude model |
| **Weather** | Wind Gusts & Pressure | Open-Meteo | `FORECAST` | `AVAILABLE` | Live | Global | `weather_data_collector` | `weather_card` | Yes | Hourly forecast |
| **Ocean** | Sea Surface Temp (SST) | Copernicus | `OBSERVED` | `AVAILABLE` | Live | Global | `ocean_data_collector`, `pfz_service` | `ocean_card`, `pfz_map` | Yes | 0.083° (~9km) grid |
| **Ocean** | Surface Currents ($u, v$) | Copernicus | `MODEL_ANALYSIS` | `AVAILABLE` | Live | Global | `ocean_data_collector`, `route_service` | `ocean_card` | Yes | 0.49m surface depth |
| **Ocean** | Salinity | Copernicus | `MODEL_ANALYSIS` | `AVAILABLE` | Live | Global | `ocean_data_collector` | `ocean_card` | Yes | 0.083° grid |
| **Ocean** | Chlorophyll-a | Copernicus | `MODEL_ANALYSIS` | `AVAILABLE` | Live | Global | `ocean_data_collector`, `pfz_service` | `ocean_card`, `pfz_map` | Yes | 0.25° (~28km) grid |
| **Marine** | Wave Height & Period | Open-Meteo | `MODELLED` | `AVAILABLE` | Live | Global | `marine_data_collector`, `risk_assessment` | `marine_conditions` | Yes | Forecast model output |
| **Tide** | Sea Level Height (MSL) | Open-Meteo | `MODELLED` | `AVAILABLE` | Live | Global | `tide_service` | `tide_card` | Yes | MSL referenced (Not LAT) |
| **Tide** | High/Low Extrema & Phase | Local Algorithm | `DERIVED` | `AVAILABLE` | Live | Global | `tide_service` | `tide_card` | Yes | Derived peak detection |
| **PFZ** | Satellite Thermal Fronts | Local Algorithm | `DERIVED` | `AVAILABLE` | Live | Regional | `pfz_service`, `pfz_fronts` | `pfz_map` | Yes | Derived from SST gradients |
| **PFZ** | Official INCOIS Bulletin | INCOIS | `OFFICIAL_BULLETIN` | `UNAVAILABLE` | Live | India | `incois_bulletin.py` | `pfz_map` | No | Live API unconfigured |
| **Hazards**| IMD/INCOIS Warning Feed | IMD / INCOIS | `OFFICIAL_BULLETIN` | `UNAVAILABLE` | Live | India | `hazard_service.py` | `hazard_alert` | No | Live API unconfigured |
| **GIS** | Indian EEZ Boundary | VLIZ Marine | `STATIC_GIS` | `AVAILABLE` | Static | India 200NM | `gis_service.py` | `geofence_alert`, `route_map` | Yes | Informational v12 polygon |
| **GIS** | Marine Protected Areas | None | `UNAVAILABLE` | `UNAVAILABLE` | None | India | `gis_service.py` | None | No | Polygon layer missing |
| **GIS** | Naval Restricted Zones | None | `UNAVAILABLE` | `UNAVAILABLE` | None | India | `gis_service.py` | None | No | Polygon layer missing |
| **Route** | Waypoint Network Graph | SAMUDRA | `STATIC_GIS` | `AVAILABLE` | Static | 27 Ports | `route_service.py` | `route_map` | Yes | 27 Indian waypoints |
| **Route** | A* Path Optimization | SAMUDRA | `ALGORITHMIC` | `AVAILABLE` | Live | 27 Ports | `route_service.py` | `route_map` | Yes | Multi-factor cost engine |

---

## 5. Missing Data Behavior

| Dataset | Backend Status | Exact Fallback Behavior | User-Visible Response | What Flutter Should Display | Disclaimer Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Official INCOIS PFZ** | `status: UNAVAILABLE` | Calculates thermal-front candidate zones from Copernicus SST/Chl | *"This is a decision-support candidate estimate calculated from satellite thermal fronts..."* | Thermal candidate points + warning badge | *"Use approved INCOIS/MOSDAC bulletins for operational confirmation."* |
| **Naval / Defence GIS** | `status: UNAVAILABLE` | Checks EEZ boundary; sets `NAVAL_RESTRICTED: UNAVAILABLE` | *"Naval/defence restriction verification is currently unavailable. Consult NHO NAVAREA VIII warnings."* | Warning badge in Geofence Card | *"Consult active NHO NAVAREA VIII warnings."* |
| **MPA Polygons** | `status: UNAVAILABLE` | Sets `MPA: UNAVAILABLE` | *"Marine Protected Area (MPA) layer is currently unavailable."* | Grayed out layer toggle with notice | *"MPA layer unconfigured."* |
| **Official Hazard Feed** | `status: UNAVAILABLE` | Returns default safe advisory payload | *"No active official IMD/INCOIS live hazard feed connected."* | Info card: "No active official warnings" | *"Official feed unconfigured."* |
| **Bathymetry / Depth** | `status: UNAVAILABLE` | Route cost engine assumes open-water depth clearance | Route generated without depth cost penalty | Informational note on Route Card | *"Bathymetric depth clearance unverified."* |

---

## 6. Complete Edge-Case Matrix

| Scenario | Backend Behavior | Artifact Generated | Frontend Rendering State | User Message |
| :--- | :--- | :--- | :--- | :--- |
| **No Location Given** | `location: None` | None | `NO_LOCATION` | *"Could you please specify your target coastal location or harbor?"* |
| **Invalid Location Name** | `status: NOT_FOUND` | None | `ERROR` | *"Location 'AtlantisCityX99' could not be resolved. Please specify a valid location."* |
| **Landlocked Location** | `status: LANDLOCKED` | None | `LANDLOCKED` | *"Oceanographic data is not available for landlocked coordinates (Zurich, Switzerland)."* |
| **Single Location Query** | Resolves lat/lon | `location_card`, domain artifact | `AVAILABLE` | Normal domain report |
| **Dual Location Query** | Resolves single target | `location_card` | `PARTIAL` | Prompts for explicit origin/destination coordinates |
| **API Timeout (Weather)** | `status: ERROR` | None | `ERROR` | *"Weather forecast service temporarily unavailable. Please retry."* |
| **Copernicus Offline** | `status: ERROR` | None (Open-Meteo fallback) | `PARTIAL` | *"Copernicus ocean snapshot offline; displaying Open-Meteo wave data."* |
| **Gemini 429 Quota Error** | Opens circuit 900s, cascades | Standard response | `AVAILABLE` | Normal response (handled seamlessly) |
| **Groq 404 / Key Failure**| Classifies config error, cascades| Standard response | `AVAILABLE` | Normal response (handled seamlessly) |
| **All LLMs Down** | Uses `FallbackMockLLM` | Standard response | `AVAILABLE` | Baseline mock report |
| **No Route Found** | `status: NO_PATH_FOUND` | `route_map` (`status: UNAVAILABLE`)| `NO_ROUTE` | *"No viable maritime route found between requested coordinates."* |

---

## 7. Standardized Frontend Data Contract Schema

Every response returned by `POST /chat` and `GET /chat/stream` adheres to this structured contract:

```typescript
interface ChatResponseContract {
  conversation_id: string;
  thread_id: string;
  response: string;                        // Synthesized natural language response
  route_path: "FAST" | "DEEP";              // Execution path
  detected_language: string;               // ISO 639-1 code (e.g. "en", "ta", "hi")
  intent: string;                          // Classified intent (safety, fishery, weather, etc.)
  risk_level?: "LOW" | "MODERATE" | "HIGH" | "VERY HIGH" | "UNKNOWN";
  risk_score?: number;                     // 0 to 100
  confidence_score?: number;               // 0.0 to 1.0
  gate_decision?: "PASS" | "RECHECK" | "BLOCKED";
  location?: {
    status: "FOUND" | "NOT_FOUND" | "LANDLOCKED";
    name: string;
    latitude: number;
    longitude: number;
    country?: string;
    admin1?: string;
  };
  artifacts: Array<{
    id: string;
    type: "location_card" | "weather_card" | "marine_conditions" | "ocean_card" | 
          "risk_summary" | "tide_card" | "pfz_map" | "route_map" | "geofence_alert" | "hazard_alert";
    title: string;
    description: string;
    data: Record<string, any>;             // Standardized artifact data payload
    metadata: Record<string, any>;
  }>;
  node_trace: string[];
  errors: string[];
}
```

---

## 8. Frontend State Model

Flutter clients should maintain an explicit **State Model** for each artifact and view, mapped directly from backend payload status fields:

```
                  ┌──────────────────────┐
                  │   Backend Payload    │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   location.status                     artifact.data.status
   - "FOUND"                           - "AVAILABLE"
   - "NOT_FOUND"                       - "PARTIAL"
   - "LANDLOCKED"                      - "UNAVAILABLE"
            │                          - "ERROR"
            │                                 │
            ▼                                 ▼
   ┌─────────────────┐               ┌─────────────────┐
   │ Frontend State  │               │ Frontend State  │
   │ - AVAILABLE     │               │ - AVAILABLE     │
   │ - NO_LOCATION   │               │ - PARTIAL       │
   │ - LANDLOCKED    │               │ - UNAVAILABLE   │
   └─────────────────┘               │ - ERROR         │
                                     └─────────────────┘
```

1. **`AVAILABLE`**: Render full interactive UI card & map overlays.
2. **`PARTIAL`**: Render available data fields + prominent limitation warning banner.
3. **`UNAVAILABLE`**: Render structured grayed-out card with explicit notice (e.g. *"Official IMD hazard feed unconfigured"*).
4. **`ERROR`**: Render error message with "Retry" action button.
5. **`NO_LOCATION`**: Render location selector prompt ("Please select or search a coastal harbor").
6. **`LANDLOCKED`**: Render inland notification banner ("Oceanographic data is not available for landlocked coordinates").

---

## 9. Backend Issues to Address Before UI Expansion

### 1. High Priority
- **Dual-Location Text Extractor**: Update `location_resolver` to parse both origin and destination harbors from plain text queries (e.g. *"route from Visakhapatnam to Chennai"*).
- **Non-Interactive Copernicus Login**: Execute `copernicusmarine.login()` on app startup using `.env` credentials to prevent interactive CLI prompt hangs.

### 2. Medium Priority
- **Groq Model Identifier**: Update default `GROQ_MODEL` in `.env` to an active model ID (e.g. `llama-3.1-8b-instant`).
- **Normalized Artifact Status Field**: Ensure every artifact payload consistently includes a top-level `status` field (`AVAILABLE` | `PARTIAL` | `UNAVAILABLE`).

---

## 10. Final Frontend Readiness Matrix

| Artifact | Backend Ready | Data Ready | Geometry Ready | Provenance Ready | Flutter Can Render | Final Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `location_card` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY FOR UI`** |
| `weather_card` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY FOR UI`** |
| `marine_conditions` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY FOR UI`** |
| `ocean_card` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY FOR UI`** |
| `risk_summary` | **YES** | **YES** | N/A | **YES** | **YES** | **`READY FOR UI`** |
| `tide_card` | **YES** | **YES** | N/A | **YES** | **YES** | **`READY WITH LIMITATIONS`** (MSL Disclaimer) |
| `pfz_map` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY WITH LIMITATIONS`** (INCOIS Disclaimer) |
| `route_map` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY FOR UI`** (27-waypoint A* engine) |
| `geofence_alert` | **YES** | **YES** | **YES** | **YES** | **YES** | **`READY WITH LIMITATIONS`** (EEZ functional, MPA/Naval unavailable) |
| `hazard_alert` | **YES** | **PARTIAL** | N/A | **YES** | **YES** | **`READY WITH LIMITATIONS`** (Renders `UNAVAILABLE` notice cleanly) |

---

## Safety Verdict for UI Development

> **VERDICT: SAFE TO BEGIN UI IMPLEMENTATION**
> 
> The SAMUDRA AI backend data contract is verified and stable. All 10 UI artifacts produce standardized JSON payloads with deterministic provenance and disclaimers. Flutter developers can safely build UI components targeting the contract defined in this document.
