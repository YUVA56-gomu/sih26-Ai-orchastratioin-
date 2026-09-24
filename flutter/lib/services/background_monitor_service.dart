import 'dart:async';
import 'dart:io' show Platform;
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart' as ph;
import 'location_service.dart';
import 'imbl_boundary_service.dart';
import '../models/location_data.dart';
import '../models/boundary_check_result.dart';
import '../utils/demo_imbl.dart';

// ─────────────────────────────────────────────────────────────────────────────
// BackgroundMonitorService — Milestone 5: background IMBL safety monitor
//
// ── What this service does ────────────────────────────────────────────────────
// Orchestrates the background safety pipeline:
//
//   Android foreground location service (via geolocator ForegroundNotificationConfig)
//     ↓
//   LocationService  ← EXISTING — not duplicated
//     ↓ LocationData
//   ImblBoundaryService  ← EXISTING — not duplicated
//     ↓ BoundaryCheckResult
//   BackgroundMonitorService (holds latest result, exposes streams)
//     ↓
//   Future: AlertService (Milestone 6 — buzzer/audio)
//
// ── Why a foreground service is required ─────────────────────────────────────
// Android 8+ aggressively kills background processes to save battery.
// A standard background Dart isolate will be suspended within minutes when
// the app is minimised.  A foreground service:
//   1. Shows a persistent notification so the user knows monitoring is active.
//   2. Prevents the OS from killing the process.
//   3. Allows continued GPS access under ACCESS_BACKGROUND_LOCATION rules.
//
// ── Notification permission (Android 13+, API 33+) ───────────────────────────
// POST_NOTIFICATIONS is declared in AndroidManifest.xml but also requires a
// runtime permission grant on Android 13+.  Without it the OS silently
// suppresses the foreground-service notification, making background execution
// unreliable.
//
// Approach:
//   - Use permission_handler to check / request POST_NOTIFICATIONS.
//   - On Android < 13 the manifest declaration is sufficient; no runtime
//     request is made.
//   - If denied, monitoring enters notificationPermissionBlocked state.
//   - The UI shows a "Grant Notification Permission" button.
//
// ── Location update configuration ────────────────────────────────────────────
// Accuracy:        LocationAccuracy.high  (GPS hardware)
// Interval:        10 seconds
// Distance filter: 10 metres
// Battery trade-off: tune once real IMBL data and field testing are available.
//
// ── IMPORTANT: DEMO DATA ─────────────────────────────────────────────────────
// Background monitoring uses the DEMO IMBL polygon only.
// NOT the real Indian IMBL. Do not use for real safety decisions.
// ─────────────────────────────────────────────────────────────────────────────

/// All possible states the background monitor can be in.
enum MonitorState {
  /// Monitor has never been started, or was cleanly stopped.
  stopped,

  /// Permissions are being requested or service is starting.
  starting,

  /// Actively receiving GPS and running IMBL checks.
  monitoring,

  /// Missing a required location permission — cannot continue.
  permissionRequired,

  /// POST_NOTIFICATIONS denied on Android 13+.
  /// The foreground-service notification will be suppressed by the OS.
  /// User must open Settings → Apps → SAMUDRA AI → Notifications to enable.
  notificationPermissionBlocked,

  /// GPS / location service is unavailable on this device.
  locationUnavailable,

  /// An unexpected error occurred.
  error,
}

/// A single snapshot produced during active monitoring.
class MonitorSnapshot {
  final LocationData location;
  final BoundaryCheckResult boundaryResult;

  /// Time taken by ImblBoundaryService.check() ONLY — not the GPS pipeline.
  final double imblCalcMs;

  final DateTime producedAt;

  const MonitorSnapshot({
    required this.location,
    required this.boundaryResult,
    required this.imblCalcMs,
    required this.producedAt,
  });

