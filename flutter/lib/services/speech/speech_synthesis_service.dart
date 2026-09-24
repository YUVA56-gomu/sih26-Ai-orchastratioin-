import 'package:flutter_tts/flutter_tts.dart';

/// Text-to-speech facade used by the voice dashboard to speak Samudra AI's
/// replies aloud.
///
/// It mirrors the app's existing settable-singleton service pattern (like
/// [ConversationService] and [SpeechService]) so the UI never touches the
/// platform TTS engine directly, and tests can inject a fake via
/// [SpeechSynthesisService.setInstance].
///
/// The engine is only touched asked to speak, never during widget construction,
/// so widget tests that don't use TTS stay fully offline.
class SpeechSynthesisService {
  SpeechSynthesisService._();

  static SpeechSynthesisService _instance = SpeechSynthesisService._();

  /// Shared instance. Swap via [setInstance] in tests or to change engines.
  static SpeechSynthesisService get instance => _instance;

  static void setInstance(SpeechSynthesisService service) {
    _instance = service;
  }

  /// The engine is created lazily — `FlutterTts` hooks a method channel in its
  /// constructor, so we must not touch it at singleton construction time (which
  /// may occur before the Widgets binding is ready, e.g. in tests).
  FlutterTts? _tts;

  bool _initialized = false;
  bool _available = true;
  bool _speaking = false;

  FlutterTts get _engine => _tts ??= FlutterTts();

  /// Fired when a spoken utterance starts. Populated by the caller.
  void Function()? onStart;

  /// Fired when a spoken utterance finishes (or is cancelled). Populated by
  /// the caller.
  void Function()? onComplete;

  /// Fired with a user-friendly message when the engine fails. Populated by
  /// the caller.
  void Function(String message)? onError;

  /// Whether the underlying engine initialised successfully.
  bool get isAvailable => _available;

  /// Whether we are mid-utterance.
  bool get isSpeaking => _speaking;

  /// Initialises the engine on first use. Safe to call repeatedly.
  /// Returns whether text-to-speech is available on this device.
  Future<bool> initialize() async {
    if (_initialized) return _available;
    try {
      _engine.setStartHandler(() {
        _speaking = true;
        onStart?.call();
      });
      _engine.setCompletionHandler(() {
        _speaking = false;
        onComplete?.call();
      });
      _engine.setCancelHandler(() {
        _speaking = false;
        onComplete?.call();
      });
      _engine.setErrorHandler((message) {
        _speaking = false;
        // ignore: avoid_dynamic_calls, cast_dynamic_to_null
        onError?.call(_friendly(message));
      });
      await _engine.setLanguage('en-US');
      _initialized = true;
      _available = true;
    } catch (_) {
      _available = false;
    }
    return _available;
  }

  /// Speaks [text] aloud. No-op if [text] is blank. Errors are surfaced via
  /// [onError] and never thrown — the UI stays alive.
  Future<void> speak(String text) async {
    final phrase = text.trim();
    if (phrase.isEmpty) return;
    try {
      if (!_initialized) {
        final ok = await initialize();
        if (!ok) {
          onError?.call('Text-to-speech isn\u2019t available on this device.');
          return;
        }
      }
      _speaking = true;
      onStart?.call();
      await _engine.speak(phrase);
    } catch (_) {
      _speaking = false;
      onError?.call('I couldn\u2019t speak that. Please try again.');
    }
  }

  /// Stops the current utterance. Best-effort, never throws.
  Future<void> stop() async {
    try {
      await _engine.stop();
    } catch (_) {
      // ignore — stopping is best-effort.
    }
    _speaking = false;
  }

  /// Maps opaque engine errors to a stable, user-facing message.
  String _friendly(dynamic raw) {
    final s = '$raw'.toLowerCase();
    if (s.contains('synthesis') ||
        s.contains('engine') ||
        s.contains('initialize') ||
        s.contains('unavailable')) {
      return 'Text-to-speech isn\u2019t available on this device.';
    }
    return 'I couldn\u2019t speak that. Please try again.';
  }
}
