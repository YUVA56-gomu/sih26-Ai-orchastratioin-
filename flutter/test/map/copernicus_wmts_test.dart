import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/models/map/copernicus_layer_config.dart';
import 'package:samudra_ai/services/map/copernicus_wmts.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for the Copernicus WMTS URL builders (ported from the source
// branch's `lib/map/copernicusWmts.ts`).
//
// Running fully offline — these only assert string construction, they never
// perform a network request.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  group('getWmtsLayerPath', () {
    test('builds <productId>/<datasetId>/<variable>', () {
      final path = getWmtsLayerPath(defaultSstConfig);
      expect(
        path,
        'SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001/'
        'METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2/analysed_sst',
      );
    });
  });

  group('buildWmtsTileUrlTemplate', () {
    test('keeps literal {z}/{x}/{y} tokens for the map engine', () {
      final template = buildWmtsTileUrlTemplate(defaultSstConfig);

      expect(template, contains('REQUEST=GetTile'));
      expect(template, contains('TILEMATRIX={z}'));
      expect(template, contains('TILEROW={y}'));
      expect(template, contains('TILECOL={x}'));
      expect(template, contains('STYLE=cmap%3Athermal'));
      expect(template, contains('SERVICE=WMTS'));
      expect(template, contains('VERSION=1.0.0'));
      expect(template, contains('TILEMATRIXSET=EPSG%3A3857'));
      expect(template, contains('TIME='));
      expect(template, startsWith('$kWmtsBaseUrl?'));
    });

    test('omits TIME when config has none', () {
      const config = CopernicusLayerConfig(
        id: 'x',
        name: 'X',
        productId: 'p',
        datasetId: 'd',
        variable: 'v',
        unit: 'u',
      );
      final template = buildWmtsTileUrlTemplate(config);
      expect(template, isNot(contains('TIME=')));
    });
  });

  group('buildWmtsTileUrl', () {
    test('substitutes concrete tile coordinates', () {
      final url = buildWmtsTileUrl(defaultSstConfig, 5, 12, 23);
      expect(url, contains('TILEMATRIX=5'));
      expect(url, contains('TILEROW=23'));
      expect(url, contains('TILECOL=12'));
      expect(url, isNot(contains('{z}')));
      expect(url, isNot(contains('{y}')));
      expect(url, isNot(contains('{x}')));
    });
  });

  group('buildCopernicusLegendUrl', () {
    test('builds a GetLegend request', () {
      final legend = buildCopernicusLegendUrl(defaultSstConfig);
      expect(legend, contains('REQUEST=GetLegend'));
      expect(legend, contains('FORMAT=image%2Fsvg%2Bxml'));
    });

    test('supports json format', () {
      final legend = buildCopernicusLegendUrl(defaultSstConfig, format: 'json');
      expect(legend, contains('FORMAT=application%2Fjson'));
    });
  });
}
