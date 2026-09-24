// ─────────────────────────────────────────────────────────────────────────────
// CopernicusLayerConfig — ported from the source branch's
// `lib/map/copernicusWmts.ts` (Project ORCA web frontend).
//
// Describes a single Copernicus Marine raster layer served over OGC WMTS
// GetTile.  The values (productId / datasetId / variable / style / time) are
// the real, verified Copernicus Marine dataset identifiers from the source
// branch — they are NOT invented here.
// ─────────────────────────────────────────────────────────────────────────────

class CopernicusLayerConfig {
  const CopernicusLayerConfig({
    required this.id,
    required this.name,
    required this.productId,
    required this.datasetId,
    required this.variable,
    required this.unit,
    this.tileMatrixSet = 'EPSG:3857',
    this.format = 'image/png',
    this.style = 'default',
    this.time,
    this.elevation,
    this.opacity = 0.70,
    this.visible = true,
  });

  final String id;
  final String name;
  final String productId;
  final String datasetId;
  final String variable;
  final String unit;
  final String tileMatrixSet;
  final String format;
  final String style;
  final String? time;
  final double? elevation;
  final double opacity;
  final bool visible;

  CopernicusLayerConfig copyWith({
    String? time,
    double? opacity,
    bool? visible,
  }) {
    return CopernicusLayerConfig(
      id: id,
      name: name,
      productId: productId,
      datasetId: datasetId,
      variable: variable,
      unit: unit,
      tileMatrixSet: tileMatrixSet,
      format: format,
      style: style,
      time: time ?? this.time,
      elevation: elevation,
      opacity: opacity ?? this.opacity,
      visible: visible ?? this.visible,
    );
  }
}
