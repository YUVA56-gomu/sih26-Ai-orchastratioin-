import '../../models/map/copernicus_layer_config.dart';

// ─────────────────────────────────────────────────────────────────────────────
// CopernicusWmts — ported from the source branch's `lib/map/copernicusWmts.ts`
// (Project ORCA web frontend).
//
// Builds OGC WMTS GetTile / GetLegend URLs for the Copernicus Marine service.
// The base service URL and dataset identifiers are the same verified values
// used by the source branch.
//
// The GetTile template keeps literal {z}, {x}, {y} tokens so it can be passed
// directly to a map engine (flutter_map's TileLayer urlTemplate) which will
// substitute the tile coordinates.
// ─────────────────────────────────────────────────────────────────────────────

/// Default (src branch) Copernicus Marine SST layer — OSTIA product, visible.
const CopernicusLayerConfig defaultSstConfig = CopernicusLayerConfig(
  id: 'copernicus-sst',
  name: 'Sea Surface Temperature',
  productId: 'SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001',
  datasetId: 'METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2',
  variable: 'analysed_sst',
  unit: '°C',
  style: 'cmap:thermal',
  time: '2026-08-28T00:00:00Z',
  opacity: 0.70,
  visible: true,
);

/// Significant Wave Height layer, hidden by default.
const CopernicusLayerConfig defaultWaveConfig = CopernicusLayerConfig(
  id: 'copernicus-wave',
  name: 'Significant Wave Height',
  productId: 'GLOBAL_ANALYSISFORECAST_WAV_001_027',
  datasetId: 'cmems_mod_glo_wav_anfc_0.083deg_PT3H-i_202411',
  variable: 'VHM0',
  unit: 'm',
  style: 'cmap:amp',
  time: '2026-08-28T00:00:00.000Z',
  opacity: 0.70,
  visible: false,
);

/// Sea Level Anomaly layer, hidden by default.
const CopernicusLayerConfig defaultSeaLevelConfig = CopernicusLayerConfig(
  id: 'copernicus-sla',
  name: 'Sea Level Anomaly',
  productId: 'SEALEVEL_GLO_PHY_L4_NRT_008_046',
  datasetId: 'cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D_202506',
  variable: 'sla',
  unit: 'm',
  style: 'cmap:plasma',
  time: '2026-08-28T00:00:00.000Z',
  opacity: 0.70,
  visible: false,
);

/// Chlorophyll-a concentration layer, hidden by default.
const CopernicusLayerConfig defaultChlorophyllConfig = CopernicusLayerConfig(
  id: 'copernicus-chl',
  name: 'Chlorophyll-a Concentration',
  productId: 'OCEANCOLOUR_GLO_BGC_L4_NRT_009_102',
  datasetId: 'cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D_202311',
  variable: 'CHL',
  unit: 'mg/m³',
  style: 'cmap:algae',
  time: '2026-08-28T00:00:00.000Z',
  opacity: 0.70,
  visible: false,
);

/// Ocean Surface Currents — architecture-ready but not rendered (UNAVAILABLE).
const CopernicusLayerConfig defaultCurrentsConfig = CopernicusLayerConfig(
  id: 'copernicus-currents',
  name: 'Ocean Surface Currents',
  productId: 'GLOBAL_ANALYSISFORECAST_PHY_001_024',
  datasetId: 'cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m_202406',
  variable: 'uo, vo',
  unit: 'm/s',
  style: 'cmap:balance',
  time: '2026-08-28T00:00:00.000Z',
  opacity: 0.70,
  visible: false,
);

/// Base Copernicus Marine WMTS endpoint.
const String kWmtsBaseUrl = 'https://wmts.marine.copernicus.eu/teroWmts';

/// Returns the Copernicus Marine WMTS service base URL.
String getWmtsBaseUrl() => kWmtsBaseUrl;

/// Standard layer path: `<PRODUCT_ID>/<DATASET_ID>/<VARIABLE>`.
String getWmtsLayerPath(CopernicusLayerConfig config) {
  return '${config.productId}/${config.datasetId}/${config.variable}';
}

/// Builds a map-engine-ready GetTile URL template containing {z}, {x}, {y}.
String buildWmtsTileUrlTemplate(CopernicusLayerConfig config) {
  final baseUrl = getWmtsBaseUrl();
  final layerPath = getWmtsLayerPath(config);

  final params = <String, String>{
    'SERVICE': 'WMTS',
    'VERSION': '1.0.0',
    'REQUEST': 'GetTile',
    'LAYER': layerPath,
    'STYLE': config.style.isEmpty ? 'default' : config.style,
    'FORMAT': config.format,
    'TILEMATRIXSET': config.tileMatrixSet,
    // Map engines require literal {z}/{y}/{x} tokens — do not URL-encode.
    'TILEMATRIX': '{z}',
    'TILEROW': '{y}',
    'TILECOL': '{x}',
  };

  if (config.time != null) {
    params['TIME'] = config.time!;
  }
  if (config.elevation != null) {
    params['ELEVATION'] = config.elevation!.toString();
  }

  var query = params.entries
      .map((e) =>
          '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value)}')
      .join('&');

  // Flutter map engines (flutter_map TileLayer.urlTemplate) substitute
  // {z}/{x}/{y} as literal tokens. Uri.encodeQueryComponent turns their braces
  // into %7B/%7D, which the engine would not recognise — restore the tokens.
  query = query
      .replaceAll('%7Bz%7D', '{z}')
      .replaceAll('%7Bx%7D', '{x}')
      .replaceAll('%7By%7D', '{y}');

  return '$baseUrl?$query';
}

/// Builds a concrete GetTile URL for a specific tile (row/col/matrix).
String buildWmtsTileUrl(
  CopernicusLayerConfig config,
  int z,
  int x,
  int y,
) {
  return buildWmtsTileUrlTemplate(config)
      .replaceAll('{z}', '$z')
      .replaceAll('{x}', '$x')
      .replaceAll('{y}', '$y');
}

/// Builds a Copernicus Marine WMTS GetLegend URL for the layer.
String buildCopernicusLegendUrl(
  CopernicusLayerConfig config, {
  String format = 'svg',
}) {
  final baseUrl = getWmtsBaseUrl();
  final layerPath = getWmtsLayerPath(config);
  final formatMime = format == 'json' ? 'application/json' : 'image/svg+xml';

  final params = <String, String>{
    'SERVICE': 'WMTS',
    'VERSION': '1.0.0',
    'REQUEST': 'GetLegend',
    'LAYER': layerPath,
    'STYLE': config.style.isEmpty ? 'cmap:thermal' : config.style,
    'FORMAT': formatMime,
  };

  final query = params.entries
      .map((e) =>
          '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value)}')
      .join('&');

  return '$baseUrl?$query';
}
