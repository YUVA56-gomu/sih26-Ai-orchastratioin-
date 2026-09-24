// ─────────────────────────────────────────────────────────────────────────────
// OceanMapLayer — ported from the source branch's `types/index.ts`
// (Project ORCA web frontend).
//
// This model describes a raster/vector overlay that can be drawn on the map.
// It is intentionally decoupled from any backend so a future hosted API can
// fill in values without touching the map UI.
// ─────────────────────────────────────────────────────────────────────────────

import 'copernicus_layer_config.dart';

/// Status of a data layer.
enum LayerStatus { connected, loading, error, unavailable, demo }

/// The source of the layer data.
enum LayerSource { copernicus, isro, incois, noaa, orca }

/// Rendering type of the layer.
enum LayerType { raster, vector, geojson, wms, wmts }

/// Optional legend metadata shown with the layer.
class OceanLayerLegend {
  const OceanLayerLegend({
    this.url,
    this.unit,
    this.title,
    this.format,
  });

  final String? url;
  final String? unit;
  final String? title;
  final String? format;
}

class OceanMapLayer {
  const OceanMapLayer({
    required this.id,
    required this.name,
    required this.source,
    required this.type,
    required this.variable,
    required this.unit,
    required this.visible,
    required this.opacity,
    required this.zIndex,
    this.productId,
    this.datasetId,
    this.temporalResolution,
    this.spatialResolution,
    this.style,
    this.legend,
    this.time,
    this.availableTimes,
    required this.status,
  });

  final String id;
  final String name;
  final LayerSource source;
  final LayerType type;
  final String? productId;
  final String? datasetId;
  final String variable;
  final String unit;
  final String? temporalResolution;
  final String? spatialResolution;
  final String? style;
  final bool visible;
  final double opacity;
  final int zIndex;
  final OceanLayerLegend? legend;
  final String? time;
  final List<String>? availableTimes;
  final LayerStatus status;

  OceanMapLayer copyWith({
    bool? visible,
    double? opacity,
    String? time,
    LayerStatus? status,
  }) {
    return OceanMapLayer(
      id: id,
      name: name,
      source: source,
      type: type,
      productId: productId,
      datasetId: datasetId,
      variable: variable,
      unit: unit,
      temporalResolution: temporalResolution,
      spatialResolution: spatialResolution,
      style: style,
      visible: visible ?? this.visible,
      opacity: opacity ?? this.opacity,
      zIndex: zIndex,
      legend: legend,
      time: time ?? this.time,
      availableTimes: availableTimes,
      status: status ?? this.status,
    );
  }

  /// Convenience: whether this layer is currently renderable on the map.
  /// Layers marked [LayerStatus.unavailable] are architecture-only stubs and
  /// must not be requested.
  bool get isRenderable => status != LayerStatus.unavailable;

  /// Builds a [CopernicusLayerConfig] for this layer so the WMTS tile template
  /// can be constructed.  Uses the layer values, falling back to the defaults
  /// where the source branch did.
  CopernicusLayerConfig toCopernicusConfig(CopernicusLayerConfig fallback) {
    return CopernicusLayerConfig(
      id: id,
      name: name,
      productId: productId ?? fallback.productId,
      datasetId: datasetId ?? fallback.datasetId,
      variable: variable,
      unit: unit,
      tileMatrixSet: fallback.tileMatrixSet,
      format: fallback.format,
      style: style ?? fallback.style,
      time: time ?? fallback.time,
      opacity: opacity,
      visible: visible,
    );
  }
}
