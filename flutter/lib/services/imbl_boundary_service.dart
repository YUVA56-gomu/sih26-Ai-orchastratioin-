import 'dart:math' as math;
import '../models/imbl_boundary.dart';
import '../models/boundary_check_result.dart';
import '../models/location_data.dart';

// ─────────────────────────────────────────────────────────────────────────────
// ImblBoundaryService — offline spatial boundary engine (Milestone 4)
//
// Pipeline:
//   GPS ↓ LocationData ↓ ImblBoundaryService ↓ BoundaryCheckResult
//                                            ↓ Background monitor (M5)
//                                            ↓ Emergency alert (M6)
//
// All geometry is computed locally — no network requests during a check.
//
// ── Algorithm: Ray-Casting (Jordan Curve Theorem) ────────────────────────────
// For a query point P, cast a horizontal ray toward +∞ in longitude.
// Count how many polygon edges the ray crosses.
// Odd  → point is INSIDE  the polygon.
// Even → point is OUTSIDE the polygon.
//
// This algorithm:
//   - Works for both CW and CCW vertex ordering.
//   - Handles non-convex (concave) polygons correctly.
//   - Is deterministic and has O(n) complexity per check.
//   - Treats a point exactly on an edge as INSIDE (safe for fishermen).
//
// ── Distance calculation: Haversine ──────────────────────────────────────────
// Uses the Haversine formula on a sphere of radius 6,371,000 m.
// Sufficient for coastal distances up to ~500 km.  Maximum error ≈0.3%.
// Vincenty would be more accurate but is unnecessary for this use case.
//
// ── GPS accuracy policy ──────────────────────────────────────────────────────
// If the GPS horizontal accuracy (1-sigma) is ≥ the computed distance to
// the boundary, the result is LOW_CONFIDENCE and UNKNOWN is returned.
// The threshold can be adjusted via BoundaryCheckConfig.
// ─────────────────────────────────────────────────────────────────────────────

/// Configuration for a boundary check.
class BoundaryCheckConfig {
  /// Distance in metres at which a vessel is considered "near" the boundary
  /// even when outside.  Must be > 0.
  final double warningDistanceMeters;

  /// Multiplier applied to GPS accuracy before comparing with boundary
  /// distance.  1.0 = 1-sigma, 2.0 = 2-sigma (more conservative).
  final double accuracySigmaFactor;

  const BoundaryCheckConfig({
    this.warningDistanceMeters = 500.0,
    this.accuracySigmaFactor = 1.0,
  });
}

class ImblBoundaryService {
  ImblBoundaryService._();

  static final ImblBoundaryService instance = ImblBoundaryService._();

  // ── Loaded boundaries (in-memory cache) ──────────────────────────────────

  final Map<String, ImblBoundary> _boundaries = {};

  /// All currently loaded boundaries.
  List<ImblBoundary> get boundaries => _boundaries.values.toList();

  // ── Boundary management ───────────────────────────────────────────────────

  /// Load (or replace) a boundary in memory.
  void loadBoundary(ImblBoundary boundary) {
    if (!boundary.isValid) {
      throw ArgumentError(
          'Boundary "${boundary.id}" has fewer than '
          '${ImblBoundary.minVertices} vertices and cannot be used.');
    }
    _boundaries[boundary.id] = boundary;
  }

  /// Load multiple boundaries at once.
  void loadBoundaries(List<ImblBoundary> list) {
    for (final b in list) {
      loadBoundary(b);
    }
  }

  /// Remove a boundary from memory.
  void unloadBoundary(String id) => _boundaries.remove(id);

  /// Clear all loaded boundaries.
  void clearBoundaries() => _boundaries.clear();

  // ── Main check entry point ────────────────────────────────────────────────