  @override
  String toString() =>
      'MonitorSnapshot('
      'classification: ${boundaryResult.classification.name}, '
      'dist: ${boundaryResult.distanceToBoundaryMeters?.toStringAsFixed(1)} m, '
      'calcMs: ${imblCalcMs.toStringAsFixed(2)}, '
      'at: $producedAt)';
}

class BackgroundMonitorService {
  BackgroundMonitorService._();

  static final BackgroundMonitorService instance = BackgroundMonitorService._();

  // ── Dependencies ──────────────────────────────────────────────────────────

  final _locationService = LocationService.instance;
  final _imblService = ImblBoundaryService.instance;

  // ── Internal state ────────────────────────────────────────────────────────

  StreamSubscription<LocationData>? _locationSub;
  MonitorState _state = MonitorState.stopped;
  MonitorSnapshot? _latestSnapshot;
  String? _errorMessage;
  bool _notificationGranted = false;

  // ── Public streams ────────────────────────────────────────────────────────

  final _stateController = StreamController<MonitorState>.broadcast();
  final _snapshotController = StreamController<MonitorSnapshot>.broadcast();

  Stream<MonitorState> get stateStream => _stateController.stream;
  Stream<MonitorSnapshot> get snapshotStream => _snapshotController.stream;

  // ── Public getters ────────────────────────────────────────────────────────

  MonitorState get state => _state;
  MonitorSnapshot? get latestSnapshot => _latestSnapshot;
  String? get errorMessage => _errorMessage;
  bool get isMonitoring => _state == MonitorState.monitoring;

  /// Whether the POST_NOTIFICATIONS permission is currently granted.
  /// Refreshed on every call to [checkNotificationPermission] or [start].
  bool get notificationGranted => _notificationGranted;

  // ── Notification permission API ───────────────────────────────────────────

  /// Check notification permission WITHOUT requesting it.
  Future<ph.PermissionStatus> checkNotificationPermission() async {
    if (!Platform.isAndroid) {
      _notificationGranted = true;
      return ph.PermissionStatus.granted;
    }
    final status = await ph.Permission.notification.status;
    _notificationGranted = status == ph.PermissionStatus.granted;
    return status;
  }

  /// Request the POST_NOTIFICATIONS runtime permission on Android 13+.
  Future<ph.PermissionStatus> requestNotificationPermission() async {
    if (!Platform.isAndroid) {
      _notificationGranted = true;
      return ph.PermissionStatus.granted;
    }
    final status = await ph.Permission.notification.request();
    _notificationGranted = status == ph.PermissionStatus.granted;
    return status;
  }

