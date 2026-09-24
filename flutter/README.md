# SAMUDRA AI — Flutter Mobile Client

**Marine intelligence and safety platform for fishermen, marine operators, and researchers.**

> **Status: Active development — Milestone 4 of 11 complete.**
> This document reflects what is actually implemented. Features not yet built are clearly marked.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Current Project Status](#2-current-project-status)
3. [What Has Been Implemented](#3-what-has-been-implemented)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Setup on a New PC (Windows)](#6-setup-on-a-new-pc-windows)
7. [Running on a Physical Android Phone](#7-running-on-a-physical-android-phone)
8. [Demo Walkthrough](#8-demo-walkthrough)
9. [Frontend Contributor Guide](#9-frontend-contributor-guide)
10. [Backend Contributor Guide](#10-backend-contributor-guide)
11. [Data Sourcing Requirements](#11-data-sourcing-requirements)
12. [Real IMBL Data Integration Plan](#12-real-imbl-data-integration-plan)
13. [Deferred and Pending Work](#13-deferred-and-pending-work)
14. [Task 15 Roadmap](#14-task-15-roadmap)
15. [Git and Contribution Workflow](#15-git-and-contribution-workflow)
16. [Environment and Secrets](#16-environment-and-secrets)
17. [Development Rules](#17-development-rules)
18. [Troubleshooting](#18-troubleshooting)
19. [Where Can I Contribute?](#19-where-can-i-contribute)

---

## 1. Project Overview

SAMUDRA AI is a marine intelligence platform designed primarily for Indian fishermen, but also useful for marine operators, researchers, and coastal authorities.

Fishermen operating offshore often have **no internet connection**. They need safety-critical information — maritime boundary awareness, sea conditions, weather — available even when completely disconnected. That is the central reason this mobile client exists as an **edge-first** application with local GPS, local SQLite storage, and local spatial calculations.

### What the platform will eventually do

- Provide AI-assisted marine information in natural language (including regional languages)
- Display marine maps with fishing zones, hazards, and maritime boundaries
- Monitor vessel position against the Indian Maritime Boundary Line (IMBL) in real time
- Alert the crew if the vessel approaches or crosses a boundary
- Cache marine data locally so it is available offline
- Connect to backend APIs for live oceanographic data when connectivity is available

### High-level data flow

```
User
 │
 ▼
SAMUDRA AI Flutter App
 │
 ├─── GPS / LocationService        (real-time position)
 ├─── SQLite / DatabaseService     (offline marine data cache)
 ├─── IMBL / ImblBoundaryService   (spatial safety engine)
 │
 ▼
Future Backend / FastAPI / Marine Intelligence
 │
 ▼
Actionable marine information
```

### What this repository is

This repository is the **Flutter Android client**. It handles:
- Mobile UI
- GPS/GNSS acquisition
- Local SQLite storage
- Offline IMBL boundary checking

The FastAPI backend and marine data ingestion pipeline are being developed separately.

---

## 2. Current Project Status

| Feature | Status | Notes |
|---------|--------|-------|
| Flutter Android client | ✅ Done | Runs on physical Android device |
| Premium mobile UI | ✅ Done | Dark marine theme, SAMUDRA design system |
| Home screen | ✅ Done | Greeting, AI input, suggestions, quick actions, status |
| Sidebar / navigation | ✅ Done | ChatGPT-style slide-out drawer |
| GPS / GNSS location | ✅ Done | Latitude, longitude, accuracy, speed, heading |
| GPS accuracy testing | ✅ Done | Tested on Moto G85 5G (Android 16) |
| IST timestamp display | ✅ Done | UTC internally, IST displayed to user |
| SQLite offline cache | ✅ Done | `sqflite`, `marine_data` table, batch inserts |
| Offline persistence testing | ✅ Done | Verified data survives app kill and restart |
| IMBL spatial engine | ✅ Done | Ray-casting PIP, Haversine distance |
| Point-in-polygon | ✅ Done | Works CW and CCW, handles concave polygons |
| Boundary distance calculation | ✅ Done | Cosine-corrected Cartesian approximation |
| GPS accuracy confidence guard | ✅ Done | Returns UNKNOWN when fix is too imprecise |
| IMBL unit tests | ✅ Done | 14/14 passing, no network required |
| **Real IMBL production dataset** | ⏳ Waiting | Task 11 team to provide authoritative geometry |
| Background monitoring | 🔜 Next | Requires verified IMBL geometry first |
| Local emergency alert / buzzer | 🔲 Pending | Depends on background breach detection |
| NavIC / NMEA integration | 🔲 Pending / Investigation | Requires device GNSS hardware verification |
| Backend API integration | 🔲 Pending | FastAPI backend in separate development |
| Real marine API data | 🔲 Pending | Data contracts not yet established |
| < 15 ms IMBL benchmark | 🔲 Pending | Correctness verified first; performance TBD |

> ⚠️ The IMBL engine currently uses a **synthetic DEMO polygon only**.
> It is **NOT** the real Indian Maritime Boundary Line.
> The real production IMBL geometry will be integrated once the Task 11 team
> confirms and provides authoritative machine-readable boundary data (GeoJSON / Shapefile).

---

## 3. What Has Been Implemented

### Milestone 1 — Flutter UI Foundation

A complete, production-quality Android mobile UI built with Flutter:

- **Design system** (`lib/app/theme.dart`) — all colours, text styles, and component styles defined in one place using `SamudraColors` and `SamudraTheme`. Nothing is hardcoded in screens.
- **Home screen** — greeting, AI input bar (`AskSamudra` widget), suggestion chips, quick-action grid, and a live status card.
- **Slide-out sidebar** (`SamudraDrawer`) — ChatGPT-style drawer, hidden by default, opens on hamburger tap or left-edge swipe.
- **Bottom navigation** — Home, Assistant, Map, Safety tabs.
- **Screens**: Assistant, Marine Map, Trip Brief, Safety Alerts, Offline Access, Settings.
- **Reusable widgets**: `AskSamudra`, `SuggestionCard`, `QuickActionCard`, `SafetyStatusCard`, `SamudraDrawer`.

> Before creating any new UI component, inspect `lib/widgets/` and `lib/app/theme.dart`.
> Reuse what exists before adding new widgets.

---

### Milestone 2 — GPS / GNSS Location

Real device GPS via the `geolocator` package (v14.0.3).

**What is acquired:**
| Field | Unit | Notes |
|-------|------|-------|
| Latitude | decimal degrees (WGS-84) | positive = North |
| Longitude | decimal degrees (WGS-84) | positive = East |
| Accuracy | metres (1-sigma) | horizontal only |
| Speed | m/s (converted to knots) | 0.0 when unavailable |
| Heading | degrees true (0–360) | 0.0 when unavailable |
| Timestamp | UTC → displayed as IST | stored in UTC internally |

**Timestamp convention:**
Timestamps are stored and processed in **UTC** throughout the application.
They are converted to **IST (UTC+05:30)** only at the display layer using:
```dart
final ist = utc.toUtc().add(const Duration(hours: 5, minutes: 30));
```
Do not modify this convention without coordinating across all display points.

**GPS accuracy in practice:**
Testing on a Moto G85 5G running Android 16 showed approximately 3.5–5 m accuracy in open-sky / rooftop conditions. Indoor accuracy degraded significantly (20–100+ m). Do not assume a fixed accuracy figure — always read `LocationData.accuracy` and use it in safety decisions.

**Architecture:**
```
GPS hardware / Android GNSS
        │
  geolocator plugin
        │
   LocationService    ← singleton, started once in main.dart
        │
  locationStream / statusStream (broadcast)
        │
  Widgets subscribe — never call geolocator directly
```

`LocationService` handles permission checking, service-disabled detection, and foreground stream management. Widgets subscribe to `locationStream` and `statusStream` only.

---

### Milestone 3 — SQLite Offline Cache

Local persistence using `sqflite` (v2.4.3).

**Why sqflite:** lightweight, production-grade, no ORM overhead, direct SQL control, excellent Android support. No alternative packages were needed.

**Schema (version 2):**

```sql
-- Marine data cache
CREATE TABLE marine_data (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  data_type   TEXT    NOT NULL,      -- 'sea_surface_temp', 'wave_height', etc.
  title       TEXT    NOT NULL,
  description TEXT    NOT NULL DEFAULT '',
  latitude    REAL,                  -- nullable geographic anchor
  longitude   REAL,
  value       TEXT,                  -- measurement value (string)
  unit        TEXT,
  source      TEXT    NOT NULL,      -- 'demo', 'incois', 'imd', etc.
  timestamp   TEXT    NOT NULL,      -- ISO-8601 UTC
  expires_at  TEXT,                  -- ISO-8601 UTC, nullable
  created_at  TEXT    NOT NULL,
  updated_at  TEXT    NOT NULL
);

-- IMBL boundary polygons (added in Milestone 4)
CREATE TABLE imbl_boundaries (
  id           TEXT    PRIMARY KEY,
  name         TEXT    NOT NULL,
  region       TEXT    NOT NULL DEFAULT '',
  polygon_flat TEXT    NOT NULL,     -- flat lat/lon pairs: "lat0,lon0,lat1,lon1,..."
  source       TEXT    NOT NULL,
  updated_at   TEXT    NOT NULL,
  created_at   TEXT    NOT NULL
);
```

**Offline persistence test:**
1. Open the app → navigate to Offline Access.
2. Tap **Insert Test Data** (inserts 5 DEMO records).
3. Force-close the app.
4. Disable mobile data and Wi-Fi.
5. Reopen the app → navigate to Offline Access.
6. All 5 records are still present — confirmed offline persistence.
7. Tap **Clear Test Data** — records are removed.

This test proves **local persistence**, not production marine-data synchronization. The demo records are clearly labelled `[DEMO DATA]` and are not real measurements.

**Batch insert:**
`DatabaseService.insertAll()` wraps all inserts in a single SQLite transaction using a `Batch` object, ensuring atomicity and dramatically better performance than N individual inserts.

---

### Milestone 4 — IMBL Spatial Boundary Engine

A fully offline spatial engine for determining whether a vessel is inside, outside, or approaching a maritime boundary polygon.

**Key files:**
- `lib/models/imbl_boundary.dart` — `LatLon` point, `ImblBoundary` polygon model
- `lib/models/boundary_check_result.dart` — `BoundaryClassification` enum, `BoundaryCheckResult`
- `lib/services/imbl_boundary_service.dart` — spatial calculation engine

**Classification results:**

| Result | Meaning |
|--------|---------|
| `safe` | Conclusively inside the boundary, GPS accuracy sufficient, not near edge |
| `nearBoundary` | Within the configured warning distance of the boundary edge |
| `outside` | Conclusively outside the boundary, GPS accuracy sufficient |
| `unknown` | Cannot determine — missing data, poor GPS, or calculation error |

**Safety contract:**
`SAFE` is **never** returned when:
- Boundary data is missing or invalid
- GPS position is null
- GPS accuracy ≥ distance to boundary (× sigma factor)
- An exception occurs during calculation

When in doubt, the engine returns `UNKNOWN`.

**Algorithms:**

*Point-in-polygon:* Ray-casting (Jordan Curve Theorem).
Cast a horizontal ray from the query point in the +longitude direction.
Count edge crossings — odd = inside, even = outside.
Works for convex and concave polygons, any winding order.
Points exactly on a boundary edge are treated as inside.

*Boundary distance:* Minimum Haversine distance to any polygon edge, using a cosine-corrected local Cartesian projection per edge.
Error < 0.3% for distances under ~100 km.

*GPS accuracy guard:*
```
if distMeters > 0 AND (accuracy × sigmaFactor) >= distMeters:
    return UNKNOWN
```

**Unit tests (all passing):**

```
test/imbl_boundary_service_test.dart

✓ Point clearly inside → SAFE
✓ Point clearly outside → OUTSIDE
✓ Point on boundary edge → INSIDE / NEAR
✓ Point near boundary (444 m, threshold 500 m) → NEAR_BOUNDARY
✓ Poor GPS accuracy (500 m, boundary 444 m away) → UNKNOWN
✓ CW winding → same result as CCW
✓ CCW polygon, inside point → SAFE
✓ Null location → UNKNOWN
✓ Unknown boundary ID → UNKNOWN
✓ Invalid polygon (< 3 vertices) → ArgumentError on load
✓ Far outside point → distance > 100 km
✓ Centre-to-edge distance ≈ 55 km
✓ Haversine: equator 1° longitude ≈ 111,320 m
✓ Haversine: 1° latitude ≈ 111,195 m
```

Run tests:
```bash
flutter test test/imbl_boundary_service_test.dart --reporter expanded
```

> ⚠️ **DEMO POLYGON ONLY.**
> `lib/utils/demo_imbl.dart` contains a synthetic ~110 × 110 km rectangle
> at 10–11°N, 75.5–76.5°E (Arabian Sea, off Kerala).
> **This is not the real IMBL.** It exists only to verify the algorithm.
> Do not use it for any navigational or safety decision.

---

## 4. Architecture

```
┌─────────────────────────────────────────────┐
│                Flutter UI                    │
│  (screens / widgets — no SQL, no geometry)   │
└─────────────┬───────────────────────────────┘
              │
    ┌─────────┼──────────────────────────────┐
    ▼         ▼                              ▼
LocationService   DatabaseService    ImblBoundaryService
(GPS stream)      (SQLite CRUD)      (PIP + Haversine)
    │                 │                      │
    ▼                 ▼                      │
LocationData     MarineData             BoundaryCheckResult
                 ImblBoundary                │
                      │                     ▼
                      └──────► Future BackgroundMonitor (M5)
                                            │
                                            ▼
                               Future AlertService (M6)
                                            │
                                            ▼
                               Future FastAPI Backend (M8)
```

**Layer responsibilities:**

| Layer | Responsibility | Must NOT contain |
|-------|---------------|-----------------|
| Screens | Display data, handle user input | SQL, GPS calls, polygon math |
| Widgets | Reusable UI components | Business logic, SQL, GPS |
| Services | All business logic | Flutter UI widgets, direct DB calls from GPS |
| Models | Data structures + serialisation | Business logic |
| Utils | Demo/test data factories | Production data |

---

## 5. Project Structure

```
samudra_ai/
├── lib/
│   ├── main.dart                        Entry point — init DB, start GPS, launch app
│   ├── app/
│   │   ├── app.dart                     MaterialApp + theme setup
│   │   └── theme.dart                   SamudraColors + SamudraTheme (design system)
│   │
│   ├── models/
│   │   ├── location_data.dart           GPS fix (lat, lon, accuracy, speed, heading)
│   │   ├── marine_data.dart             SQLite marine cache row model
│   │   ├── imbl_boundary.dart           LatLon + ImblBoundary polygon model
│   │   └── boundary_check_result.dart   BoundaryClassification enum + check result
│   │
│   ├── services/
│   │   ├── location_service.dart        GPS singleton — stream + permission handling
│   │   ├── database_service.dart        SQLite singleton — all CRUD lives here
│   │   └── imbl_boundary_service.dart   Spatial engine — PIP, Haversine, accuracy guard
│   │
│   ├── screens/
│   │   ├── home/home_screen.dart        Home tab — greeting, AI input, actions, status
│   │   ├── assistant/assistant_screen.dart  AI chat placeholder
│   │   ├── marine_map/marine_map_screen.dart  Chart placeholder
│   │   ├── trip_brief/trip_brief_screen.dart  Voyage planning placeholder
│   │   ├── safety/safety_screen.dart    Safety alerts placeholder
│   │   ├── offline/offline_screen.dart  Offline cache + dev test panel
│   │   └── settings/settings_screen.dart  GPS test + IMBL test + app settings
│   │
│   ├── widgets/
│   │   ├── samudra_drawer.dart          Slide-out sidebar navigation
│   │   ├── ask_samudra.dart             AI input bar (mic + send)
│   │   ├── suggestion_card.dart         Tappable suggestion chip
│   │   ├── quick_action_card.dart       Icon + label action tile
│   │   └── safety_status_card.dart      Animated pulsing status card
│   │
│   └── utils/
│       ├── demo_data.dart               ⚠️ DEMO marine data — not real measurements
│       └── demo_imbl.dart               ⚠️ DEMO IMBL polygon — not a real boundary
│
├── test/
│   └── imbl_boundary_service_test.dart  14 unit tests for spatial engine
│
├── assets/
│   └── images/
│       └── samudra_logo.png             App logo (replace placeholder with official)
│
├── android/                             Android build configuration
├── local_packages/
│   └── geolocator_linux_stub/           No-op stub — prevents cross-drive Kotlin error
│
└── pubspec.yaml                         Dependencies
```

**Where to place new work:**

| What you're adding | Where it goes |
|-------------------|---------------|
| New data model | `lib/models/` |
| New service / business logic | `lib/services/` |
| New screen | `lib/screens/<feature>/` |
| New reusable widget | `lib/widgets/` |
| Test data / stubs | `lib/utils/` (clearly labelled DEMO) |
| Unit / widget tests | `test/` |

---

## 6. Setup on a New PC (Windows)

### Prerequisites

You need: **Git**, **Flutter SDK**, **Android Studio**, **Android SDK**, and a **JDK** (JDK 17 recommended — Flutter's current Gradle requires it).

---

### Step 1 — Install Git

Download from https://git-scm.com and install with default settings.
Verify:
```bash
git --version
```

---

### Step 2 — Install Flutter SDK

1. Download the latest stable Flutter SDK from https://docs.flutter.dev/get-started/install/windows
2. Extract to a folder **without spaces** and **without admin-protected paths**, e.g. `C:\src\flutter`
3. Add `C:\src\flutter\bin` to your **System PATH**:
   - Search → "Edit the system environment variables"
   - Environment Variables → System variables → Path → Edit → New → `C:\src\flutter\bin`
4. Restart your terminal.

Verify:
```bash
flutter --version
```

---

### Step 3 — Install Android Studio

1. Download from https://developer.android.com/studio
2. Install with default settings
3. On first launch, complete the Android Studio Setup Wizard — it installs the Android SDK automatically

---

### Step 4 — Configure Android SDK

In Android Studio:
- **File → Settings → Appearance & Behavior → System Settings → Android SDK**
- Under **SDK Platforms**: install Android API 34 (or latest stable)
- Under **SDK Tools**: ensure these are checked:
  - Android SDK Build-Tools
  - Android SDK Platform-Tools
  - Android SDK Command-line Tools (latest)
  - Android Emulator (if you want to use a virtual device)

---

### Step 5 — Accept Android Licenses

Open a terminal and run:
```bash
flutter doctor --android-licenses
```
Press `y` to accept all licenses.

---

### Step 6 — Run Flutter Doctor

```bash
flutter doctor
```

All items should show a green tick except iOS (which is not needed for this project).
Common issues:
- **Android toolchain — no licenses**: Run `flutter doctor --android-licenses`
- **Android Studio not found**: Set `ANDROID_HOME` or `ANDROID_SDK_ROOT` to your SDK path
- **cmdline-tools not installed**: Install via SDK Manager (Step 4)

---

### Step 7 — Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd samudra_ai
```

---

### Step 8 — Install Dependencies

```bash
flutter pub get
```

> **Note about `dependency_overrides`:**
> `pubspec.yaml` contains `geolocator_linux: path: local_packages/geolocator_linux_stub`.
> This is intentional — it prevents a Kotlin incremental-cache error that occurs on Windows
> when the Flutter project is on a different drive (e.g. `D:\`) from the pub cache (`C:\`).
> Do not remove it.

---

### Step 9 — Connect a Device or Start an Emulator

Physical device (recommended for GPS):
- Enable USB debugging (see Section 7)
- Connect via USB

Emulator:
- Open Android Studio → Device Manager → Create Virtual Device
- Choose a phone profile (Pixel 6 or similar), download a system image, finish

Verify:
```bash
flutter devices
```

---

### Step 10 — Run the App

```bash
flutter run
```

Or in **Android Studio**: open the project folder, select your device from the device dropdown, press the Run button (▶).

---

### Step 11 — Run Unit Tests

```bash
flutter test
```

Or to run just the IMBL spatial tests:
```bash
flutter test test/imbl_boundary_service_test.dart --reporter expanded
```

---

## 7. Running on a Physical Android Phone

GPS accuracy is significantly better on a real device outdoors. Always use a physical phone for GPS and IMBL testing.

### Enable Developer Options

1. Go to **Settings → About phone**
2. Tap **Build number** seven times
3. You will see "You are now a developer"
4. Go to **Settings → Developer options**

### Enable USB Debugging

1. In **Developer options**, enable **USB debugging**
2. Connect the phone to your PC via USB
3. On the phone, accept the "Allow USB debugging?" dialog
4. Select "Always allow from this computer"

### Verify connection

```bash
flutter devices
```

Your phone should appear in the list.

### Run

```bash
flutter run
```

To target a specific device:
```bash
flutter run -d <device-id>
```

### GPS testing notes

- **Test outdoors / open sky** for best accuracy (typically 3–5 m on modern Android devices)
- Indoor GPS is often 20–100+ m — do not treat indoor readings as representative
- The app requests `ACCESS_FINE_LOCATION` (foreground only — background not yet enabled)
- GPS fixes update every 5 seconds or when the device moves more than 5 metres
- Always grant location permission when prompted

---

## 8. Demo Walkthrough

> ⚠️ **All demo data is synthetic. Do not use for navigation or safety decisions.**

### Current demo sequence

**Step 1 — Open the app**
The home screen shows a greeting, the AI input bar, suggestion chips, quick actions, and a status card showing GPS status.

**Step 2 — Check GPS (Settings)**
Open the sidebar → Settings.
The **GPS Development Test** panel (Milestone 2) shows:
- Live latitude, longitude, accuracy
- Speed (m/s and knots)
- Heading
- Last Updated in IST

Tap **Refresh** to force a new GPS fix.

**Step 3 — Offline data (Offline Access)**
Quick Actions → Offline Access (or sidebar → Offline Packs).
- Tap **Insert Test Data** — inserts 5 DEMO records (SST, chlorophyll, wave height, wind speed, salinity)
- Records appear with `DEMO` badge
- Kill the app, re-open, disable internet — records are still there
- Tap **Clear Test Data** to remove them

These are not real oceanographic measurements.

**Step 4 — IMBL Boundary Test (Settings)**
Sidebar → Settings → scroll to **IMBL Boundary Test** panel (Milestone 4, amber border).
- The DEMO polygon is loaded automatically
- Your current GPS coordinates are shown
- Tap **Run Boundary Check**
- The result shows:
  - Latitude / Longitude
  - GPS Accuracy
  - Distance to Boundary
  - Status: `SAFE` / `NEAR BOUNDARY` / `OUTSIDE` / `UNKNOWN`

Since the demo polygon covers 10–11°N, 75.5–76.5°E, most locations in India will show `OUTSIDE`. If you are near Kerala you may see `NEAR BOUNDARY`.

> ⚠️ The DEMO IMBL test zone is a synthetic rectangle used only to verify the algorithm.
> It is **not a real maritime boundary**.

---

## 9. Frontend Contributor Guide

### Current state

The Flutter UI foundation is complete. Screens exist for all planned features, but most are in a **placeholder state** — they display the correct visual design but are not yet connected to real data or backend APIs.

### What needs to happen next (frontend)

1. **Replace hardcoded/demo content** with real data from services and eventually from the backend API
2. **Add loading states** — every screen that fetches data needs a skeleton or spinner
3. **Add error states** — what does the user see when GPS fails? When offline data is empty? When the backend is unreachable?
4. **Add empty states** — design appropriate empty-state UI for each screen
5. **Prepare API-facing models** — extend `lib/models/` to deserialize backend JSON cleanly
6. **Marine map** — integrate a real map widget with tile data
7. **Safety alert UI** — connect to real alert data when available
8. **Background monitoring status** — home screen status card needs to reflect real-time safety state (Milestone 5)

### How frontend will eventually connect to the backend

```
Flutter UI
    │
    ▼
Repository / API service layer (to be created in lib/services/)
    │
    ▼
FastAPI (HTTP/JSON)
    │
    ▼
Backend services / Agentic AI / Marine data
    │
    ▼
JSON response
    │
    ▼
Dart model (fromMap / fromJson)
    │
    ▼
UI
```

Design your models now so they can absorb backend JSON cleanly later.
Every model should have a `fromMap(Map<String, dynamic>)` constructor.

### Rules for frontend contributors

- **Read `lib/app/theme.dart` before hardcoding any colour or text style.** Use `SamudraColors.*` and `Theme.of(context).textTheme.*`.
- **Read `lib/widgets/` before building a new component.** `QuickActionCard`, `SuggestionCard`, `SafetyStatusCard` are reusable.
- **Never write SQL inside a widget.** All database access goes through `DatabaseService`.
- **Never write GPS logic inside a widget.** Subscribe to `LocationService.locationStream` or `statusStream`.
- **Never write polygon math inside a widget.** Use `ImblBoundaryService.check()`.
- Do not connect to fake backend endpoints unless they are clearly marked as mock/development.

---

## 10. Backend Contributor Guide

The FastAPI backend is being developed separately. The Flutter app will communicate with it over HTTP/JSON when connectivity is available, while falling back to local SQLite data when offline.

### Expected integration pattern

```
Flutter HTTP client (to be implemented in lib/services/)
    │
    ▼
POST/GET https://<api-domain>/v1/...
    │
    ▼
FastAPI
    │
    ├── Agentic AI (marine queries)
    ├── Marine data ingestion (INCOIS, IMD, etc.)
    ├── IMBL geometry store
    └── User/trip management
    │
    ▼
JSON response → Flutter model → UI
```

### What backend contributors need to provide

For every API endpoint, document:

```
Method:           GET / POST / etc.
Path:             /v1/marine/forecast
Auth:             Bearer token / API key / none
Request params:   lat (float), lon (float), radius_km (float)
Request body:     { ... }
Response body:    { "data": [...], "source": "incois", "generated_at": "2024-..." }
Error response:   { "error": "...", "code": 404 }
Timestamp format: ISO-8601 UTC (e.g. "2024-08-29T14:30:00Z")
Units:            metres, knots, °C, PSU — explicitly stated
Source:           data origin and provenance
```

### Timestamp standard

The app uses **UTC internally** for all timestamps. Backend responses must include UTC timestamps. The app converts to IST at the display layer.

### Offline-first requirement

The API integration must be designed so the app **works fully without the backend**. Backend data supplements local SQLite data — it does not replace it. When the backend is unreachable, the app must continue functioning with cached data.

---

## 11. Data Sourcing Requirements

> **For the data/backend team — this is critical blocking work.**

The following datasets need to be identified, verified, and made available in machine-readable form. Screenshots and web pages are not sufficient — the team needs downloadable GIS files or authenticated API access.

Use this template for each dataset:

```
Name:
Provider:
Official source URL:
Format:             GeoJSON / Shapefile / KML / REST API / CSV
Download/API method:
Update frequency:
Spatial resolution:
Temporal resolution:
Units:
Coordinate system:  EPSG:4326 (WGS-84) or other
License / usage:
Authentication:
Rate limits:
Example file/response:
Last verified:
```

---

### Priority 1 — Real IMBL / Maritime Boundary Geometry

**This is the single most important missing dataset for Task 15.**

The app's spatial engine is ready to consume real boundary geometry — the engine is not the blocker. The data is.

What to look for:
- Authoritative polygon geometry in GeoJSON, Shapefile, or KML format
- Published by: Ministry of External Affairs (MEA), Indian Navy, INCOIS, Survey of India, or a recognised international GIS source
- Verify the coordinate reference system (CRS) — must be WGS-84 (EPSG:4326) or convertible
- Confirm it is the **IMBL (International Maritime Boundary Line)**, not just the EEZ
- EEZ and IMBL are **not automatically the same** — verify which boundary is legally relevant for fishermen safety
- Consider checking MarineRegions.org (https://www.marineregions.org) for standardised maritime boundary layers
- Check if INCOIS publishes any GIS boundary layers alongside their PFZ data

Do NOT add any boundary geometry to production based on an unverified source.

---

### Priority 2 — INCOIS Marine Datasets

Indian National Centre for Ocean Information Services (https://incois.gov.in)

Look for machine-readable API or download access to:
- Potential Fishing Zone / PFZ advisories
- Ocean State Forecast (OSF)
- Significant wave height
- Sea surface temperature (SST)
- Ocean currents
- Marine meteorological alerts
- Buoy and in-situ observation data

Check if INCOIS has an authenticated REST API or FTP/SFTP download. Check data formats (NetCDF, JSON, CSV, GeoJSON).

---

### Priority 3 — ISRO / MOSDAC Data

Space Applications Centre / MOSDAC (https://mosdac.gov.in)

Look for:
- Oceansat / ScatSat satellite observations
- INSAT-3D/3DR marine/weather products
- Machine-readable download or API access

---

### Priority 4 — IMD Fishermen Warnings

India Meteorological Department (https://mausam.imd.gov.in)

Look for:
- Cyclone and disturbance tracking
- Fishermen warnings for specific sea areas
- Weather bulletins in structured (JSON/XML) rather than PDF format
- Historical data for model training

---

### Priority 5 — NOAA and International Validation Data

Where required for model validation or gap-filling:
- NOAA ERDDAP datasets (https://coastwatch.pfeg.noaa.gov/erddap)
- HYCOM ocean model output
- Copernicus Marine Service (CMEMS) for global products
- Global buoy data (WMO/GTS) for in-situ validation

---

### Priority 6 — Geographic / Hazard Zone Layers

- Protected marine areas / wildlife sanctuaries
- Shipping lane corridors
- Known hazard zones (shoals, wrecks, restricted military areas)
- Port approach corridors

---

## 12. Real IMBL Data Integration Plan

### Current (Milestone 4)

```
DemoImbl.polygon()          ← synthetic rectangle (dev testing only)
        │
ImblBoundaryService.check()  ← algorithm verified, all 14 tests passing
        │
BoundaryCheckResult          ← SAFE / NEAR / OUTSIDE / UNKNOWN
```

### Future (when authoritative data is available)

```
Real IMBL dataset (GeoJSON / Shapefile)
        │
        ▼
Validate CRS (must be WGS-84)
        │
        ▼
Validate geometry type (Polygon / MultiPolygon)
        │
        ▼
Parse to List<LatLon> — use LatLon.fromGeoJsonCoord() for GeoJSON
        │
        ▼
ImblBoundary object
        │
        ▼
DatabaseService.saveBoundary()  ← stores to imbl_boundaries table
        │
        ▼
ImblBoundaryService.loadBoundary()  ← loads into memory
        │
        ▼
Real GPS → ImblBoundaryService.check() → safety classification
```

**Critical:** Do **not** rewrite the IMBL engine when the real dataset arrives. The engine is designed to accept any valid `ImblBoundary` object. The only work required is:
1. Parse the real geometry into `LatLon` coordinates
2. Handle MultiPolygon if the boundary consists of multiple segments (support documented for a future milestone)
3. Store to SQLite and load into `ImblBoundaryService`

---

## 13. Deferred and Pending Work

| Feature | Status | Reason | Current alternative |
|---------|--------|--------|---------------------|
| Real IMBL dataset | ⏳ Waiting for data | Task 11 team has not confirmed authoritative machine-readable geometry | DEMO polygon for algorithm testing |
| Background monitoring | 🔜 Next milestone | Requires verified IMBL geometry + foreground service implementation | Foreground test in Settings screen |
| 105 dB local emergency buzzer | 🔲 Pending | Depends on background breach detection | None yet |
| NavIC / NMEA integration | 🔲 Pending / Investigation | Requires verifying actual device hardware GNSS capabilities and Android raw NMEA access — not all phones support this | Standard Android GNSS via geolocator |
| Backend API integration | 🔲 Pending | FastAPI backend in separate development | Local SQLite + demo data |
| Real marine API data | 🔲 Pending | Data contracts and API endpoints not yet established | DEMO records labelled clearly |
| < 15 ms IMBL benchmark | 🔲 Pending | Correctness prioritised over performance; real production geometry needed first | Engine correctness verified with 14 tests |

---

## 14. Task 15 Roadmap

| Phase | Milestone | Status |
|-------|-----------|--------|
| 1 | Flutter Android UI | ✅ Done |
| 2 | GPS / GNSS location | ✅ Done |
| 3 | SQLite offline cache | ✅ Done |
| 4 | IMBL spatial engine | ✅ Done |
| 5 | Background monitoring | 🔜 Next |
| 6 | Local emergency alert | 🔲 Pending |
| 7 | NavIC / NMEA investigation | 🔲 Pending |
| 8 | Real IMBL dataset integration | ⏳ Waiting for data |
| 9 | FastAPI / backend integration | 🔲 Pending |
| 10 | Performance benchmarking | 🔲 Pending |
| 11 | End-to-end offline safety demo | 🔲 Pending |

---

## 15. Git and Contribution Workflow

### Before starting

```bash
git pull
```
Always pull before creating a new branch.

### Create a feature branch

```bash
git checkout -b feature/<short-name>
# Examples:
git checkout -b feature/background-monitor
git checkout -b feature/marine-map-tiles
git checkout -b feature/api-service
```

### After making changes

```bash
git status
git add .
git commit -m "feat: <description of what you did>"
```

Use conventional commit prefixes:
- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code change that doesn't add a feature or fix a bug
- `test:` — adding or updating tests
- `docs:` — documentation only

### Push and create a pull request

```bash
git push -u origin feature/<short-name>
```
Then open a pull request on the repository.

### Team rules

- Do not directly push to `main` or `develop`
- Do not modify another contributor's active feature branch without coordination
- Keep commits small and focused
- Do not commit secrets, API keys, or production credentials
- Do not commit generated build files (`build/`, `.dart_tool/`)
- Do not replace real data with fake data silently — always label DEMO/TEST data clearly
- If you change the database schema, increment `_kDbVersion` in `database_service.dart` and add a migration in `_onUpgrade`

---

## 16. Environment and Secrets

Currently, the app has **no external API connections** and no secrets management layer.

When backend integration begins:
- API base URLs, keys, and tokens must **not** be hardcoded in source code
- Use a `.env` file approach, Flutter `--dart-define`, or a secrets management tool
- Add `.env` to `.gitignore` before creating it
- Document which environment variables are required (without their values) in this README

> **Backend/API environment configuration will be added during Milestone 9 (backend integration).**

---

## 17. Development Rules

1. **Do not invent production data.** If you need data for testing, use `DemoData` or `DemoImbl` and clearly label it.
2. **Label all demo/mock data.** Source field = `'demo'`, description contains `[DEMO DATA]`.
3. **Do not claim a safety feature is production-ready until it has been tested on real data and real hardware.**
4. **Keep GPS logic in `LocationService`.** Widgets subscribe to streams — they do not call geolocator.
5. **Keep SQL in `DatabaseService`.** No raw queries in screens or widgets.
6. **Keep polygon calculations in `ImblBoundaryService`.** No geometry in UI code.
7. **Keep backend logic in service classes.** Widgets display results, not business logic.
8. **Reuse existing services and models.** Check `lib/services/` and `lib/models/` before creating new files.
9. **Test on a physical Android device** for GPS, background behaviour, and real-world accuracy.
10. **Preserve offline functionality.** The app must work with zero connectivity.
11. **UTC internally, IST for display.** Do not change this convention without coordinating the change everywhere.
12. **Document data sources.** Every real dataset added must include source, provenance, update frequency, and licence.
13. **Do not silently change existing architecture.** Discuss structural changes before implementing.
14. **Test before committing.** Run `flutter analyze` and `flutter test` before every push.

```bash
flutter analyze
flutter test
```

---

## 18. Troubleshooting

### `flutter` command not recognised

```
flutter : The term 'flutter' is not recognized...
```
- Verify `flutter/bin` is in your system PATH (not user PATH)
- Restart your terminal after editing PATH
- Run `flutter doctor` to confirm the SDK is found

---

### No Android device found

```
No devices found
```
- Check USB cable (use data cable, not charge-only)
- Check that USB Debugging is enabled in Developer Options
- Accept the "Allow USB debugging?" dialog on the phone
- Run `adb devices` to confirm ADB sees the device
- Try a different USB port or cable

---

### GPS shows `--` or UNKNOWN

- Grant location permission when prompted
- Move to an outdoor / open-sky area
- Wait 10–30 seconds for a GNSS fix
- Check that Location (GPS) is enabled in Android Settings
- Indoor GPS accuracy can be 20–100+ m and may trigger the UNKNOWN confidence guard

---

### SQLite data missing after update

- If the database schema version changed (`_kDbVersion` incremented), the migration in `_onUpgrade` must handle the upgrade
- If the app was uninstalled and reinstalled, the database is erased — this is expected
- If the app was force-stopped without proper disposal, the database file is intact and data is preserved

---

### Build fails with Kotlin incremental cache error

```
Could not close incremental caches in D:\...\package_info_plus\kotlin\...
```
This is a known issue on Windows when the Flutter project is on a different drive (`D:\`) from the pub cache (`C:\Users\...\Pub\Cache`). The fix is already in `pubspec.yaml`:

```yaml
dependency_overrides:
  geolocator_linux:
    path: local_packages/geolocator_linux_stub
```

If it recurs, run:
```bash
flutter clean
flutter pub get
```
And kill any lingering Java processes before rebuilding.

---

### Background GPS doesn't work

- `ACCESS_BACKGROUND_LOCATION` permission is **intentionally not requested** until Milestone 5
- Do not test background behaviour on an emulator — emulator GNSS simulation differs significantly from real hardware
- Android 10+ requires explicit `ACCESS_BACKGROUND_LOCATION` and a foreground notification for background location

---

## 19. Where Can I Contribute?

### Frontend contributors

Focus on:
- Building the real marine map view (Milestone 9 prep)
- Safety alert screen connected to real data
- Background monitoring status UI (Milestone 5 prep)
- Loading, error, empty, and offline states across all screens
- API-ready model extensions (`fromJson` methods)
- Improving accessibility and internationalisation

### Backend contributors

Focus on:
- FastAPI service design and endpoint documentation
- Marine data ingestion pipelines (INCOIS, IMD, ISRO/MOSDAC)
- Agent service for natural-language marine queries
- API contract documentation for Flutter integration
- Real IMBL geometry processing (GeoJSON/Shapefile → `ImblBoundary`)
- Authentication and rate-limiting design

### Mobile / edge contributors

Focus on:
- Background monitoring service (Milestone 5)
- Android foreground service with persistent notification
- Local emergency alert / buzzer (Milestone 6)
- NavIC / raw NMEA investigation on supported hardware (Milestone 7)
- IMBL performance benchmarking with real polygon data (Milestone 10)

### Data contributors

Focus on:
- Locating authoritative IMBL geometry (highest priority)
- Verifying INCOIS API access (PFZ, OSF, wave data)
- Documenting ISRO/MOSDAC satellite data availability
- Verifying IMD structured fishermen warning data
- Completing the dataset template (Section 11) for every source
- Confirming CRS, update frequency, licence, and rate limits for each dataset

---

*SAMUDRA AI — Built for the sea. Works without the internet.*
