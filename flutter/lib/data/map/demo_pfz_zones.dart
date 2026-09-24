import '../../models/map/pfz_zone.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DemoPfzZones — ported from the source branch's `mock/mockPFZ.ts`
// (Project ORCA web frontend).
//
// ⚠️ These are DEMO polygons only — they are the same synthetic PFZ sectors
// used by the source branch for development, NOT live data, and must not be
// used for navigation or decisions.  The backend will provide real zones.
// ─────────────────────────────────────────────────────────────────────────────

class DemoPfzZones {
  DemoPfzZones._();

  /// High-level region presets (centre + default zoom) for initial camera.
  static const List<({String id, String name, double lat, double lng, double zoom})>
      regionPresets = [
    (
      id: 'arabian-sea',
      name: 'Arabian Sea Central Basin',
      lat: 12.5,
      lng: 71.0,
      zoom: 5.5,
    ),
    (
      id: 'kerala-coast',
      name: 'Kerala Coast & South Shelf',
      lat: 9.8,
      lng: 75.8,
      zoom: 7.0,
    ),
    (
      id: 'bay-of-bengal',
      name: 'Bay of Bengal Deep Basin',
      lat: 13.5,
      lng: 85.0,
      zoom: 5.5,
    ),
    (
      id: 'tamil-nadu',
      name: 'Tamil Nadu & Coromandel Coast',
      lat: 11.5,
      lng: 80.5,
      zoom: 7.0,
    ),
    (
      id: 'lakshadweep',
      name: 'Lakshadweep Archipelago Shelf',
      lat: 10.5,
      lng: 73.0,
      zoom: 7.2,
    ),
    (
      id: 'sri-lanka',
      name: 'Gulf of Mannar & Sri Lanka Basin',
      lat: 8.5,
      lng: 79.5,
      zoom: 6.8,
    ),
  ];

  /// Default camera centre/zoom (Arabian Sea) used when GPS is unavailable.
  static const ({double lat, double lng, double zoom}) defaultCamera = (
    lat: 12.5,
    lng: 71.0,
    zoom: 5.5,
  );

