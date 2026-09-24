import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/services/speech/speech_synthesis_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for the text-to-speech facade.
//
// The real FlutterTts engine touches a platform channel, which is unavailable
// in the test VM — so calling initialize()/speak() fails fast and the facade
// must surface that as a friendly error and never throw.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  // FlutterTts hooks a method channel in its constructor, so we need a binding
  // before the engine is created (the "unavailable" test path).
  TestWidgetsFlutterBinding.ensureInitialized();

  tearDown(() {
    // Reset any callbacks so they don't leak between tests.
    SpeechSynthesisService.instance.onStart = null;
    SpeechSynthesisService.instance.onComplete = null;
    SpeechSynthesisService.instance.onError = null;
  });

  test('blank text is a no-op and never raises', () async {
    final svc = SpeechSynthesisService.instance;
    String? error;
    svc.onError = (msg) => error = msg;

    await svc.speak('   ');
    await svc.speak('');

    expect(error, isNull);
  });

  test('speak surfaces a friendly error when the engine is unavailable',
      () async {
    final svc = SpeechSynthesisService.instance;
    String? error;
    svc.onError = (msg) => error = msg;

    // In the test VM the platform channel is missing, so initialisation fails
    // and speak() must report a friendly message instead of throwing.
    await svc.speak('Hello Samudra');

    expect(error, isNotNull);
    expect(error, isNotEmpty);
  });
}
