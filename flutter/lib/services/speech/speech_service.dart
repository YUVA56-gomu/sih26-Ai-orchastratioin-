import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Microphone permission resolution for voice input.
enum MicPermission {
  granted,
  denied,
  permanentlyDenied,
}

/// SpeechService — thin, self-contained facade over the platform speech
/// recogniser (speech_to_text) plus microphone permission handling
/// (permission_handler).
///
/// It mirrors the app's existing service pattern (a settable singleton like
/// [ConversationService]) so the UI never touches low-level platform APIs, and
/// tests can inject a fake via [SpeechService.setInstance].
///
/// The recogniser and microphone are only touched when a mic button is tapped,
/// so no platform channel is invoked during widget construction — this keeps
/// widget tests that don't use the microphone fully offline.
class SpeechService {
  SpeechService._();

  static SpeechService _instance = SpeechService._();

  /// Shared instance. Swap via [setInstance] in tests or to change engines.
  static SpeechService get instance => _instance;

  static void setInstance(SpeechService service) {
    _instance = service;
  }

  final SpeechToText _speech = SpeechToText();
  bool _available = false;
  bool _listening = false;

  /// Most recent error handler, wired to the recogniser's global error
  /// callback (speech_to_text delivers listening errors via `initialize`,
  /// not via `listen`).
  void Function(String message)? _onError;

  /// Fired when the recogniser stops (no speech / timed out) without producing
  /// a result. Lets the UI return to idle instead of hanging on "listening".
  void Function()? _onEnded;

  /// Whether the platform speech recogniser initialised successfully.
  bool get isAvailable => _available;

  /// Whether we are currently capturing audio.
  bool get isListening => _listening;

  /// Initialises the recogniser on first use. Safe to call repeatedly.
  /// Returns whether speech recognition is available on this device.
  Future<bool> initialize() async {
    if (_available) return true;
    try {
      _available = await _speech.initialize(
        onStatus: (status) {
          // status: "listening" | "notListening" | "done"
          if (status == 'done' || status == 'notListening') {
            _listening = false;
            _onEnded?.call();
          }
        },
        onError: (error) {
          _listening = false;
          _onError?.call(_friendlyError(error.errorMsg));
        },
      );
    } catch (_) {
      _available = false;
    }
    return _available;
  }

  /// Resolves microphone permission, requesting it if not yet asked.
  /// Distinguishes "permanently denied" so the UI can offer a settings path.
  Future<MicPermission> resolveMicrophonePermission() async {
    try {
      var status = await Permission.microphone.status;
      if (status.isGranted) return MicPermission.granted;
      if (status.isPermanentlyDenied) return MicPermission.permanentlyDenied;
      status = await Permission.microphone.request();
      if (status.isGranted) return MicPermission.granted;
      if (status.isPermanentlyDenied) return MicPermission.permanentlyDenied;
      return MicPermission.denied;
    } catch (_) {
      return MicPermission.denied;
    }
  }

  /// Opens the app's system settings (for permanently-denied permissions).
  Future<void> openSettings() async {
    try {
      // ignore: deprecated_member_use
      await openAppSettings();
    } catch (_) {
      // Best-effort; never crash the UI if settings can't be opened.
    }
  }

  /// Starts listening. [onResult] fires with the fully recognised text.
  /// [onError] fires with a human-friendly message on failure.
  Future<void> startListening({
    required void Function(String text) onResult,
    void Function(String message)? onError,
    void Function()? onEnded,
  }) async {
    _onError = onError;
    _onEnded = onEnded;
    _listening = true;
    // Ensure the recogniser is initialised (the error callback is registered
    // there — speech_to_text delivers listen errors through `initialize`).
    if (!_available) {
      final ok = await initialize();
      if (!ok) {
        _listening = false;
        onError?.call('Speech recognition is unavailable on this device.');
        return;
      }
    }
    try {
      await _speech.listen(
        onResult: (result) {
          // Act ONLY on the final, settled result. The engine streams partial
          // words as the user speaks; handling those sends an incomplete query
          // and stops the recogniser too early (which made input inaccurate).
          if (!result.finalResult) return;
          final text = result.recognizedWords;
          if (text.trim().isNotEmpty) onResult(text.trim());
        },
        listenOptions: SpeechListenOptions(
          partialResults: true,
          listenMode: ListenMode.dictation,
        ),
      );
    } catch (_) {
      _listening = false;
      onError?.call('Speech recognition could not start on this device.');
    }
  }

  /// Stops listening and delivers the final recognised text via [onResult].
  /// Safe to call from a cancel path (no text is delivered).
  Future<void> stop() async {
    _listening = false;
    try {
      await _speech.stop();
    } catch (_) {
      // ignore — stopping is best-effort.
    }
  }

  /// Cancels the current recognition session without delivering text.
  Future<void> cancel() async {
    _listening = false;
    try {
      await _speech.cancel();
    } catch (_) {
      // ignore — cancelling is best-effort.
    }
  }

  /// Maps opaque recogniser errors to a stable, user-facing message. Distinguishes
  /// a soft "no speech heard" (so the UI can prompt a retry calmly) from a real
  /// device/network fault.
  String _friendlyError(String raw) {
    final lower = raw.toLowerCase();
    if (lower.contains('permission')) {
      return 'Microphone permission is required for voice input.';
    }
    if (lower.contains('no_match') ||
        lower.contains('no match') ||
        lower.contains('no_speech') ||
        lower.contains('speech_timeout') ||
        lower.contains('timeout') ||
        lower.contains('no speech')) {
      return 'I didn\u2019t catch that. Tap the orb and speak again.';
    }
    if (lower.contains('audio') ||
        lower.contains('busy') ||
        lower.contains('client')) {
      return 'The microphone couldn\u2019t be used right now. Please try again.';
    }
    if (lower.contains('unavailable') ||
        lower.contains('network') ||
        lower.contains('offline')) {
      return 'Voice input isn\u2019t available right now. Please check network '
          'and try again.';
    }
    if (lower.contains('stopped')) {
      return 'Voice input stopped. Tap the orb and try again.';
    }
    return 'I couldn\u2019t understand that. Please try again.';
  }
}
