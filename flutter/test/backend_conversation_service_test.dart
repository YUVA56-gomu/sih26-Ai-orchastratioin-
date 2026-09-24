import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:samudra_ai/config/backend_config.dart';
import 'package:samudra_ai/models/conversation/conversation_message.dart';
import 'package:samudra_ai/services/conversation/backend_conversation_service.dart';
import 'package:samudra_ai/services/conversation/conversation_service.dart';

void main() {
  group('BackendConfig', () {
    test('has valid backend URL configured', () {
      expect(BackendConfig.baseUrl, isNotEmpty);
      expect(BackendConfig.isConfigured, isTrue);
    });
  });

  group('BackendConversationService — not configured', () {
    test('throws a safe ConversationException when base URL is empty', () async {
      final service = BackendConversationService(baseUrl: '');

      expect(
        () => service.sendMessage('Hello'),
        throwsA(
          isA<ConversationException>().having(
            (e) => e.message.toLowerCase(),
            'message',
            contains('not configured'),
          ),
        ),
      );
    });
  });

  group('BackendConversationService — configured (mock HTTP)', () {
    test('sends message to /chat with a JSON body and returns summary/response', () async {
      final captured = <String, dynamic>{};
      late http.Request capturedRequest;

      final mock = MockClient((request) async {
        capturedRequest = request;
        captured['body'] = jsonDecode(request.body);
        return http.Response(
          jsonEncode({
            'request_id': 'orca_abc123',
            'conversation_id': 'conv_xyz789',
            'response': 'The sea is calm with 1.2 m waves. Wind is light from the NE.',
            'answer': {
              'status': 'safe',
              'summary': 'The sea is calm with 1.2 m waves.',
              'observations': ['Wind is light from the NE.'],
              'recommendations': ['Best window is early morning.'],
            },
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final service = BackendConversationService(
        client: mock,
        baseUrl: 'http://192.168.1.50:8000',
        locationProvider: () async => null,
      );

      final reply = await service.sendMessage('Where should I fish today?');

      expect(capturedRequest.method, 'POST');
      expect(capturedRequest.url.toString(), contains('/chat'));
      expect(reply, contains('sea is calm'));
    });

    test('sends the device GPS location in the request body when available', () async {
      final captured = <Map<String, dynamic>>[];

      final mock = MockClient((request) async {
        captured.add(jsonDecode(request.body) as Map<String, dynamic>);
        return http.Response(
          jsonEncode({
            'conversation_id': 'conv_loc',
            'response': 'Conditions here.',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final service = BackendConversationService(
        client: mock,
        baseUrl: 'http://backend:8000',
        locationProvider: () async => {'latitude': 9.9312, 'longitude': 76.2673},
      );

      await service.sendMessage('What are the conditions here?');

      expect(captured.single['latitude'], 9.9312);
      expect(captured.single['longitude'], 76.2673);
    });

    test('reuses conversation_id from a prior response on the next call', () async {
      final sentBodies = <Map<String, dynamic>>[];
      final mock = MockClient((request) async {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        sentBodies.add(body);
        return http.Response(
          jsonEncode({
            'conversation_id': 'conv_keep_me',
            'response': 'A-ok.',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final service = BackendConversationService(
        client: mock,
        baseUrl: 'http://backend:8000',
        locationProvider: () async => null,
      );

      await service.sendMessage('first');
      await service.sendMessage('second');

      expect(sentBodies.first.containsKey('conversation_id'), isFalse);
      expect(sentBodies[1]['conversation_id'], 'conv_keep_me');
    });

    test('throws a friendly error on HTTP 500', () async {
      final mock = MockClient((_) async => http.Response('oops', 500));

      final service = BackendConversationService(
        client: mock,
        baseUrl: 'http://backend:8000',
        locationProvider: () async => null,
      );

      expect(
        () => service.sendMessage('hello'),
        throwsA(
          isA<ConversationException>().having(
            (e) => e.message,
            'message',
            contains('500'),
          ),
        ),
      );
    });
  });

  group('BackendConversationService — persistent history', () {
    test('loadHistory picks the most recent conversation and maps messages', () async {
      final paths = <String>[];
      final mock = MockClient((request) async {
        paths.add(request.url.path);
        if (request.url.path == '/conversations' || request.url.path == '/api/conversations') {
          return http.Response(
            jsonEncode([
              {
                'conversation_id': 'conv_latest',
                'message_count': 2,
                'last_message': 'hi',
                'updated_at': '2026-01-01T00:00:00Z',
              },
            ]),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/conversations/conv_latest' ||
            request.url.path == '/api/conversations/conv_latest/messages') {
          return http.Response(
            jsonEncode({
              'conversation_id': 'conv_latest',
              'messages': [
                {
                  'role': 'user',
                  'content': 'hi',
                  'created_at': '2026-01-01T00:00:00Z',
                },
                {
                  'role': 'assistant',
                  'content': 'Hello!',
                  'created_at': '2026-01-01T00:00:01Z',
                },
              ],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('not found', 404);
      });

      final service = BackendConversationService(
        client: mock,
        baseUrl: 'http://backend:8000',
        locationProvider: () async => null,
      );

      final history = await service.loadHistory();

      expect(history.length, 2);
      expect(history.first.role, MessageRole.user);
      expect(history.first.text, 'hi');
      expect(history.last.role, MessageRole.assistant);
      expect(history.last.text, 'Hello!');
    });
  });
}
