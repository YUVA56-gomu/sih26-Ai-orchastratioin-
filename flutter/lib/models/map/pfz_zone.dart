// ─────────────────────────────────────────────────────────────────────────────
// PfzZone — ported from the source branch's `types/pfz.ts` and
// `mock/mockPFZ.ts` (Project ORCA web frontend).
//
// Represents a Potential Fishing Zone (PFZ) candidate drawn on the map.
// The current implementation serves DEMO polygons; a future backend can supply
// real values through the same model without changing the map UI.
// ─────────────────────────────────────────────────────────────────────────────

/// Confidence level of a zone or factor.
enum ConfidenceLevel { high, medium, low }

/// Overall classification of a zone.
enum PfzClassification { high, moderate, low }

/// Status of a PFZ data record.
enum PfzZoneStatus { demo, connected, error, unavailable }

/// A polygon geometry. Coordinates are [lng, lat] pairs in the same order the
/// source branch used (GeoJSON-style [x, y]).
class PfzGeometry {
  const PfzGeometry(this.points);

  /// List of [lng, lat] pairs forming a closed ring.
  final List<List<double>> points;

  /// Convert to `latlong2` points (lat, lon) for map rendering.
  List<({double lat, double lon})> toLatLng() {
    // The source uses [lng, lat]; latlong2 uses (lat, lon).
    return points.map((p) => (lat: p[1], lon: p[0])).toList();
  }
}

class PfzMetrics {
  const PfzMetrics({
    required this.sst,
    required this.sstAnomaly,
    required this.chlorophyll,
    required this.waveHeight,
    required this.currentVelocity,
    required this.depthMeters,
  });

  final double sst;
  final double sstAnomaly;
  final double chlorophyll;
  final double waveHeight;
  final String currentVelocity;
  final double depthMeters;
}

class PfzFactor {
  const PfzFactor({
    required this.name,
    required this.weight,
    required this.status,
    required this.description,
    required this.source,
    required this.isReal,
  });

  final String name;
  final int weight;
  final String status;
  final String description;
  final String source;
  final bool isReal;
}

class PfzZone {
  const PfzZone({
    required this.id,
    required this.name,
    required this.sector,
    required this.latitude,
    required this.longitude,
    required this.score,
    required this.classification,
    required this.confidence,
    required this.primaryFactor,
    required this.status,
    required this.timestamp,
    required this.geometry,
    required this.metrics,
    required this.factors,
  });

  final String id;
  final String name;
  final String sector;
  final double latitude;
  final double longitude;
  final int score;
  final PfzClassification classification;
  final ConfidenceLevel confidence;
  final String primaryFactor;
  final PfzZoneStatus status;
  final String timestamp;
  final PfzGeometry geometry;
  final PfzMetrics metrics;
  final List<PfzFactor> factors;

  /// A short human-readable summary used in the map info panel.
  String get summary =>
      '$name · $sector\n'
      'Score $score / 100 · ${classification.name.toUpperCase()} · '
      '${confidence.name.toUpperCase()}\n'
      'SST ${metrics.sst}°C · CHL ${metrics.chlorophyll} mg/m³ · '
      'Wave ${metrics.waveHeight} m';
}
