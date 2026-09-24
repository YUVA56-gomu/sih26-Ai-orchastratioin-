// ─────────────────────────────────────────────────────────────────────────────
// ConversationSummary — lightweight metadata for one conversation.
//
// Returned by ConversationService.loadConversations() for a list/sidebar view.
// Carries no message bodies; fetch individual messages via loadHistory().
// ─────────────────────────────────────────────────────────────────────────────

/// High-level info about a single conversation.
class ConversationSummary {
  const ConversationSummary({
    required this.conversationId,
    this.title,
    this.messageCount = 0,
    this.lastMessage,
    this.updatedAt,
  });

  /// Parse from the backend's `{"conversation_id", "message_count",
  /// "last_message", "updated_at"}` list item.
  factory ConversationSummary.fromJson(Map<String, dynamic> json) {
    return ConversationSummary(
      conversationId: (json['conversation_id'] as String?) ?? '',
      title: json['title'] as String?,
      messageCount: (json['message_count'] as num?)?.toInt() ?? 0,
      lastMessage: json['last_message'] as String?,
      updatedAt: DateTime.tryParse((json['updated_at'] as String?) ?? ''),
    );
  }

  final String conversationId;
  final String? title;
  final int messageCount;
  final String? lastMessage;
  final DateTime? updatedAt;
}
