// ─────────────────────────────────────────────────────────────────────────────
// MarineData — typed model for locally cached marine information.
//
// Stored in the SQLite marine_data table.  The latitude/longitude fields allow
// simple bounding-box queries now, and leave room for richer spatial queries
// (IMBL polygon membership, region tagging) in future milestones.
// ─────────────────────────────────────────────────────────────────────────────

class MarineData {
  final int? id; // null until inserted into SQLite

  /// Category of data, e.g. 'sea_surface_temp', 'wave_height', 'imbl_zone'.
  /// Used for filtered queries — do NOT add IMBL logic here yet.
  final String dataType;

  final String title;
  final String description;

  /// Optional geographic anchor.  Nullable — not all records have a position.
  final double? latitude;
  final double? longitude;

  /// Numeric measurement value (string-encoded to support any unit).
  final String? value;
  final String? unit;

  /// Origin label, e.g. 'demo', 'incois', 'imd', 'user'.
  final String source;

  /// UTC time the measurement was taken / valid for.
  final DateTime timestamp;

  /// UTC time after which this record should be treated as stale.
  /// Null means the record never expires.
  final DateTime? expiresAt;

  /// UTC time this row was written to the local database.
  final DateTime createdAt;

  /// UTC time this row was last updated in the local database.
  final DateTime updatedAt;

  const MarineData({
    this.id,
    required this.dataType,
    required this.title,
    required this.description,
    this.latitude,
    this.longitude,
    this.value,
    this.unit,
    required this.source,
    required this.timestamp,
    this.expiresAt,
    required this.createdAt,
    required this.updatedAt,
  });

  // ── Serialisation ─────────────────────────────────────────────────────────

  /// Convert to a map suitable for SQLite insert/update.
  /// DateTime values are stored as ISO-8601 UTC strings.
  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'data_type': dataType,
      'title': title,
      'description': description,
      'latitude': latitude,
      'longitude': longitude,
      'value': value,
      'unit': unit,
      'source': source,
      'timestamp': timestamp.toUtc().toIso8601String(),
      'expires_at': expiresAt?.toUtc().toIso8601String(),
      'created_at': createdAt.toUtc().toIso8601String(),
      'updated_at': updatedAt.toUtc().toIso8601String(),
    };
  }

  /// Reconstruct a MarineData from a SQLite row map.
  factory MarineData.fromMap(Map<String, dynamic> map) {
    return MarineData(
      id: map['id'] as int?,
      dataType: map['data_type'] as String,
      title: map['title'] as String,
      description: map['description'] as String,
      latitude: map['latitude'] as double?,
      longitude: map['longitude'] as double?,
      value: map['value'] as String?,
      unit: map['unit'] as String?,
      source: map['source'] as String,
      timestamp: DateTime.parse(map['timestamp'] as String).toUtc(),
      expiresAt: map['expires_at'] != null
          ? DateTime.parse(map['expires_at'] as String).toUtc()
          : null,
      createdAt: DateTime.parse(map['created_at'] as String).toUtc(),
      updatedAt: DateTime.parse(map['updated_at'] as String).toUtc(),
    );
  }

  /// Returns a copy with updated fields (useful for update operations).
  MarineData copyWith({
    int? id,
    String? dataType,
    String? title,
    String? description,
    double? latitude,
    double? longitude,
    String? value,
    String? unit,
    String? source,
    DateTime? timestamp,
    DateTime? expiresAt,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return MarineData(
      id: id ?? this.id,
      dataType: dataType ?? this.dataType,
      title: title ?? this.title,
      description: description ?? this.description,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      value: value ?? this.value,
      unit: unit ?? this.unit,
      source: source ?? this.source,
      timestamp: timestamp ?? this.timestamp,
      expiresAt: expiresAt ?? this.expiresAt,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() =>
      'MarineData(id: $id, type: $dataType, title: $title, '
      'source: $source, ts: $timestamp)';
}
