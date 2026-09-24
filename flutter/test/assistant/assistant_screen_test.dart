import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/models/conversation/conversation_message.dart';
import 'package:samudra_ai/models/conversation/conversation_summary.dart';
import 'package:samudra_ai/screens/assistant/assistant_screen.dart';
import 'package:samudra_ai/services/conversation/conversation_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Widget tests for the conversational Assistant flow.
//
// A controllable stub ConversationService is injected via
// ConversationService.setInstance() so these tests are fully offline and
// deterministic — no backend, no network.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  late _StubConversationService stub;

  setUp(() {
    stub = _StubConversationService();
    ConversationService.setInstance(stub);
  });

  tearDown(() {
    // Restore the default implementation so nothing leaks across tests.
    ConversationService.setInstance(const LocalConversationService());
  });

  Future<void> pumpAssistant(WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: AssistantScreen())),
    );
  }

  group('Greeting', () {
    testWidgets('Assistant opens → greeting is displayed', (tester) async {
      await pumpAssistant(tester);
      expect(find.textContaining('How can I help you today?'), findsOneWidget);
      // Greeting alone must NOT trigger a backend request.
      expect(stub.callCount, 0);
    });
  });

  group('Send + response', () {
    testWidgets('user message appears, then response appears', (tester) async {
      await pumpAssistant(tester);

      await tester.enterText(find.byType(TextField), 'Sea conditions near Kochi?');
      await tester.pump(); // rebuild so the send button is active
      await tester.tap(find.byIcon(Icons.arrow_upward_rounded));
      await tester.pump(); // start the request
      await tester.pump(const Duration(milliseconds: 50));

      // User bubble appears.
      expect(find.text('Sea conditions near Kochi?'), findsOneWidget);
      // sendMessage called exactly once.
      expect(stub.callCount, 1);

      // Complete the stub and let it settle.
      await stub.complete('The sea is calm today with ~1.2 m waves.');
      await tester.pump();
      await tester.pump();

      // Assistant response appears.
      expect(find.textContaining('calm today'), findsOneWidget);
      // Loading cleared.
      expect(find.text('Thinking...'), findsNothing);
    });
  });

  group('Loading', () {
    testWidgets('typing indicator appears while waiting', (tester) async {
      await pumpAssistant(tester);

      await tester.enterText(find.byType(TextField), 'Is it safe today?');
      await tester.pump(); // rebuild so the send button is active
      await tester.tap(find.byIcon(Icons.arrow_upward_rounded));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      expect(find.text('Samudra is analyzing...'), findsOneWidget);
    });
  });

  group('Error handling', () {
    testWidgets('friendly error appears if the service fails', (tester) async {
      await pumpAssistant(tester);

      await tester.enterText(find.byType(TextField), 'Test error path');
      await tester.pump(); // rebuild so the send button is active
      await tester.tap(find.byIcon(Icons.arrow_upward_rounded));
      await tester.pump();

      // Fail the request with a user-facing exception.
      await stub.fail(const ConversationException(
        'I\u2019m having trouble connecting right now. Please try again in a moment.',
      ));
      await tester.pump();
      await tester.pump();

      expect(find.textContaining('having trouble connecting'), findsOneWidget);
      // Loading cleared.
      expect(find.text('Thinking...'), findsNothing);
    });

    testWidgets('unknown errors map to a friendly message', (tester) async {
      await pumpAssistant(tester);

      await tester.enterText(find.byType(TextField), 'Test unknown error');
      await tester.pump(); // rebuild so the send button is active
      await tester.tap(find.byIcon(Icons.arrow_upward_rounded));
      await tester.pump();

      await stub.fail(_UnexpectedError('boom'));
      await tester.pump();
      await tester.pump();

      expect(find.textContaining('Please try again in a moment'), findsOneWidget);
    });
  });

  group('Duplicate protection', () {
    testWidgets('rapid taps do not create multiple simultaneous requests',
        (tester) async {
      await pumpAssistant(tester);

      await tester.enterText(find.byType(TextField), 'tap rapidly');
      await tester.pump(); // rebuild so the send button is active
      final sendButton = find.byIcon(Icons.arrow_upward_rounded);

      // Tap several times without pumping in between. The send button is
      // replaced by a spinner only on the next frame, so it stays hittable —
      // this exercises the _submit guard (which must not issue a second call
      // once _isLoading is true).
      await tester.tap(sendButton, warnIfMissed: false);
      await tester.tap(sendButton, warnIfMissed: false);
      await tester.tap(sendButton, warnIfMissed: false);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      // Only one request should have been issued.
      expect(stub.callCount, 1);
    });
  });

  group('Persistent history reload', () {
    testWidgets('reopens an existing conversation instead of a fresh greeting',
        (tester) async {
      final historyStub = _HistoryStub([
        ConversationMessage.user('hi there'),
        ConversationMessage.assistant('Hello! How can I help?'),
      ]);
      ConversationService.setInstance(historyStub);

      await pumpAssistant(tester);
      await tester.pump(); // let the async history load settle + rebuild

      // Loaded history replaces the local greeting.
      expect(find.textContaining('How can I help you today?'), findsNothing);
      expect(find.text('hi there'), findsOneWidget);
      expect(find.text('Hello! How can I help?'), findsOneWidget);
    });

    testWidgets('keeps the greeting when nothing is persisted', (tester) async {
      // stub.loadHistory inherits the default no-op -> returns [].
      ConversationService.setInstance(stub);

      await pumpAssistant(tester);
      await tester.pump();

      expect(find.textContaining('How can I help you today?'), findsOneWidget);
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Test doubles
// ─────────────────────────────────────────────────────────────────────────────

/// Controllable stub whose [sendMessage] result is driven by the test.
class _StubConversationService implements ConversationService {
  int callCount = 0;

  Completer<String>? _pending;

  @override
  Future<String> sendMessage(String message) {
    callCount++;
    _pending = Completer<String>();
    return _pending!.future;
  }

  /// Complete the in-flight request with [response].
  Future<void> complete(String response) async {
    _pending?.complete(response);
    _pending = null;
  }

  /// Fail the in-flight request with [error].
  Future<void> fail(Object error) async {
    _pending?.completeError(error);
    _pending = null;
  }
}

/// A generic non-Conversation exception used to exercise the catch-all path.
class _UnexpectedError implements Exception {
  const _UnexpectedError(this.message);
  final String message;
  @override
  String toString() => message;
}

/// Stub that returns pre-populated history from [loadHistory].
class _HistoryStub implements ConversationService, ConversationHistoryProvider {
  _HistoryStub(this.history);
  final List<ConversationMessage> history;

  @override
  Future<String> sendMessage(String message) async => 'ok';

  @override
  Future<List<ConversationMessage>> loadHistory() async => history;

  @override
  Future<List<ConversationSummary>> loadConversations() async => const [];
}