  /// Opens the system app-settings page so the user can manually enable
  /// the notification permission after permanent denial.
  Future<void> openNotificationSettings() => ph.openAppSettings();

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  /// Start background monitoring.
  ///
  /// Permission flow:
  ///   1a. Check / request location permission.
  ///   1b. Check / request POST_NOTIFICATIONS (Android 13+ only).
  ///   2.  Load DEMO IMBL polygon.
  ///   3.  Stop current location stream and restart with foreground config.
  ///   4.  Subscribe and run IMBL checks on every GPS fix.
  Future<void> start() async {
    if (_state == MonitorState.monitoring ||
        _state == MonitorState.starting) {
      return;
    }

    _emitState(MonitorState.starting);
    _errorMessage = null;

    try {
      // ── 1a Location permission ────────────────────────────────────────────
      final serviceOn = await _locationService.checkLocationService();
      if (!serviceOn) {
        _emitState(MonitorState.locationUnavailable);
        _errorMessage = 'Location services are disabled.';
        return;
      }

      var locPerm = await _locationService.checkPermission();
      if (locPerm == LocationPermission.denied) {
        locPerm = await _locationService.requestPermission();
      }
      if (locPerm == LocationPermission.denied ||
          locPerm == LocationPermission.deniedForever) {
        _emitState(MonitorState.permissionRequired);
        _errorMessage = locPerm == LocationPermission.deniedForever
            ? 'Location permission permanently denied. Open app settings.'
            : 'Location permission denied.';
        return;
      }

      // ── 1b Notification permission (Android 13+ only) ─────────────────────
      // POST_NOTIFICATIONS is declared in the manifest but requires runtime
      // grant on API 33+.  Without it the foreground-service notification is
      // silently suppressed and the OS may kill the background process.
      final notifStatus = await requestNotificationPermission();
      if (notifStatus != ph.PermissionStatus.granted) {
        _emitState(MonitorState.notificationPermissionBlocked);
        _errorMessage = notifStatus == ph.PermissionStatus.permanentlyDenied
            ? 'Notification permission permanently blocked. '
              'Open Settings → Apps → SAMUDRA AI → Notifications.'
            : 'Notification permission denied. '
              'Required for the safety-monitor notification on Android 13+.';
        return;
      }

      // ── 2  Load DEMO boundary ─────────────────────────────────────────────
      if (!_imblService.boundaries.any((b) => b.id == DemoImbl.id)) {
        _imblService.loadBoundary(DemoImbl.polygon());
      }

      // ── 3  Start foreground location stream ───────────────────────────────
      await _locationService.stopLocationStream();
      await _startForegroundLocationStream();

      // ── 4  Subscribe and run IMBL checks ──────────────────────────────────
      await _locationSub?.cancel();
      _locationSub = _locationService.locationStream.listen(
        _onLocationUpdate,
        onError: (_) {
          _emitState(MonitorState.error);
          _errorMessage = 'Location stream error.';
        },
        cancelOnError: false,
      );

      _emitState(MonitorState.monitoring);
    } catch (e) {
      _emitState(MonitorState.error);
      _errorMessage = 'Failed to start monitoring: $e';
    }
  }

  /// Stop background monitoring and restore normal foreground GPS stream.
  Future<void> stop() async {
    await _locationSub?.cancel();
    _locationSub = null;
    await _locationService.stopLocationStream();
    await _locationService.startLocationStream();
    _emitState(MonitorState.stopped);
  }

  // ── Internal: foreground location stream ─────────────────────────────────

  Future<void> _startForegroundLocationStream() async {
    final locationSettings = AndroidSettings(
      accuracy: LocationAccuracy.high,
      intervalDuration: const Duration(seconds: 10),
      distanceFilter: 0,
      foregroundNotificationConfig: const ForegroundNotificationConfig(
        notificationText:
            'SAMUDRA AI is monitoring your vessel position for IMBL safety.',
        notificationTitle: 'SAMUDRA AI — Safety Monitor Active',
        enableWakeLock: true,
      ),
    );
    await _locationService.startForegroundStream(locationSettings);
  }

  // ── Internal: process each GPS update ─────────────────────────────────────

  void _onLocationUpdate(LocationData location) {
    if (_state != MonitorState.monitoring) return;

    // Benchmark ONLY the IMBL calculation.
    final sw = Stopwatch()..start();
    final result = _imblService.check(
      location,
      DemoImbl.id,
      config: const BoundaryCheckConfig(warningDistanceMeters: 500.0),
    );
    sw.stop();

    final snapshot = MonitorSnapshot(
      location: location,
      boundaryResult: result,
      imblCalcMs: sw.elapsedMicroseconds / 1000.0,
      producedAt: DateTime.now().toUtc(),
    );

    _latestSnapshot = snapshot;
    _snapshotController.add(snapshot);
    // Safety: NEAR_BOUNDARY / OUTSIDE / UNKNOWN are never silently ignored.
    // Milestone 6 (AlertService) will act on them.
  }

  // ── Internal helpers ──────────────────────────────────────────────────────

  void _emitState(MonitorState s) {
    _state = s;
    _stateController.add(s);
  }

  // ── Dispose ───────────────────────────────────────────────────────────────

  Future<void> dispose() async {
    await _locationSub?.cancel();
    await _stateController.close();
    await _snapshotController.close();
  }
}
