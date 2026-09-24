import 'dart:async';
import 'package:geolocator/geolocator.dart';
import '../models/location_data.dart';

// ─────────────────────────────────────────────────────────────────────────────
// LocationService — GPS/GNSS abstraction layer (Milestone 2)
//
// Architecture pipeline this feeds into:
//   GPS/GNSS
//     ↓ LocationService          ← this file
//     ↓ SQLite spatial cache     (Milestone 3)
//     ↓ IMBL point-in-polygon    (Milestone 4)
//     ↓ Background monitor       (Milestone 5)
//     ↓ Local emergency alert    (Milestone 6)
//     ↓ NavIC/NMEA integration   (Milestone 7)
//
// All UI code interacts with LocationService only — never with geolocator
// directly. This keeps the plugin swappable without changing any widgets.
// ─────────────────────────────────────────────────────────────────────────────

/// Represents every distinct state the location subsystem can be in.
enum LocationStatus {
  /// Has not been initialised yet.
  idle,

  /// Location services are disabled on the device (Settings → Location).
  serviceDisabled,

  /// The user has not yet responded to the permission prompt.
  permissionDenied,

  /// The user tapped "Don't ask again" / permanently denied.
  permissionPermanentlyDenied,

  /// Permission granted and actively streaming fixes.
  active,

  /// Permission granted but no fix received yet.
  searching,

  /// A recoverable error occurred (timeout, provider temporarily unavailable).
  error,
}

class LocationService {
  LocationService._();

  /// Singleton — the rest of the app always uses [LocationService.instance].
  static final LocationService instance = LocationService._();

  // ── Internal state ────────────────────────────────────────────────────────

  StreamSubscription<Position>? _positionSubscription;

  // Public stream that the UI listens to for live location updates.
  final StreamController<LocationData> _locationController =
      StreamController<LocationData>.broadcast();

  // Public stream for status changes so the UI can react without polling.
  final StreamController<LocationStatus> _statusController =
      StreamController<LocationStatus>.broadcast();

  LocationStatus _currentStatus = LocationStatus.idle;
  LocationData? _lastLocation;

  // ── Public API ────────────────────────────────────────────────────────────

  /// The last successfully received location fix, or null if none yet.
  LocationData? get lastLocation => _lastLocation;

  /// Current permission/service status.
  LocationStatus get currentStatus => _currentStatus;

  /// Stream of [LocationData] fixes as they arrive from the device.
  Stream<LocationData> get locationStream => _locationController.stream;

  /// Stream of [LocationStatus] transitions.
  Stream<LocationStatus> get statusStream => _statusController.stream;

  // ── Checks ────────────────────────────────────────────────────────────────

  /// Returns true if the device's location services (GPS/Network) are on.
  Future<bool> checkLocationService() async {
    return Geolocator.isLocationServiceEnabled();
  }

  /// Returns the current permission state without requesting anything.
  Future<LocationPermission> checkPermission() async {
    return Geolocator.checkPermission();
  }

  /// Requests foreground location permission from the user.
  /// Returns the resulting [LocationPermission].
  Future<LocationPermission> requestPermission() async {
    return Geolocator.requestPermission();
  }

  // ── One-shot location ─────────────────────────────────────────────────────

