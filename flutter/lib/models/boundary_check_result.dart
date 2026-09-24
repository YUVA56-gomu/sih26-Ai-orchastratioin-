// ─────────────────────────────────────────────────────────────────────────────
// BoundaryCheckResult — output of ImblBoundaryService.check().
//
// Contains enough information for the future background alerting pipeline
// (Milestone 5) to decide whether to trigger a warning without re-running
// the geometry calculation.
//
// Safety contract:
//   - SAFE is only returned when:
//       • boundary data is valid
//       • GPS position is available
//       • GPS accuracy is sufficient relative to the distance to boundary
//       • point is conclusively inside the polygon
//   - UNKNOWN is returned on ANY ambiguity, including:
//       • missing boundary data
//       • null GPS position
//       • insufficient GPS accuracy
//       • calculation exception
//   Never claim SAFE when confidence is low.
// ─────────────────────────────────────────────────────────────────────────────

/// Possible classifications produced by a boundary check.
enum BoundaryClassification {
  /// Position is conclusively inside the boundary with adequate GPS accuracy.
  safe,

  /// Position is inside but dangerously close to the boundary edge,
  /// OR outside but within the configured warning-distance threshold.
  nearBoundary,

  /// Position is conclusively outside the boundary.
  outside,

  /// Cannot determine — missing data, poor GPS, or calculation error.
  unknown,
}

/// The complete result of a single boundary check.
class BoundaryCheckResult {
  final BoundaryClassification classification;

  /// Approximate distance in metres from the point to the nearest boundary
  /// edge.  Null when the boundary or position is unavailable.
  final double? distanceToBoundaryMeters;

  /// The boundary that was checked against, or null if none was loaded.
  final String? boundaryId;
  final String? boundaryName;

  /// GPS horizontal accuracy used in this check (metres).
  final double? locationAccuracyMeters;

  /// UTC time this check was performed.
  final DateTime checkedAt;

  /// Human-readable note explaining the classification (for dev UI / logs).
  final String? note;

  const BoundaryCheckResult({
    required this.classification,
    this.distanceToBoundaryMeters,
    this.boundaryId,
    this.boundaryName,
    this.locationAccuracyMeters,
    required this.checkedAt,
    this.note,
  });

  /// Convenience constructor for UNKNOWN results with a reason string.
  factory BoundaryCheckResult.unknown(String reason) {
    return BoundaryCheckResult(
      classification: BoundaryClassification.unknown,
      checkedAt: DateTime.now().toUtc(),
      note: reason,
    );
  }

  bool get isSafe => classification == BoundaryClassification.safe;
  bool get isNearBoundary =>
      classification == BoundaryClassification.nearBoundary;
  bool get isOutside => classification == BoundaryClassification.outside;
  bool get isUnknown => classification == BoundaryClassification.unknown;

  @override
  String toString() =>
      'BoundaryCheckResult('
      'classification: ${classification.name}, '
      'distance: ${distanceToBoundaryMeters?.toStringAsFixed(1)} m, '
      'accuracy: ${locationAccuracyMeters?.toStringAsFixed(1)} m, '
      'note: $note)';
}
