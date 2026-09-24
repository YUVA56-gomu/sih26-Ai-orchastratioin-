import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/data/map/demo_pfz_zones.dart';
import 'package:samudra_ai/models/map/pfz_zone.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for the DEMO PFZ zones ported from the source branch's
// `mock/mockPFZ.ts`.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  group('DemoPfzZones', () {
    test('defines a default camera', () {
      expect(DemoPfzZones.defaultCamera.lat, inInclusiveRange(-90, 90));
      expect(DemoPfzZones.defaultCamera.lng, inInclusiveRange(-180, 180));
      expect(DemoPfzZones.defaultCamera.zoom, greaterThan(0));
    });

    test('defines region presets', () {
      expect(DemoPfzZones.regionPresets, isNotEmpty);
      for (final preset in DemoPfzZones.regionPresets) {
        expect(preset.name, isNotEmpty);
        expect(preset.zoom, greaterThan(0));
      }
    });

    test('zones are non-empty and valid', () {
      expect(DemoPfzZones.zones, isNotEmpty);

      for (final zone in DemoPfzZones.zones) {
        // Each zone has a closed polygon with at least 3 vertices.
        expect(zone.geometry.points.length, greaterThanOrEqualTo(3));

        // toLatLng flips [lng, lat] → (lat, lon) and preserves order/count.
        final latLngs = zone.geometry.toLatLng();
        expect(latLngs.length, zone.geometry.points.length);
        expect(latLngs.first.lat, zone.geometry.points.first[1]);
        expect(latLngs.first.lon, zone.geometry.points.first[0]);

        // Zone metadata is present.
        expect(zone.id, isNotEmpty);
        expect(zone.score, inInclusiveRange(0, 100));
        expect(zone.status, PfzZoneStatus.demo);
      }
    });
  });
}
