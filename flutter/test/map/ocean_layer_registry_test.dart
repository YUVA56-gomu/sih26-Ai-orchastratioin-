import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/models/map/ocean_layer.dart';
import 'package:samudra_ai/services/map/ocean_layer_registry.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for OceanLayerRegistry (ported from the source branch's
// `lib/map/layerManager.ts`).
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  group('defaultOceanLayers', () {
    test('SST is visible by default', () {
      final sst = OceanLayerRegistry.defaultOceanLayers
          .firstWhere((l) => l.id == 'copernicus-sst');
      expect(sst.visible, isTrue);
      expect(sst.status, LayerStatus.connected);
    });

    test('wave / SLA / chlorophyll are hidden by default', () {
      for (final id in ['copernicus-wave', 'copernicus-sla', 'copernicus-chl']) {
        final layer = OceanLayerRegistry.defaultOceanLayers
            .firstWhere((l) => l.id == id);
        expect(layer.visible, isFalse);
      }
    });

    test('currents layer is architecture-only (unavailable)', () {
      final layer = OceanLayerRegistry.defaultOceanLayers
          .firstWhere((l) => l.id == 'copernicus-currents');
      expect(layer.status, LayerStatus.unavailable);
      expect(layer.isRenderable, isFalse);
    });
  });

  group('OceanLayerRegistry instance', () {
    test('creates an instance seeded with default layers', () {
      final registry = OceanLayerRegistry();
      expect(registry.layers.length, greaterThanOrEqualTo(5));
      expect(registry.getLayer('copernicus-sst'), isNotNull);
    });

    test('renderableLayers excludes unavailable layers', () {
      final registry = OceanLayerRegistry();
      expect(
        registry.renderableLayers.map((l) => l.id),
        isNot(contains('copernicus-currents')),
      );
    });

    test('setLayerVisible toggles visibility', () {
      final registry = OceanLayerRegistry();
      expect(registry.isLayerVisible('copernicus-wave'), isFalse);

      final ok = registry.setLayerVisible('copernicus-wave', true);
      expect(ok, isTrue);
      expect(registry.isLayerVisible('copernicus-wave'), isTrue);
    });

    test('setLayerVisible returns false for an unknown id', () {
      final registry = OceanLayerRegistry();
      expect(registry.setLayerVisible('does-not-exist', true), isFalse);
    });
  });
}