  static const List<PfzZone> zones = [
    PfzZone(
      id: 'ZONE-001',
      name: 'Kochi-South Shelf Front',
      sector: 'Kerala Coast (Sector K2)',
      latitude: 9.6,
      longitude: 76.0,
      score: 84,
      classification: PfzClassification.high,
      confidence: ConfidenceLevel.high,
      primaryFactor: 'CHLOROPHYLL CONVERGENCE',
      status: PfzZoneStatus.demo,
      timestamp: '2026-08-29T00:00:00Z',
      geometry: PfzGeometry([
        [75.6, 9.9],
        [76.3, 9.8],
        [76.2, 9.3],
        [75.5, 9.4],
        [75.6, 9.9],
      ]),
      metrics: PfzMetrics(
        sst: 28.6,
        sstAnomaly: 0.45,
        chlorophyll: 0.58,
        waveHeight: 1.4,
        currentVelocity: 'UNAVAILABLE',
        depthMeters: 45,
      ),
      factors: [
        PfzFactor(
          name: 'SST Gradient',
          weight: 80,
          status: 'FAVORABLE',
          description: 'Thermal front detected: 0.65°C / 10 km at shelf break',
          source: 'Copernicus OSTIA L4 NRT',
          isReal: true,
        ),
      ],
    ),
    PfzZone(
      id: 'ZONE-002',
      name: 'Lakshadweep East Passage',
      sector: 'Lakshadweep Sea (Sector L4)',
      latitude: 10.35,
      longitude: 73.3,
      score: 76,
      classification: PfzClassification.high,
      confidence: ConfidenceLevel.high,
      primaryFactor: 'THERMAL EDDY BOUNDARY',
      status: PfzZoneStatus.demo,
      timestamp: '2026-08-29T00:00:00Z',
      geometry: PfzGeometry([
        [72.9, 10.6],
        [73.6, 10.5],
        [73.5, 10.1],
        [72.8, 10.2],
        [72.9, 10.6],
      ]),
      metrics: PfzMetrics(
        sst: 28.9,
        sstAnomaly: 0.25,
        chlorophyll: 0.42,
        waveHeight: 1.6,
        currentVelocity: 'UNAVAILABLE',
        depthMeters: 120,
      ),
      factors: [
        PfzFactor(
          name: 'SST Gradient',
          weight: 80,
          status: 'FAVORABLE',
          description: 'Mesoscale cyclonic eddy periphery gradient 0.45°C / 12 km',
          source: 'Copernicus OSTIA L4 NRT',
          isReal: true,
        ),
      ],
    ),
    PfzZone(
      id: 'ZONE-003',
      name: 'Vizhinjam Coastward Upwelling',
      sector: 'South Kerala Shelf (Sector V1)',
      latitude: 8.15,
      longitude: 76.8,
      score: 68,
      classification: PfzClassification.moderate,
      confidence: ConfidenceLevel.medium,
      primaryFactor: 'COASTAL UPWELLING FRONT',
      status: PfzZoneStatus.demo,
      timestamp: '2026-08-29T00:00:00Z',
      geometry: PfzGeometry([
        [76.5, 8.4],
        [77.1, 8.3],
        [77.0, 7.9],
        [76.4, 8.0],
        [76.5, 8.4],
      ]),
      metrics: PfzMetrics(
        sst: 27.8,
        sstAnomaly: -0.65,
        chlorophyll: 0.65,
        waveHeight: 2.1,
        currentVelocity: 'UNAVAILABLE',
        depthMeters: 60,
      ),
      factors: [
        PfzFactor(
          name: 'Chlorophyll-a Convergence',
          weight: 80,
          status: 'FAVORABLE',
          description: 'Elevated nutrient bloom (0.65 mg/m³)',
          source: 'Copernicus BGC L4 NRT',
          isReal: true,
        ),
      ],
    ),
    PfzZone(
      id: 'ZONE-004',
      name: 'Gulf of Mannar Pelagic Ridge',
      sector: 'Sri Lanka Basin (Sector M3)',
      latitude: 8.85,
      longitude: 79.15,
      score: 62,
      classification: PfzClassification.moderate,
      confidence: ConfidenceLevel.medium,
      primaryFactor: 'CHLOROPHYLL JET',
      status: PfzZoneStatus.demo,
      timestamp: '2026-08-29T00:00:00Z',
      geometry: PfzGeometry([
        [78.8, 9.1],
        [79.5, 9.0],
        [79.4, 8.6],
        [78.7, 8.7],
        [78.8, 9.1],
      ]),
      metrics: PfzMetrics(
        sst: 29.2,
        sstAnomaly: 0.30,
        chlorophyll: 0.38,
        waveHeight: 1.3,
        currentVelocity: 'UNAVAILABLE',
        depthMeters: 30,
      ),
      factors: [
        PfzFactor(
          name: 'Wave Conditions',
          weight: 40,
          status: 'FAVORABLE',
          description: 'Sheltered shallow water sea state (1.3 m Hm0)',
          source: 'Copernicus WAV L4 NRT',
          isReal: true,
        ),
      ],
    ),
    PfzZone(
      id: 'ZONE-005',
      name: 'Central Arabian Gyre Boundary',
      sector: 'Deep Basin (Sector A1)',
      latitude: 14.2,
      longitude: 67.8,
      score: 46,
      classification: PfzClassification.low,
      confidence: ConfidenceLevel.low,
      primaryFactor: 'DIFFUSE THERMAL BOUNDARY',
      status: PfzZoneStatus.demo,
      timestamp: '2026-08-29T00:00:00Z',
      geometry: PfzGeometry([
        [67.0, 14.6],
        [68.6, 14.5],
        [68.4, 13.8],
        [66.8, 13.9],
        [67.0, 14.6],
      ]),
      metrics: PfzMetrics(
        sst: 28.2,
        sstAnomaly: -0.10,
        chlorophyll: 0.18,
        waveHeight: 2.4,
        currentVelocity: 'UNAVAILABLE',
        depthMeters: 3200,
      ),
      factors: [
        PfzFactor(
          name: 'SST Gradient',
          weight: 80,
          status: 'MODERATE',
          description: 'Weak offshore thermal frontal boundary',
          source: 'Copernicus OSTIA L4 NRT',
          isReal: true,
        ),
      ],
    ),
  ];
}
