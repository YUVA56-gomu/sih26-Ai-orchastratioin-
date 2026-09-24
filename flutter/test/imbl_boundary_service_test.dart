import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/models/imbl_boundary.dart';
import 'package:samudra_ai/models/boundary_check_result.dart';
import 'package:samudra_ai/models/location_data.dart';
import 'package:samudra_ai/services/imbl_boundary_service.dart';
import 'package:samudra_ai/utils/demo_imbl.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for ImblBoundaryService
//
// These tests run entirely offline — no network, no GPS hardware, no SQLite.
// The demo polygon is a ~1°×1° square:
//   SW (10.00, 75.50)  NW (11.00, 75.50)
//   NE (11.00, 76.50)  SE (10.00, 76.50)
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  late ImblBoundaryService svc;
  late ImblBoundary demo;

  // Helpers ──────────────────────────────────────────────────────────────────

  LocationData loc(double lat, double lon, {double accuracy = 10.0}) {
    return LocationData(
      latitude: lat,
      longitude: lon,
      accuracy: accuracy,
      speed: 0,
      heading: 0,
      timestamp: DateTime.now().toUtc(),
    );
  }

  setUp(() {
    svc = ImblBoundaryService.instance;
    svc.clearBoundaries();
    demo = DemoImbl.polygon();
    svc.loadBoundary(demo);
  });

  group('Point-in-polygon', () {
    test('1. Point clearly inside polygon is SAFE', () {
      // Centre of the box: (10.50, 76.00)
      final result = svc.check(loc(10.50, 76.00), DemoImbl.id);
      expect(result.classification, BoundaryClassification.safe);
      expect(result.boundaryId, DemoImbl.id);
    });

    test('2. Point clearly outside polygon is OUTSIDE', () {
      // Far south-west of the polygon
      final result = svc.check(loc(9.00, 74.00), DemoImbl.id);
      expect(result.classification, BoundaryClassification.outside);
    });

    test('3. Point on polygon boundary edge is treated as INSIDE/NEAR', () {
      // On the western edge: lat 10.50, lon exactly 75.50
      // Use accuracy=0 so the accuracy guard doesn't interfere with distMeters≈0
      final result = svc.check(loc(10.50, 75.50, accuracy: 0.0), DemoImbl.id);
      // Algorithm returns INSIDE (safe or near-boundary depending on distance)
      expect(
        result.classification,
        anyOf(BoundaryClassification.safe, BoundaryClassification.nearBoundary),
      );
    });

    test('4. Point near boundary but outside is NEAR_BOUNDARY', () {
      // lat 11.004° ≈ 444 m north of the northern edge (11.00°)
      const config = BoundaryCheckConfig(warningDistanceMeters: 500.0);
      final result = svc.check(loc(11.004, 76.00), DemoImbl.id, config: config);
      expect(result.classification, BoundaryClassification.nearBoundary);
      expect(result.distanceToBoundaryMeters, lessThan(500.0));
    });

    test('5. Poor GPS accuracy yields UNKNOWN', () {
      // Place point 100 m outside the northern edge; give 500 m accuracy
      // The boundary is ~444 m away; accuracy (500 m) > distance → UNKNOWN
      const config = BoundaryCheckConfig(
        warningDistanceMeters: 500.0,
        accuracySigmaFactor: 1.0,
      );
      final result = svc.check(
        loc(11.004, 76.00, accuracy: 500.0),
        DemoImbl.id,
        config: config,
      );
      expect(result.classification, BoundaryClassification.unknown);
    });

    test('6. Clockwise polygon gives same result as CCW', () {
      // Reverse the vertex order of the demo polygon (making it CW)
      final cwBoundary = ImblBoundary(
        id: 'demo_cw',
        name: 'CW Test',
        region: 'test',
        source: 'test',
        updatedAt: DateTime.utc(2024),
        polygon: demo.polygon.reversed.toList(),
      );
      svc.loadBoundary(cwBoundary);

      final resultCCW = svc.check(loc(10.50, 76.00), DemoImbl.id);
      final resultCW = svc.check(loc(10.50, 76.00), 'demo_cw');

      expect(resultCCW.classification, resultCW.classification,
          reason: 'CW and CCW should produce identical results');
    });

    test('7. Counter-clockwise polygon — inside point is SAFE', () {
      // The demo polygon is already CCW — confirm centre is SAFE
      final result = svc.check(loc(10.50, 76.00), DemoImbl.id);
      expect(result.classification, BoundaryClassification.safe);
    });
  });

  group('Guard conditions', () {
    test('8. Null location returns UNKNOWN', () {
      final result = svc.check(null, DemoImbl.id);
      expect(result.classification, BoundaryClassification.unknown);
      expect(result.note, contains('unavailable'));
    });

    test('9. Unknown boundary ID returns UNKNOWN', () {
      final result = svc.check(loc(10.50, 76.00), 'nonexistent_id');
      expect(result.classification, BoundaryClassification.unknown);
    });

    test('10. Invalid polygon (< 3 vertices) throws on load', () {
      final bad = ImblBoundary(
        id: 'bad',
        name: 'Bad',
        region: 'test',
        source: 'test',
        updatedAt: DateTime.utc(2024),
        polygon: [const LatLon(10.0, 75.5), const LatLon(11.0, 75.5)],
      );
      expect(() => svc.loadBoundary(bad), throwsArgumentError);
    });
  });

  group('Distance calculation', () {
    test('11. Distance from far-outside point is positive and reasonable', () {
      final result = svc.check(loc(9.00, 74.00), DemoImbl.id);
      expect(result.distanceToBoundaryMeters, isNotNull);
      expect(result.distanceToBoundaryMeters!, greaterThan(0));
      // From (9.00, 74.00) to SW corner (10.00, 75.50) is ≈ ~190 km
      expect(result.distanceToBoundaryMeters!, greaterThan(100000));
    });

    test('12. Distance from centre of box to edge is ≈ 55 km', () {
      // Centre (10.50, 76.00), nearest edge is lon=75.50 at same latitude.
      // 0.5° longitude at ~10.5° lat: 0.5 × 111 km × cos(10.5°) ≈ 54.5 km
      final result = svc.check(loc(10.50, 76.00), DemoImbl.id);
      expect(result.distanceToBoundaryMeters, isNotNull);
      final d = result.distanceToBoundaryMeters!;
      // Allow 10% tolerance for the Cartesian approximation
      expect(d, greaterThan(45000));
      expect(d, lessThan(65000));
    });
  });

  group('Haversine', () {
    test('13. Known distance: equator, 1 degree longitude ≈ 111 km', () {
      final d = svc.haversineMeters(0, 0, 0, 1);
      expect(d, closeTo(111320, 200)); // ±200 m tolerance
    });

    test('14. Known distance: 1 degree latitude ≈ 111 km', () {
      final d = svc.haversineMeters(0, 0, 1, 0);
      // 1° latitude from equator ≈ 111,195 m (meridian length is not uniform;
      // this is the value at 0°–1°).  Allow ±500 m tolerance.
      expect(d, closeTo(111195, 500));
    });
  });
}
