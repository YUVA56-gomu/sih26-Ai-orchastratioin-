import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../config/backend_config.dart';
import '../../models/conversation/conversation_message.dart';
import '../../models/conversation/conversation_summary.dart';
import '../location_service.dart';
import 'conversation_service.dart';

typedef LocationProvider = Future<Map<String, double>?> Function();

Future<Map<String, double>?> _deviceLocation() async {
  try {
    final data = await LocationService.instance
        .getCurrentLocation()
        .timeout(const Duration(seconds: 5));
    if (data == null) return null;
    return {'latitude': data.latitude, 'longitude': data.longitude};
  } catch (_) {
    return null;
  }
}

class BackendConversationService
    implements ConversationService, ConversationHistoryProvider {
  BackendConversationService({
    http.Client? client,
    String? baseUrl,
    LocationProvider? locationProvider,
  })  : _client = client ?? http.Client(),
        _baseUrl = (baseUrl != null) ? baseUrl : BackendConfig.baseUrl,
        _locationProvider = locationProvider ?? _deviceLocation;

  final http.Client _client;
  final String _baseUrl;
  final LocationProvider _locationProvider;

  static const Duration _timeout = Duration(seconds: 120);
  String? _conversationId;

  String? get currentConversationId => _conversationId;

  void newConversation() {
    _conversationId = null;
  }

  void setConversationId(String id) {
    _conversationId = id;
  }

  @override
  Future<String> sendMessage(String message) async {
    final result = await sendStructuredMessage(message);
    return result.text;
  }

  /// Main structured message call — returns full [ConversationMessage] carrying
  /// natural text, artifacts, agent execution steps, risk level, and risk score.
  Future<ConversationMessage> sendStructuredMessage(String message) async {
    if (_baseUrl.trim().isEmpty) {
      throw const ConversationException(
        'The conversational backend is not configured yet. '
        'Please try again later.',
      );
    }

    // Try primary `/chat` endpoint, fallback to `/api/chat` for legacy mock tests
    Uri uri = Uri.parse('${_baseUrl.trim()}/chat');
    final location = await _locationProvider();

    final bodyMap = <String, dynamic>{
      'message': message,
      if (_conversationId != null) 'conversation_id': _conversationId,
      if (location != null) ...{
        'latitude': location['latitude'],
        'longitude': location['longitude'],
        'location': location,
      },
    };

    http.Response response;
    try {
      response = await _client
          .post(
            uri,
            headers: const {'Content-Type': 'application/json'},
            body: jsonEncode(bodyMap),
          )
          .timeout(_timeout);

      if (response.statusCode == 404) {
        // Fallback to /api/chat if /chat returns 404
        uri = Uri.parse('${_baseUrl.trim()}/api/chat');
        response = await _client
            .post(
              uri,
              headers: const {'Content-Type': 'application/json'},
              body: jsonEncode(bodyMap),
            )
            .timeout(_timeout);
      }
    } catch (_) {
      throw const ConversationException(
        'I could not connect to Samudra AI right now. '
        'Please try again in a moment.',
      );
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ConversationException(
        'Samudra AI is having trouble right now. '
        'Please try again in a moment. (HTTP ${response.statusCode})',
      );
    }

    try {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (data is! Map<String, dynamic>) {
        throw const ConversationException(
          'Samudra AI sent an unexpected response. Please try again.',
        );
      }

      final conversationId = data['conversation_id'];
      if (conversationId is String && conversationId.isNotEmpty) {
        _conversationId = conversationId;
      }

      // Extract natural language response text
      String text = '';
      if (data['response'] is String && (data['response'] as String).trim().isNotEmpty) {
        text = (data['response'] as String).trim();
      } else if (data['answer'] != null) {
        text = _composeAnswer(data['answer']);
      }

      if (text.trim().isEmpty) {
        throw const ConversationException(
          'Samudra AI did not return a readable answer. Please try again.',
        );
      }

      // Extract artifacts list
      final rawArtifacts = data['artifacts'];
      List<Map<String, dynamic>>? artifacts;
      if (rawArtifacts is List) {
        artifacts = rawArtifacts
            .whereType<Map<String, dynamic>>()
            .toList();
      }

      // Extract agent execution steps (node trace)
      final rawTrace = data['node_trace'];
      List<Map<String, dynamic>>? agentSteps;
      if (rawTrace is List) {
        agentSteps = rawTrace
            .map((item) {
              if (item is Map<String, dynamic>) return item;
              if (item is Map) return Map<String, dynamic>.from(item);
              if (item is String && item.isNotEmpty) {
                return {
                  'node': item,
                  'label': item.replaceAll('_', ' ').toUpperCase(),
                  'thought': 'Executed step: $item',
                  'icon': '🤖',
                };
              }
              return null;
            })
            .whereType<Map<String, dynamic>>()
            .toList();
      }

      final riskLevel = data['risk_level'] as String?;
      final riskScore = (data['risk_score'] as num?)?.toInt();

      return ConversationMessage.assistant(
        text,
        artifacts: artifacts,
        agentSteps: agentSteps,
        riskLevel: riskLevel,
        riskScore: riskScore,
      );
    } on ConversationException {
      rethrow;
    } catch (_) {
      throw const ConversationException(
        'Samudra AI sent an unexpected response. Please try again.',
      );
    }
  }

  // ── History & Conversations ────────────────────────────────────────────────

  @override
  Future<List<ConversationMessage>> loadHistory() async {
    if (_baseUrl.trim().isEmpty) return const [];

    if (_conversationId == null) {
      try {
        _conversationId = await _mostRecentConversationId();
      } catch (_) {
        return const [];
      }
    }
    if (_conversationId == null) return const [];

    return loadHistoryFor(_conversationId!);
  }

  /// Load complete message history for a specific conversation ID.
  Future<List<ConversationMessage>> loadHistoryFor(String conversationId) async {
    if (_baseUrl.trim().isEmpty) return const [];

    _conversationId = conversationId;

    // Try GET /conversations/{id}
    Uri uri = Uri.parse('${_baseUrl.trim()}/conversations/$conversationId');
    http.Response response;
    try {
      response = await _client.get(uri).timeout(_timeout);
      if (response.statusCode == 404) {
        uri = Uri.parse('${_baseUrl.trim()}/api/conversations/$conversationId/messages');
        response = await _client.get(uri).timeout(_timeout);
      }
    } catch (_) {
      throw const ConversationException('I could not load your conversation history.');
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      return const [];
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data is! Map<String, dynamic>) return const [];

    final messages = data['messages'];
    if (messages is! List) return const [];

    final result = <ConversationMessage>[];
    for (final m in messages.whereType<Map<String, dynamic>>()) {
      final role = m['role'] == 'assistant' ? MessageRole.assistant : MessageRole.user;
      final text = (m['content'] as String?) ?? (m['text'] as String?) ?? '';
      if (text.trim().isEmpty) continue;

      final rawArts = m['artifacts'];
      final artifacts = rawArts is List ? rawArts.whereType<Map<String, dynamic>>().toList() : null;

      final rawSteps = m['agentSteps'] ?? m['node_trace'];
      List<Map<String, dynamic>>? steps;
      if (rawSteps is List) {
        steps = rawSteps
            .map((item) {
              if (item is Map<String, dynamic>) return item;
              if (item is Map) return Map<String, dynamic>.from(item);
              if (item is String && item.isNotEmpty) {
                return {
                  'node': item,
                  'label': item.replaceAll('_', ' ').toUpperCase(),
                  'thought': 'Executed step: $item',
                  'icon': '🤖',
                };
              }
              return null;
            })
            .whereType<Map<String, dynamic>>()
            .toList();
      }

      result.add(ConversationMessage(
        role: role,
        text: text,
        timestamp: DateTime.tryParse((m['created_at'] as String?) ?? '') ?? DateTime.now(),
        artifacts: artifacts,
        agentSteps: steps,
        riskLevel: m['risk_level'] as String?,
        riskScore: (m['risk_score'] as num?)?.toInt(),
      ));
    }

    return result;
  }

  @override
  Future<List<ConversationSummary>> loadConversations() async {
    if (_baseUrl.trim().isEmpty) return const [];

    Uri uri = Uri.parse('${_baseUrl.trim()}/conversations');
    http.Response response;
    try {
      response = await _client.get(uri).timeout(_timeout);
      if (response.statusCode == 404) {
        uri = Uri.parse('${_baseUrl.trim()}/api/conversations');
        response = await _client.get(uri).timeout(_timeout);
      }
    } catch (_) {
      throw const ConversationException('I could not load your conversations.');
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      return const [];
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    final list = data is List
        ? data
        : (data is Map<String, dynamic> ? (data['conversations'] as List?) : null);

    if (list is! List) return const [];

    return list
        .whereType<Map<String, dynamic>>()
        .map(ConversationSummary.fromJson)
        .toList();
  }

  Future<String?> _mostRecentConversationId() async {
    final list = await loadConversations();
    if (list.isEmpty) return null;
    return list.first.conversationId;
  }

  String _composeAnswer(Object? answer) {
    if (answer is! Map<String, dynamic>) {
      throw const ConversationException(
        'Samudra AI sent an unexpected response. Please try again.',
      );
    }

    final summary = answer['summary'];
    final observations = answer['observations'];
    final recommendations = answer['recommendations'];

    final buffer = StringBuffer();
    if (summary is String && summary.trim().isNotEmpty) {
      buffer.write(summary.trim());
    }

    void appendList(String heading, Object? value) {
      if (value is List && value.isNotEmpty) {
        final items = value
            .whereType<String>()
            .map((e) => e.trim())
            .where((e) => e.isNotEmpty)
            .toList();
        if (items.isEmpty) return;
        if (buffer.isNotEmpty) buffer.write('\n\n');
        buffer.writeln(heading);
        for (final item in items) {
          buffer.writeln('• $item');
        }
      }
    }

    appendList('Observations', observations);
    appendList('Recommendations', recommendations);

    final text = buffer.toString().trim();
    if (text.isEmpty) {
      throw const ConversationException(
        'Samudra AI did not return a readable answer. Please try again.',
      );
    }
    return text;
  }
}
