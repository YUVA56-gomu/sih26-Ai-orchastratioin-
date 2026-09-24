import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/screens/voice_assistant/voice_assistant_screen.dart';
import 'package:samudra_ai/services/conversation/conversation_service.dart';
import 'package:samudra_ai/services/speech/speech_service.dart';
import 'package:samudra_ai/services/speech/speech_synthesis_service.dart';
import 'package:samudra_ai/widgets/agent_voice_orb.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Widget tests for the voice-first dashboard.
//
// All three service dependencies are swapped for controllable fakes via
// setInstance(), so the tests are fully offline and deterministic. The real
// recogniser / TTS / backend are never touched.
//
// The orb runs an infinite wave animation while any state is active, so these
// tests must pump by duration (never pumpAndSettle) during listening/thinking/
// speaking.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  late _StubConversationService conv;
  late _FakeSpeech speech;
  late _FakeTts tts;

  setUp(() {
    conv = _StubConversationService();
    speech = _FakeSpeech();
    tts = _FakeTts();
    ConversationService.setInstance(conv);
    SpeechService.setInstance(speech);
    SpeechSynthesisService.setInstance(tts);
  });

  tearDown(() {
    // Restore the default backend so nothing leaks. The speech / TTS mocks are
    // replaced fresh in every setUp.
    ConversationService.setInstance(const LocalConversationService());
  });

  Future<void> pumpDashboard(
    WidgetTester tester, {
    String? pendingQuery,
  }) async {
    await tester.pumpWidget(
      MaterialApp(home: VoiceAssistantScreen(pendingQuery: pendingQuery)),
    );
  }

  String stateLabel(WidgetTester tester) {
    final finder = find.text('Listening… speak now').hitTestable();
    if (finder.evaluate().isNotEmpty) return 'listening';
    if (find.text('Samudra AI is thinking…').evaluate().isNotEmpty) {
      return 'thinking';
    }
    if (find.text('Samudra AI is speaking…').evaluate().isNotEmpty) {
      return 'speaking';
    }
    if (find.text('Tap the orb to speak').evaluate().isNotEmpty) {
      return 'idle';
    }
    return 'unknown';
  }

  group('Idle + auto-listening open', () {
    testWidgets('opens listening when no pending query', (tester) async {
      await pumpDashboard(tester);
      await tester.pump(); // post-frame callback → _startListening starts
      await tester.pump(); // permission + init resolve
      await tester.pump();

      expect(stateLabel(tester), 'listening');
      expect(find.text('Listening… speak now'), findsOneWidget);
      expect(conv.callCount, 0);
    });

    testWidgets('denied permission shows friendly message and idles',
        (tester) async {
      speech.permission = MicPermission.denied;
      await pumpDashboard(tester);
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'idle');
      expect(
        find.text('Microphone permission is needed for voice input.'),
        findsOneWidget,
      );
    });

    testWidgets('engine ends with no result → returns to idle, no send',
        (tester) async {
      await pumpDashboard(tester);
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'listening');

      // The engine times out / user stays silent (status, not error).
      speech.stopListening();
      await tester.pump();

      expect(stateLabel(tester), 'idle');
      expect(
        find.text('I didn\u2019t catch that. Tap the orb and speak again.'),
        findsOneWidget,
      );
      expect(conv.callCount, 0);
    });
  });

  group('Speak → reply → spoken aloud', () {
    testWidgets('transcribes, sends, then speaks the reply', (tester) async {
      await pumpDashboard(tester);
      await tester.pump();
      await tester.pump();

      // Simulate the user speaking a phrase.
      speech.emit('Sea conditions near Kochi?');
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'thinking');
      expect(find.text('Sea conditions near Kochi?'), findsOneWidget);
      expect(conv.callCount, 1);

      // Backend replies.
      await conv.complete('The sea is calm with about 1.2 m waves.');
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'speaking');
      expect(find.textContaining('calm'), findsOneWidget);
      expect(tts.spoken, ['The sea is calm with about 1.2 m waves.']);

      // Speech finishes → back to idle.
      tts.finish();
      await tester.pump();
      await tester.pump();
      expect(stateLabel(tester), 'idle');
    });

    testWidgets('pendingQuery sends + speaks without listening',
        (tester) async {
      await pumpDashboard(tester, pendingQuery: 'fishing zones near shore');
      await tester.pump();
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'thinking');
      expect(find.text('fishing zones near shore'), findsOneWidget);
      expect(conv.callCount, 1);

      await conv.complete('Fishing zones are active off the coast.');
      await tester.pump();
      await tester.pump();

      expect(tts.spoken, ['Fishing zones are active off the coast.']);
      expect(stateLabel(tester), 'speaking');
    });
  });

  group('Error handling', () {
    testWidgets('backend failure shows a friendly message', (tester) async {
      await pumpDashboard(tester);
      await tester.pump();
      await tester.pump();

      speech.emit('test backend failure');
      await tester.pump();
      await tester.pump();

      await conv.fail(const ConversationException(
        'I\u2019m having trouble connecting right now. Please try again in a moment.',
      ));
      await tester.pump();
      await tester.pump();

      expect(
        find.textContaining('having trouble connecting'),
        findsOneWidget,
      );
      expect(stateLabel(tester), 'idle');
    });
  });

  group('Cancel', () {
    testWidgets('tap while listening cancels and idles', (tester) async {
      await pumpDashboard(tester);
      await tester.pump();
      await tester.pump();

      expect(stateLabel(tester), 'listening');

      await tester.tap(find.byType(AgentVoiceOrb));
      await tester.pump();

      expect(find.text('Voice input cancelled.'), findsOneWidget);
      expect(stateLabel(tester), 'idle');
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Test doubles
// ─────────────────────────────────────────────────────────────────────────────

/// Controllable backend stub with a Completer-driven [sendMessage].
class _StubConversationService implements ConversationService {
  int callCount = 0;
  Completer<String>? _pending;

  @override
  Future<String> sendMessage(String message) {
    callCount++;
    _pending = Completer<String>();
    return _pending!.future;
  }

  Future<void> complete(String response) async {
    _pending?.complete(response);
    _pending = null;
  }

  Future<void> fail(Object error) async {
    _pending?.completeError(error);
    _pending = null;
  }
}

/// Fake speech-to-text service. Emits a phrase on demand.
class _FakeSpeech implements SpeechService {
  MicPermission permission = MicPermission.granted;
  bool initOk = true;
  void Function(String text)? _onResult;
  void Function(String message)? _onError;
  void Function()? _onEnded;

  @override
  bool get isAvailable => initOk;

  @override
  bool get isListening => false;

  @override
  Future<bool> initialize() async => initOk;

  @override
  Future<MicPermission> resolveMicrophonePermission() async => permission;

  @override
  Future<void> openSettings() async {}

  @override
  Future<void> startListening({
    required void Function(String text) onResult,
    void Function(String message)? onError,
    void Function()? onEnded,
  }) async {
    _onResult = onResult;
    _onError = onError;
    _onEnded = onEnded;
  }

  @override
  Future<void> stop() async {}

  @override
  Future<void> cancel() async {}

  void emit(String text) => _onResult?.call(text);

  void error(String message) => _onError?.call(message);

  void stopListening() => _onEnded?.call();
}

/// Fake text-to-speech service. Records spoken phrases and lets the test
/// trigger completion.
class _FakeTts implements SpeechSynthesisService {
  final List<String> spoken = [];
  bool _speaking = false;
  Completer<void>? _speakCompleter;

  @override
  void Function()? onStart;

  @override
  void Function()? onComplete;

  @override
  void Function(String message)? onError;

  @override
  bool get isAvailable => true;

  @override
  bool get isSpeaking => _speaking;

  @override
  Future<bool> initialize() async => true;

  @override
  Future<void> speak(String text) async {
    spoken.add(text);
    _speaking = true;
    onStart?.call();
    _speakCompleter = Completer<void>();
    await _speakCompleter!.future;
    _speaking = false;
    onComplete?.call();
  }

  @override
  Future<void> stop() async {
    _speaking = false;
  }

  void finish() {
    if (_speakCompleter != null && !_speakCompleter!.isCompleted) {
      _speakCompleter!.complete();
    }
  }
}
