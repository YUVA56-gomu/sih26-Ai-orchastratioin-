import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/marine_data.dart';
import '../models/imbl_boundary.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DatabaseService — local SQLite layer (Milestone 3 + 4)
//
// Architecture pipeline this feeds into:
//   Online data / GPS fixes
//     ↓ DatabaseService          ← this file
//     ↓ IMBL spatial engine      (Milestone 4 — ImblBoundaryService)
//     ↓ Background monitor       (Milestone 5)
//     ↓ Emergency alert          (Milestone 6)
//     ↓ Backend API sync         (Milestone 8)
//
// UI widgets NEVER import sqflite directly.  All SQL lives here.
// ─────────────────────────────────────────────────────────────────────────────

/// Current schema version.  Increment when the schema changes.
/// v1 — marine_data table (Milestone 3)
/// v2 — imbl_boundaries table added (Milestone 4)
const int _kDbVersion = 2;

/// Name of the local database file on-device.
const String _kDbName = 'samudra_ai.db';

class DatabaseService {
  DatabaseService._();

  /// Singleton — obtain via [DatabaseService.instance].
  static final DatabaseService instance = DatabaseService._();

  Database? _db;

  // ── Initialisation ────────────────────────────────────────────────────────

  /// Opens (or creates) the local database.
  /// Must be called before any other method.  Safe to call multiple times.
  Future<void> initialize() async {
    if (_db != null && _db!.isOpen) return; // already open

    final dbPath = join(await getDatabasesPath(), _kDbName);

    _db = await openDatabase(
      dbPath,
      version: _kDbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  /// Closes the database.  Call on app shutdown if needed.
  Future<void> close() async {
    await _db?.close();
    _db = null;
  }

  // ── Schema ────────────────────────────────────────────────────────────────

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE marine_data (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type   TEXT    NOT NULL,
        title       TEXT    NOT NULL,
        description TEXT    NOT NULL DEFAULT '',
        latitude    REAL,
        longitude   REAL,
        value       TEXT,
        unit        TEXT,
        source      TEXT    NOT NULL DEFAULT 'unknown',
        timestamp   TEXT    NOT NULL,
        expires_at  TEXT,
        created_at  TEXT    NOT NULL,
        updated_at  TEXT    NOT NULL
      )
    ''');

    // Index on data_type for fast type-filtered queries.
    await db.execute(
        'CREATE INDEX idx_marine_data_type ON marine_data (data_type)');

    // Composite index on lat/lon to support bounding-box queries.
    // Milestone 4 will add polygon/region tables on top of this foundation.
    await db.execute(
        'CREATE INDEX idx_marine_data_latlon ON marine_data (latitude, longitude)');

    // Index on expires_at so stale-record cleanup is efficient.
    await db.execute(
        'CREATE INDEX idx_marine_data_expires ON marine_data (expires_at)');

    // Milestone 4: IMBL boundary table.
    await _createImblTable(db);
  }

  static Future<void> _createImblTable(Database db) async {
    await db.execute('''
      CREATE TABLE imbl_boundaries (
        id           TEXT    PRIMARY KEY,
        name         TEXT    NOT NULL,
        region       TEXT    NOT NULL DEFAULT '',
        polygon_flat TEXT    NOT NULL,
        source       TEXT    NOT NULL DEFAULT 'unknown',
        updated_at   TEXT    NOT NULL,
        created_at   TEXT    NOT NULL
      )
    ''');
    // Index by region for multi-region queries (future milestones).
    await db.execute(
        'CREATE INDEX idx_imbl_region ON imbl_boundaries (region)');
  }

  /// Upgrade path — increment _kDbVersion and add ALTER TABLE / new tables here
  /// when the schema changes in a future milestone.
  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      // Milestone 4: add IMBL boundary table to existing databases.
      await _createImblTable(db);
    }
    // Future: if (oldVersion < 3) { ... }
  }

  // ── Internal helper ───────────────────────────────────────────────────────

  Database get _database {
    if (_db == null || !_db!.isOpen) {
      throw StateError(
          'DatabaseService not initialised. Call initialize() first.');
    }
    return _db!;
  }

  // ── Insert ────────────────────────────────────────────────────────────────

  /// Insert a single [MarineData] record.
  /// Returns the new row ID.
  Future<int> insert(MarineData data) async {
    return _database.insert(
      'marine_data',
      data.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Insert multiple records in a single transaction for efficiency.
  /// Returns the list of inserted row IDs.
  Future<List<int>> insertAll(List<MarineData> records) async {
    final ids = <int>[];
    await _database.transaction((txn) async {
      final batch = txn.batch();
      for (final record in records) {
        batch.insert(
          'marine_data',
          record.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
      final results = await batch.commit(noResult: false);
      for (final r in results) {
        if (r is int) ids.add(r);
      }
    });
    return ids;
  }

  // ── Update ────────────────────────────────────────────────────────────────

  /// Update an existing record by its [id].
  /// Returns number of rows affected (0 if the record was not found).
  Future<int> update(MarineData data) async {
    if (data.id == null) return 0;
    final updated = data.copyWith(updatedAt: DateTime.now().toUtc());
    return _database.update(
      'marine_data',
      updated.toMap(),
      where: 'id = ?',
      whereArgs: [data.id],
    );
  }

  // ── Delete ────────────────────────────────────────────────────────────────

  /// Delete a single record by its [id].
  Future<int> delete(int id) async {
    return _database.delete(
      'marine_data',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Delete all records of a given [dataType].
  Future<int> deleteByType(String dataType) async {
    return _database.delete(
      'marine_data',
      where: 'data_type = ?',
      whereArgs: [dataType],
    );
  }

  /// Delete ALL records.  Used by the dev "Clear Test Data" button.
  Future<int> deleteAll() async {
    return _database.delete('marine_data');
  }

  /// Delete records whose [expires_at] is earlier than [before] (UTC).
  Future<int> deleteExpired({DateTime? before}) async {
    final cutoff = (before ?? DateTime.now()).toUtc().toIso8601String();
    return _database.delete(
      'marine_data',
      where: 'expires_at IS NOT NULL AND expires_at < ?',
      whereArgs: [cutoff],
    );
  }

  // ── Queries ───────────────────────────────────────────────────────────────

  /// Retrieve a single record by primary key.  Returns null if not found.
  Future<MarineData?> getById(int id) async {
    final rows = await _database.query(
      'marine_data',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return MarineData.fromMap(rows.first);
  }

  /// Retrieve every record, newest first.
  Future<List<MarineData>> getAll() async {
    final rows = await _database.query(
      'marine_data',
      orderBy: 'created_at DESC',
    );
    return rows.map(MarineData.fromMap).toList();
  }

  /// Retrieve records filtered by [dataType], newest first.
  Future<List<MarineData>> getByType(String dataType) async {
    final rows = await _database.query(
      'marine_data',
      where: 'data_type = ?',
      whereArgs: [dataType],
      orderBy: 'created_at DESC',
    );
    return rows.map(MarineData.fromMap).toList();
  }

  /// Simple bounding-box query — returns records whose lat/lon falls within
  /// [latDelta] degrees of latitude and [lonDelta] degrees of longitude
  /// from the given [lat]/[lon] centre.
  ///
  /// NOTE: This is NOT geospatial polygon arithmetic.
  /// It is a rectangular approximation only and is appropriate for short
  /// distances (<100 km) where spherical distortion is negligible.
  /// Milestone 4 will add proper IMBL polygon containment on top of this.
  Future<List<MarineData>> getNearLocation(
    double lat,
    double lon, {
    double latDelta = 1.0,
    double lonDelta = 1.0,
  }) async {
    final rows = await _database.query(
      'marine_data',
      where: '''
        latitude  IS NOT NULL AND longitude IS NOT NULL
        AND latitude  BETWEEN ? AND ?
        AND longitude BETWEEN ? AND ?
      ''',
      whereArgs: [
        lat - latDelta,
        lat + latDelta,
        lon - lonDelta,
        lon + lonDelta,
      ],
      orderBy: 'created_at DESC',
    );
    return rows.map(MarineData.fromMap).toList();
  }

  /// Returns the total number of rows in the marine_data table.
  Future<int> count() async {
    final result = await _database
        .rawQuery('SELECT COUNT(*) AS cnt FROM marine_data');
    return (result.first['cnt'] as int?) ?? 0;
  }

  /// Returns the UTC timestamp of the most recently created record, or null.
  Future<DateTime?> lastUpdated() async {
    final result = await _database.rawQuery(
        'SELECT MAX(created_at) AS last FROM marine_data');
    final raw = result.first['last'] as String?;
    if (raw == null) return null;
    return DateTime.parse(raw).toUtc();
  }

  // ── IMBL boundary persistence ─────────────────────────────────────────────

  /// Persist a boundary polygon to SQLite.
  /// Uses REPLACE so the same id can be re-inserted to update geometry.
  Future<void> saveBoundary(ImblBoundary boundary) async {
    final now = DateTime.now().toUtc().toIso8601String();
    final map = boundary.toMap();
    map['created_at'] = now;
    await _database.insert(
      'imbl_boundaries',
      map,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Save multiple boundaries in one transaction.
  Future<void> saveBoundaries(List<ImblBoundary> list) async {
    final now = DateTime.now().toUtc().toIso8601String();
    await _database.transaction((txn) async {
      final batch = txn.batch();
      for (final b in list) {
        final map = b.toMap();
        map['created_at'] = now;
        batch.insert('imbl_boundaries', map,
            conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await batch.commit(noResult: true);
    });
  }

  /// Retrieve a single boundary by its string [id].
  Future<ImblBoundary?> getBoundaryById(String id) async {
    final rows = await _database.query(
      'imbl_boundaries',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return ImblBoundary.fromMap(rows.first);
  }

  /// Retrieve all stored boundaries.
  Future<List<ImblBoundary>> getAllBoundaries() async {
    final rows = await _database.query('imbl_boundaries');
    return rows.map(ImblBoundary.fromMap).toList();
  }

  /// Delete a boundary by its string [id].
  Future<int> deleteBoundary(String id) async {
    return _database.delete(
      'imbl_boundaries',
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