  /// Fetches a single location fix.
  /// Returns null and updates [currentStatus] on any failure.
  Future<LocationData?> getCurrentLocation() async {
    try {
      // Check services first
      final serviceEnabled = await checkLocationService();
      if (!serviceEnabled) {
        _emitStatus(LocationStatus.serviceDisabled);
        return null;
      }

      // Check / request permission
      var permission = await checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await requestPermission();
      }
      if (permission == LocationPermission.denied) {
        _emitStatus(LocationStatus.permissionDenied);
        return null;
      }
      if (permission == LocationPermission.deniedForever) {
        _emitStatus(LocationStatus.permissionPermanentlyDenied);
        return null;
      }

      _emitStatus(LocationStatus.searching);

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 20),
        ),
      );

      final data = _toLocationData(position);
      _lastLocation = data;
      _emitStatus(LocationStatus.active);
      return data;
    } on TimeoutException {
      _emitStatus(LocationStatus.error);
      return null;
    } catch (e) {
      _emitStatus(LocationStatus.error);
      return null;
    }
  }

  // ── Location stream ───────────────────────────────────────────────────────

  /// Starts a continuous foreground location stream.
  /// Idempotent — if a stream is already active and permission is granted,
  /// this call is a no-op. Call stopLocationStream() first to force a restart.
  Future<void> startLocationStream() async {
    // Already streaming — don't restart
    if (_positionSubscription != null) return;

    final serviceEnabled = await checkLocationService();
    if (!serviceEnabled) {
      _emitStatus(LocationStatus.serviceDisabled);
      return;
    }

    var permission = await checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await requestPermission();
    }
    if (permission == LocationPermission.denied) {
      _emitStatus(LocationStatus.permissionDenied);
      return;
    }
    if (permission == LocationPermission.deniedForever) {
      _emitStatus(LocationStatus.permissionPermanentlyDenied);
      return;
    }

    _emitStatus(LocationStatus.searching);

    // Android-specific: request best accuracy, update every 5 seconds
    // or when the device moves more than 5 metres.
    final locationSettings = AndroidSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 5,           // metres
      intervalDuration: const Duration(seconds: 5),
      // foregroundNotificationConfig is intentionally omitted —
      // background location is NOT enabled in this milestone.
    );

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen(
      (position) {
        final data = _toLocationData(position);
        _lastLocation = data;
        _emitStatus(LocationStatus.active);
        _locationController.add(data);
      },
      onError: (Object error) {
        _emitStatus(LocationStatus.error);
      },
      cancelOnError: false,
    );
  }

  /// Stops the active location stream.
  Future<void> stopLocationStream() async {
    await _positionSubscription?.cancel();
    _positionSubscription = null;
  }

  // ── Background / foreground-service stream ────────────────────────────────

  /// Starts a location stream with caller-supplied [settings].
  ///
  /// Used by [BackgroundMonitorService] to pass an [AndroidSettings] that
  /// includes [ForegroundNotificationConfig].  Emits through the same
  /// [locationStream] broadcast so all existing subscribers see updates.
  ///
  /// Stops any existing subscription before starting the new one.
  Future<void> startForegroundStream(AndroidSettings settings) async {
    await stopLocationStream();

    _emitStatus(LocationStatus.searching);

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: settings,
    ).listen(
      (position) {
        final data = _toLocationData(position);
        _lastLocation = data;
        _emitStatus(LocationStatus.active);
        _locationController.add(data);
      },
      onError: (Object error) {
        _emitStatus(LocationStatus.error);
      },
      cancelOnError: false,
    );
  }

  /// Opens the device's location settings page so the user can enable GPS.
  Future<bool> openLocationSettings() => Geolocator.openLocationSettings();

  /// Opens the app's permission settings page for permanently-denied cases.
  Future<bool> openAppSettings() => Geolocator.openAppSettings();

  // ── Dispose ───────────────────────────────────────────────────────────────

  /// Must be called when the app exits to release resources.
  /// In practice this is called from main.dart or a top-level provider.
  Future<void> dispose() async {
    await stopLocationStream();
    await _locationController.close();
    await _statusController.close();
  }

  // ── Private helpers ───────────────────────────────────────────────────────

  void _emitStatus(LocationStatus status) {
    _currentStatus = status;
    _statusController.add(status);
  }

  /// Converts a raw geolocator [Position] into the app-level [LocationData].
  LocationData _toLocationData(Position position) {
    return LocationData(
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy,
      // speed can be negative (-1.0) when unavailable — clamp to 0
      speed: position.speed < 0 ? 0.0 : position.speed,
      // heading can be -1.0 when unavailable — clamp to 0
      heading: position.heading < 0 ? 0.0 : position.heading,
      timestamp: position.timestamp,
    );
  }
}
