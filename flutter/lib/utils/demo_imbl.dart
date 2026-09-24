import '../models/imbl_boundary.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DemoImbl — DEVELOPMENT TEST polygon only.
//
// ⚠️  THIS IS NOT THE REAL INDIAN MARITIME BOUNDARY LINE (IMBL).
// ⚠️  DO NOT use for any navigational or safety decisions.
// ⚠️  The coordinates below are a small synthetic rectangle in the
//     Arabian Sea off the Kerala coast, chosen only to make algorithmic
//     testing easy without referencing any real border.
//
// The real IMBL data will be loaded from an authoritative source in a
// future production milestone and must not be confused with these values.
//
// Demo polygon centre: ~10.50°N, 76.00°E
// Shape: a ~110 km × ~110 km square (≈1° × 1° at this latitude)
//
// Vertex order: counter-clockwise (CCW) — algorithm handles both.
// ─────────────────────────────────────────────────────────────────────────────

class DemoImbl {
  DemoImbl._();

  /// ID used throughout the app to reference the demo boundary.
  static const String id = 'demo_imbl_test_zone';

  static ImblBoundary polygon() {
    return ImblBoundary(
      id: id,
      name: 'DEMO IMBL TEST ZONE',
      region: 'Arabian Sea (Development Only)',
      source: 'demo',
      updatedAt: DateTime.utc(2024, 1, 1),
      polygon: const [
        LatLon(10.00, 75.50), // SW corner
        LatLon(11.00, 75.50), // NW corner
        LatLon(11.00, 76.50), // NE corner
        LatLon(10.00, 76.50), // SE corner
        // polygon is implicitly closed — no need to repeat first vertex
      ],
    );
  }

  /// A point clearly INSIDE the demo polygon.
  static const LatLon pointInside = LatLon(10.50, 76.00);

  /// A point clearly OUTSIDE the demo polygon.
  static const LatLon pointOutside = LatLon(9.00, 74.00);

  /// A point on the western boundary edge of the polygon.
  static const LatLon pointOnBoundary = LatLon(10.50, 75.50);

  /// A point just outside but within 500 m of the northern edge.
  /// (Latitude 11.004° ≈ 444 m north of the 11.00° edge)
  static const LatLon pointNearBoundary = LatLon(11.004, 76.00);
}
