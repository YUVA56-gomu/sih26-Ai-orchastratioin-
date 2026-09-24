import '../../models/map/ocean_layer.dart';
import 'copernicus_wmts.dart';

// ─────────────────────────────────────────────────────────────────────────────
// OceanLayerRegistry — ported from the source branch's `lib/map/layerManager.ts`
// (Project ORCA web frontend).
//
// The canonical default set of oceanographic layers drawn on the map, plus a
// tiny state registry (visibility) so toggling is cheap and testable.
// ─────────────────────────────────────────────────────────────────────────────

class OceanLayerRegistry {
  /// Creates an empty registry pre-populated with the default ocean layers.
  OceanLayerRegistry();

  /// Canonical default ocean layers (source branch registry order).
  static final List<OceanMapLayer> defaultOceanLayers = _buildDefaultLayers();

  static List<OceanMapLayer> _buildDefaultLayers() {
    return [
      OceanMapLayer(
        id: 'copernicus-sst',
        name: 'Sea Surface Temperature',
        source: LayerSource.copernicus,
        type: LayerType.wmts,
        productId: defaultSstConfig.productId,
        datasetId: defaultSstConfig.datasetId,
        variable: defaultSstConfig.variable,
        unit: defaultSstConfig.unit,
        temporalResolution: 'P1D (Daily)',
        spatialResolution: '0.05° (~5 km)',
        style: defaultSstConfig.style,
        visible: true,
        opacity: 0.70,
        zIndex: 10,
        time: defaultSstConfig.time,
        status: LayerStatus.connected,
        legend: OceanLayerLegend(
          url: buildCopernicusLegendUrl(defaultSstConfig, format: 'svg'),
          unit: '°C',
          title: 'SEA SURFACE TEMPERATURE',
          format: 'svg',
        ),
      ),
      OceanMapLayer(
        id: 'copernicus-wave',
        name: 'Significant Wave Height',
        source: LayerSource.copernicus,
        type: LayerType.wmts,
        productId: defaultWaveConfig.productId,
        datasetId: defaultWaveConfig.datasetId,
        variable: defaultWaveConfig.variable,
        unit: defaultWaveConfig.unit,
        temporalResolution: 'PT3H (3-Hourly)',
        spatialResolution: '0.083° (~9 km)',
        style: defaultWaveConfig.style,
        visible: false,
        opacity: 0.70,
        zIndex: 11,
        time: defaultWaveConfig.time,
        status: LayerStatus.connected,
        legend: OceanLayerLegend(
          url: buildCopernicusLegendUrl(defaultWaveConfig, format: 'svg'),
          unit: 'm',
          title: 'SIGNIFICANT WAVE HEIGHT',
          format: 'svg',
        ),
      ),
      OceanMapLayer(
        id: 'copernicus-sla',
        name: 'Sea Level Anomaly',
        source: LayerSource.copernicus,
        type: LayerType.wmts,
        productId: defaultSeaLevelConfig.productId,
        datasetId: defaultSeaLevelConfig.datasetId,
        variable: defaultSeaLevelConfig.variable,
        unit: defaultSeaLevelConfig.unit,
        temporalResolution: 'P1D (Daily)',
        spatialResolution: '0.125° (~14 km)',
        style: defaultSeaLevelConfig.style,
        visible: false,
        opacity: 0.70,
        zIndex: 12,
        time: defaultSeaLevelConfig.time,
        status: LayerStatus.connected,
        legend: OceanLayerLegend(
          url: buildCopernicusLegendUrl(defaultSeaLevelConfig, format: 'svg'),
          unit: 'm',
          title: 'SEA LEVEL ANOMALY',
          format: 'svg',
        ),
      ),
      OceanMapLayer(
        id: 'copernicus-chl',
        name: 'Chlorophyll-a Concentration',
        source: LayerSource.copernicus,
        type: LayerType.wmts,
        productId: defaultChlorophyllConfig.productId,
        datasetId: defaultChlorophyllConfig.datasetId,
        variable: defaultChlorophyllConfig.variable,
        unit: defaultChlorophyllConfig.unit,
        temporalResolution: 'P1D (Daily Gap-Free)',
        spatialResolution: '4 km (~0.04°)',
        style: defaultChlorophyllConfig.style,
        visible: false,
        opacity: 0.70,
        zIndex: 13,
        time: defaultChlorophyllConfig.time,
        status: LayerStatus.connected,
        legend: OceanLayerLegend(
          url: buildCopernicusLegendUrl(defaultChlorophyllConfig, format: 'svg'),
          unit: 'mg/m³',
          title: 'CHLOROPHYLL-A',
          format: 'svg',
        ),
      ),
      OceanMapLayer(
        id: 'copernicus-currents',
        name: 'Ocean Surface Currents',
        source: LayerSource.copernicus,
        type: LayerType.wmts,
        productId: defaultCurrentsConfig.productId,
        datasetId: defaultCurrentsConfig.datasetId,
        variable: defaultCurrentsConfig.variable,
        unit: defaultCurrentsConfig.unit,
        temporalResolution: 'P1D (Daily)',
        spatialResolution: '0.083° (~9 km)',
        style: 'cmap:balance',
        visible: false,
        opacity: 0.70,
        zIndex: 14,
        time: '2026-08-28T00:00:00.000Z',
        status: LayerStatus.unavailable,
      ),
    ];
  }

  final Map<String, OceanMapLayer> _layers = {
    for (final l in defaultOceanLayers) l.id: l,
  };

  /// All registered layers, in registry order.
  List<OceanMapLayer> get layers => _layers.values.toList();

  /// All renderable (non-unavailable) layers.
  List<OceanMapLayer> get renderableLayers =>
      _layers.values.where((l) => l.isRenderable).toList();

  OceanMapLayer? getLayer(String id) => _layers[id];

  /// Toggle a layer's visibility. Returns false if the id is unknown.
  bool setLayerVisible(String id, bool visible) {
    final layer = _layers[id];
    if (layer == null) return false;
    _layers[id] = layer.copyWith(visible: visible);
    return true;
  }

  /// Returns true if the layer is currently visible.
  bool isLayerVisible(String id) => _layers[id]?.visible ?? false;
}