  /// Check whether [location] is inside, outside, or near the boundary
  /// identified by [boundaryId].
  ///
  /// Returns [BoundaryCheckResult.unknown] when:
  ///   - [boundaryId] is not loaded
  ///   - [location] is null
  ///   - GPS accuracy ≥ distance-to-boundary × [config.accuracySigmaFactor]
  BoundaryCheckResult check(
    LocationData? location,
    String boundaryId, {
    BoundaryCheckConfig config = const BoundaryCheckConfig(),
  }) {
    // Guard: no location
    if (location == null) {
      return BoundaryCheckResult.unknown('GPS location is unavailable.');
    }

    // Guard: boundary not loaded
    final boundary = _boundaries[boundaryId];
    if (boundary == null) {
      return BoundaryCheckResult.unknown(
          'Boundary "$boundaryId" is not loaded.');
    }

    // Guard: invalid polygon
    if (!boundary.isValid) {
      return BoundaryCheckResult.unknown(
          'Boundary "${boundary.name}" polygon is invalid.');
    }

    final lat = location.latitude;
    final lon = location.longitude;
    final accuracy = location.accuracy;

    try {
      // Fast bounding-box pre-filter
      final bb = boundary.boundingBox;
      final inBbox = lat >= bb.minLat &&
          lat <= bb.maxLat &&
          lon >= bb.minLon &&
          lon <= bb.maxLon;

      // Compute distance to nearest boundary edge (used for proximity + accuracy check)
      final distMeters = _distanceToBoundaryMeters(lat, lon, boundary.polygon);

      // GPS accuracy check — if the position uncertainty is larger than the
      // distance to the boundary we cannot confidently classify.
      // Exception: distMeters == 0 means the point is exactly on the edge;
      // we treat this as INSIDE (nearBoundary) regardless of accuracy.
      final effectiveAccuracy = accuracy * config.accuracySigmaFactor;
      if (distMeters > 0 && effectiveAccuracy >= distMeters) {
        return BoundaryCheckResult(
          classification: BoundaryClassification.unknown,
          distanceToBoundaryMeters: distMeters,
          boundaryId: boundary.id,
          boundaryName: boundary.name,
          locationAccuracyMeters: accuracy,
          checkedAt: DateTime.now().toUtc(),
          note: 'GPS accuracy (${accuracy.toStringAsFixed(1)} m) is too low '
              'relative to boundary distance '
              '(${distMeters.toStringAsFixed(1)} m).',
        );
      }

      // Full point-in-polygon check
      final inside = inBbox && _isPointInPolygon(lat, lon, boundary.polygon);

      // Classify
      final BoundaryClassification classification;
      if (inside) {
        if (distMeters <= config.warningDistanceMeters) {
          classification = BoundaryClassification.nearBoundary;
        } else {
          classification = BoundaryClassification.safe;
        }
      } else {
        if (distMeters <= config.warningDistanceMeters) {
          classification = BoundaryClassification.nearBoundary;
        } else {
          classification = BoundaryClassification.outside;
        }
      }

      return BoundaryCheckResult(
        classification: classification,
        distanceToBoundaryMeters: distMeters,
        boundaryId: boundary.id,
        boundaryName: boundary.name,
        locationAccuracyMeters: accuracy,
        checkedAt: DateTime.now().toUtc(),
        note: inside ? 'Inside polygon.' : 'Outside polygon.',
      );
    } catch (e) {
      return BoundaryCheckResult.unknown(
          'Calculation error: $e');
    }
  }

  // ── Point-in-Polygon (Ray-Casting) ────────────────────────────────────────

