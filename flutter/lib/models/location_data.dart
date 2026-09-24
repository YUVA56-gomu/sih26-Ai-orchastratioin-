// ─────────────────────────────────────────────────────────────────────────────
// LocationData — typed model for GPS/GNSS position data.
//
// Screens and services use this model instead of raw geolocator objects so
// that the underlying location plugin can be swapped (e.g. NavIC/NMEA in
// Milestone 7) without touching any UI code.
// ─────────────────────────────────────────────────────────────────────────────

class LocationData {
  /// Decimal degrees (WGS-84)
  final double latitude;
  final double longitude;

  /// Estimated horizontal accuracy in metres
  final double accuracy;

  /// Speed in metres per second (0.0 when unavailable)
  final double speed;

  /// True bearing in degrees (0–360, 0.0 when unavailable)
  final double heading;

  /// When this fix was acquired
  final DateTime timestamp;

  const LocationData({
    required this.latitude,
    required this.longitude,
    required this.accuracy,
    required this.speed,
    required this.heading,
    required this.timestamp,
  });

  /// Speed converted to knots (1 m/s ≈ 1.94384 kn)
  double get speedKnots => speed * 1.94384;

  /// Human-readable summary for debug display
  @override
  String toString() =>
      'LocationData(lat: ${latitude.toStringAsFixed(6)}, '
      'lon: ${longitude.toStringAsFixed(6)}, '
      'acc: ${accuracy.toStringAsFixed(1)} m, '
      'spd: ${speed.toStringAsFixed(2)} m/s, '
      'hdg: ${heading.toStringAsFixed(1)}°, '
      'ts: $timestamp)';
}
