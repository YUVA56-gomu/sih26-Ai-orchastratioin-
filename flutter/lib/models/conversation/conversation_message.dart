// ─────────────────────────────────────────────────────────────────────────────
// ConversationMessage — a single turn in the conversation.
//
// Generic and completely independent of the backend. The Assistant UI renders
// a list of these; the ConversationService only ever produces/consumes plain
// text responses, so this model carries no HTTP / auth / JSON knowledge.
// ─────────────────────────────────────────────────────────────────────────────

/// Who produced a [ConversationMessage].
enum MessageRole {
  /// The human user.
  user,

  /// The conversational assistant / backend.
  assistant,
}

/// One message in the conversation.
class ConversationMessage {
  const ConversationMessage({
    required this.role,
    required this.text,
    required this.timestamp,
    this.id,
    this.artifacts,
    this.agentSteps,
    this.riskLevel,
    this.riskScore,
  });

  /// A message typed/sent by the user.
  factory ConversationMessage.user(String text, {String? id}) => ConversationMessage(
        id: id ?? 'user_${DateTime.now().millisecondsSinceEpoch}',
        role: MessageRole.user,
        text: text,
        timestamp: DateTime.now(),
      );

  /// A reply produced by the assistant.
  factory ConversationMessage.assistant(
    String text, {
    String? id,
    List<Map<String, dynamic>>? artifacts,
    List<Map<String, dynamic>>? agentSteps,
    String? riskLevel,
    int? riskScore,
  }) =>
      ConversationMessage(
        id: id ?? 'assistant_${DateTime.now().millisecondsSinceEpoch}',
        role: MessageRole.assistant,
        text: text,
        timestamp: DateTime.now(),
        artifacts: artifacts,
        agentSteps: agentSteps,
        riskLevel: riskLevel,
        riskScore: riskScore,
      );

  final String? id;
  final MessageRole role;
  final String text;
  final DateTime timestamp;
  final List<Map<String, dynamic>>? artifacts;
  final List<Map<String, dynamic>>? agentSteps;
  final String? riskLevel;
  final int? riskScore;
}