  /// Returns true if (lat, lon) is inside [polygon].
  ///
  /// Algorithm: cast a horizontal ray in the +longitude direction from the
  /// query point and count edge crossings (Jordan Curve Theorem).
  /// Works for any simple polygon regardless of winding order.
  /// A point exactly on an edge is considered INSIDE.
  bool _isPointInPolygon(double lat, double lon, List<LatLon> polygon) {
    final n = polygon.length;
    var inside = false;

    var j = n - 1;
    for (var i = 0; i < n; i++) {
      final xi = polygon[i].lon;
      final yi = polygon[i].lat;
      final xj = polygon[j].lon;
      final yj = polygon[j].lat;

      // Check if the point lies exactly on this edge (treat as inside)
      if (_isOnSegment(lat, lon, yi, xi, yj, xj)) return true;

      // Ray-crossing test
      if (((yi > lat) != (yj > lat)) &&
          (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
      j = i;
    }
    return inside;
  }

  /// Returns true if point (pLat, pLon) lies on the segment
  /// from (aLat, aLon) to (bLat, bLon).
  bool _isOnSegment(
    double pLat,
    double pLon,
    double aLat,
    double aLon,
    double bLat,
    double bLon,
  ) {
    const eps = 1e-10;
    // Cross product (collinearity check)
    final cross =
        (pLon - aLon) * (bLat - aLat) - (pLat - aLat) * (bLon - aLon);
    if (cross.abs() > eps) return false;
    // Dot product (between endpoints check)
    final dot = (pLon - aLon) * (bLon - aLon) + (pLat - aLat) * (bLat - aLat);
    if (dot < 0) return false;
    final lenSq =
        (bLon - aLon) * (bLon - aLon) + (bLat - aLat) * (bLat - aLat);
    return dot <= lenSq;
  }

  // ── Haversine distance ────────────────────────────────────────────────────

  static const double _earthRadiusMeters = 6371000.0;

  /// Great-circle distance in metres between two lat/lon points.
  double haversineMeters(
      double lat1, double lon1, double lat2, double lon2) {
    final dLat = _deg2rad(lat2 - lat1);
    final dLon = _deg2rad(lon2 - lon1);
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(_deg2rad(lat1)) *
            math.cos(_deg2rad(lat2)) *
            math.sin(dLon / 2) *
            math.sin(dLon / 2);
    final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return _earthRadiusMeters * c;
  }

  double _deg2rad(double deg) => deg * math.pi / 180.0;

  // ── Distance to polygon boundary ─────────────────────────────────────────

  /// Returns the minimum distance in metres from point (lat, lon) to any
  /// edge of [polygon].
  ///
  /// Uses the closest-point-on-segment calculation in geographic space.
  /// For short distances (< ~100 km) the planar approximation introduced
  /// by projecting onto a local Cartesian grid has negligible error.
  double _distanceToBoundaryMeters(
      double lat, double lon, List<LatLon> polygon) {
    double minDist = double.infinity;
    final n = polygon.length;

    for (var i = 0; i < n; i++) {
      final a = polygon[i];
      final b = polygon[(i + 1) % n];

      final d = _distanceToSegmentMeters(lat, lon, a.lat, a.lon, b.lat, b.lon);
      if (d < minDist) minDist = d;
    }
    return minDist;
  }

  /// Minimum distance in metres from point P to line segment AB.
  double _distanceToSegmentMeters(
    double pLat,
    double pLon,
    double aLat,
    double aLon,
    double bLat,
    double bLon,
  ) {
    // Project to a local Cartesian plane centred on A.
    // Scale longitude by cos(lat) to account for meridian convergence.
    final cosLat = math.cos(_deg2rad((aLat + bLat) / 2));
    final metersPerDeg = _earthRadiusMeters * math.pi / 180.0;

    final px = (pLon - aLon) * cosLat * metersPerDeg;
    final py = (pLat - aLat) * metersPerDeg;
    final bx = (bLon - aLon) * cosLat * metersPerDeg;
    final by = (bLat - aLat) * metersPerDeg;

    final lenSq = bx * bx + by * by;
    if (lenSq == 0) {
      // Degenerate segment (A == B) — just return distance to A
      return haversineMeters(pLat, pLon, aLat, aLon);
    }

    // Parameter t — clamped to [0, 1] to stay on segment
    var t = (px * bx + py * by) / lenSq;
    t = t.clamp(0.0, 1.0);

    final closestX = t * bx;
    final closestY = t * by;

    final dx = px - closestX;
    final dy = py - closestY;
    return math.sqrt(dx * dx + dy * dy);
  }
}
