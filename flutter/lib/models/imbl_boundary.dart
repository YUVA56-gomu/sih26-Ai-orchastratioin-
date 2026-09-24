// ─────────────────────────────────────────────────────────────────────────────
// ImblBoundary — geographic polygon model for IMBL boundary data.
//
// Coordinate convention (CRITICAL — do not mix):
//   Every point is stored as (latitude, longitude) in decimal degrees (WGS-84).
//   Latitude  positive = North,  negative = South.
//   Longitude positive = East,   negative = West.
//   This matches GeoJSON's [longitude, latitude] ordering but reversed:
//   GeoJSON arrays are [lon, lat]; LatLon objects here are (lat, lon).
//
// Polygon winding order:
//   The point-in-polygon algorithm works for both clockwise (CW) and
//   counter-clockwise (CCW) vertex ordering.  No normalisation required.
//
// MultiPolygon limitation (Milestone 4):
//   Only simple Polygon geometries are supported in this milestone.
//   MultiPolygon support (e.g. island groups) is documented for Milestone 7.
// ─────────────────────────────────────────────────────────────────────────────

/// A single (latitude, longitude) coordinate pair.
class LatLon {
  final double lat;
  final double lon;

  const LatLon(this.lat, this.lon);

  /// Construct from a GeoJSON-style [lon, lat] list.
  factory LatLon.fromGeoJsonCoord(List<double> coord) {
    assert(coord.length >= 2, 'GeoJSON coordinate must have [lon, lat]');
    return LatLon(coord[1], coord[0]); // GeoJSON is [lon, lat]
  }

  /// Convert back to GeoJSON [lon, lat] for serialisation.
  List<double> toGeoJsonCoord() => [lon, lat];

  Map<String, dynamic> toMap() => {'lat': lat, 'lon': lon};

  factory LatLon.fromMap(Map<String, dynamic> m) =>
      LatLon(m['lat'] as double, m['lon'] as double);

  @override
  String toString() => 'LatLon($lat, $lon)';
}

/// An IMBL geographic boundary polygon.
class ImblBoundary {
  /// Unique identifier (database primary key or named identifier).
  final String id;

  /// Human-readable name, e.g. "India–Sri Lanka Maritime Boundary (Gulf)".
  final String name;

  /// Region label for grouping, e.g. "Arabian Sea", "Bay of Bengal".
  final String region;

  /// Ordered list of (lat, lon) vertices forming the closed polygon.
  /// The first and last point may or may not be identical — the engine
  /// treats the polygon as implicitly closed.
  final List<LatLon> polygon;

  /// Data origin, e.g. 'demo', 'incois', 'mea_india'.
  final String source;

  /// UTC timestamp of when this boundary data was last updated.
  final DateTime updatedAt;

  const ImblBoundary({
    required this.id,
    required this.name,
    required this.region,
    required this.polygon,
    required this.source,
    required this.updatedAt,
  });

  /// Minimum number of vertices for a valid polygon.
  static const int minVertices = 3;

  /// True if this boundary has enough vertices to form a valid polygon.
  bool get isValid => polygon.length >= minVertices;

  /// Axis-aligned bounding box — fast pre-filter before full PIP check.
  ({double minLat, double maxLat, double minLon, double maxLon})
      get boundingBox {
    double minLat = polygon.first.lat;
    double maxLat = polygon.first.lat;
    double minLon = polygon.first.lon;
    double maxLon = polygon.first.lon;
    for (final p in polygon) {
      if (p.lat < minLat) minLat = p.lat;
      if (p.lat > maxLat) maxLat = p.lat;
      if (p.lon < minLon) minLon = p.lon;
      if (p.lon > maxLon) maxLon = p.lon;
    }
    return (
      minLat: minLat,
      maxLat: maxLat,
      minLon: minLon,
      maxLon: maxLon,
    );
  }

  // ── Serialisation ─────────────────────────────────────────────────────────

  Map<String, dynamic> toMap() => {
        'id': id,
        'name': name,
        'region': region,
        // Store polygon as a flat list: [lat0, lon0, lat1, lon1, ...]
        'polygon_flat': polygon
            .expand((p) => [p.lat, p.lon])
            .toList()
            .join(','),
        'source': source,
        'updated_at': updatedAt.toUtc().toIso8601String(),
      };

  factory ImblBoundary.fromMap(Map<String, dynamic> m) {
    final flat = (m['polygon_flat'] as String)
        .split(',')
        .map(double.parse)
        .toList();
    final pts = <LatLon>[];
    for (var i = 0; i + 1 < flat.length; i += 2) {
      pts.add(LatLon(flat[i], flat[i + 1]));
    }
    return ImblBoundary(
      id: m['id'] as String,
      name: m['name'] as String,
      region: m['region'] as String,
      polygon: pts,
      source: m['source'] as String,
      updatedAt: DateTime.parse(m['updated_at'] as String).toUtc(),
    );
  }

  @override
  String toString() =>
      'ImblBoundary(id: $id, name: $name, vertices: ${polygon.length})';
}
