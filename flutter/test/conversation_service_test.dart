import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/services/conversation/conversation_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Unit tests for ConversationService and LocalConversationService.
//
// These tests run fully offline — no backend, no network.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  group('LocalConversationService', () {
    late LocalConversationService svc;

    setUp(() => svc = const LocalConversationService());

    test('returns a non-empty response', () async {
      final response = await svc.sendMessage('Hello');
      expect(response, isNotEmpty);
    });

    test('response contains the original message', () async {
      const query = 'Is it safe to fish today?';
      final response = await svc.sendMessage(query);
      expect(response, contains(query));
    });

    test('response is clearly marked as a placeholder', () async {
      final response = await svc.sendMessage('test');
      // Response must not pretend to be real AI or Google ADK output.
      expect(
        response.toLowerCase(),
        anyOf(
          contains('placeholder'),
          contains('local'),
          contains('future'),
          contains('being developed'),
        ),
      );
    });

    test('handles an empty string gracefully', () async {
      // Even an empty message must not throw.
      final response = await svc.sendMessage('');
      expect(response, isNotEmpty);
    });

    test('handles a very long message gracefully', () async {
      final longMessage = 'word ' * 200;
      final response = await svc.sendMessage(longMessage.trim());
      expect(response, isNotEmpty);
    });
  });

  group('ConversationService instance management', () {
    test('default instance is LocalConversationService', () {
      expect(
        ConversationService.instance,
        isA<LocalConversationService>(),
      );
    });

    test('setInstance replaces the active implementation', () {
      final custom = _EchoConversationService();
      ConversationService.setInstance(custom);
      expect(ConversationService.instance, same(custom));

      // Restore the default so other tests are not affected.
      ConversationService.setInstance(const LocalConversationService());
    });

    test('custom implementation is called via instance', () async {
      ConversationService.setInstance(const _EchoConversationService());
      const input = 'echo test';
      final response = await ConversationService.instance.sendMessage(input);
      expect(response, 'echo: $input');

      // Restore.
      ConversationService.setInstance(const LocalConversationService());
    });
  });

  group('ConversationException', () {
    test('message is preserved', () {
      const ex = ConversationException('Something failed');
      expect(ex.message, 'Something failed');
    });

    test('toString includes the message', () {
      const ex = ConversationException('oops');
      expect(ex.toString(), contains('oops'));
    });
  });
}

/// Minimal test double: echoes the message back.
class _EchoConversationService implements ConversationService {
  const _EchoConversationService();

  @override
  Future<String> sendMessage(String message) async => 'echo: $message';
}
