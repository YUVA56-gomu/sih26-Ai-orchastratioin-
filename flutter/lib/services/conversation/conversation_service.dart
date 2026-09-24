// ─────────────────────────────────────────────────────────────────────────────
// ConversationService — abstraction layer between the Assistant UI and the
// conversation backend.
//
// The concrete implementation is injected at app startup (see main.dart).
// This means AssistantScreen never imports a specific backend implementation
// and can remain unchanged when the backend changes.
//
// CURRENT IMPLEMENTATIONS
//   LocalConversationService        — offline placeholder (no network).
//   BackendConversationService      — talks to the real teammate FastAPI
//                                     backend (8-backend → finalll/) over HTTP.
//
// HOW TO SWAP IMPLEMENTATIONS
//   In main.dart, change the value passed to ConversationService.setInstance().
//   No other file needs editing.
// ─────────────────────────────────────────────────────────────────────────────

import '../../models/conversation/conversation_message.dart';
import '../../models/conversation/conversation_summary.dart';

/// Contract that every conversation backend must satisfy.
///
/// A single method: receive a plain-text [message] from the user and return
/// a plain-text [String] response.
///
/// The implementation decides how to produce the response — local logic,
/// a remote API, a language model, etc. The [AssistantScreen] only sees
/// this interface.
abstract class ConversationService {
  // ── Global instance ─────────────────────────────────────────────────────────

  static ConversationService _instance = LocalConversationService();

  /// The active [ConversationService] used throughout the app.
  static ConversationService get instance => _instance;

  /// Replace the active implementation. Call this in `main()` before
  /// `runApp()`.
  ///
  /// Example (once Google ADK is ready):
  /// ```dart
  /// ConversationService.setInstance(GoogleAdkConversationService());
  /// ```
  static void setInstance(ConversationService service) {
    _instance = service;
  }

  // ── Interface ───────────────────────────────────────────────────────────────

  /// Send a [message] from the user and return the assistant's reply.
  ///
  /// Throws a [ConversationException] if the underlying transport or service
  /// fails in a way that should be shown to the user.
  Future<String> sendMessage(String message);
}

// ─────────────────────────────────────────────────────────────────────────────
// ConversationHistoryProvider — optional persistent-history capability
// ─────────────────────────────────────────────────────────────────────────────

/// Optional capability implemented by backends that support persistent
/// conversation history. Declared separately from [ConversationService] so that
/// non-persisting implementations (e.g. the local placeholder) are untouched.
///
/// The Assistant UI checks `ConversationService.instance is
/// ConversationHistoryProvider` before loading history — if the active backend
/// cannot persist, the screen simply shows the local greeting.
abstract class ConversationHistoryProvider {
  /// Load the history for the current conversation (or the most recent one).
  ///
  /// Returns an empty list when nothing is persisted, so callers fall back to a
  /// local greeting.
  Future<List<ConversationMessage>> loadHistory();

  /// List all saved conversations, most recent first.
  Future<List<ConversationSummary>> loadConversations();
}

// ─────────────────────────────────────────────────────────────────────────────
// ConversationException
// ─────────────────────────────────────────────────────────────────────────────

/// Thrown by [ConversationService.sendMessage] when something goes wrong.
///
/// [message] is always safe to show directly in the UI.
class ConversationException implements Exception {
  const ConversationException(this.message);
  final String message;

  @override
  String toString() => 'ConversationException: $message';
}

// ─────────────────────────────────────────────────────────────────────────────
// LocalConversationService — offline placeholder
// ─────────────────────────────────────────────────────────────────────────────

/// Offline placeholder implementation used when no backend URL is configured.
///
/// Returns a clearly marked local response — it does NOT simulate or pretend
/// to be real marine intelligence.
///
/// main.dart swaps this for `BackendConversationService` once a
/// `--dart-define=BACKEND_BASE_URL=...` is provided.
class LocalConversationService implements ConversationService {
  const LocalConversationService();

  @override
  Future<String> sendMessage(String message) async {
    // Simulate a short processing delay so the UI loading state is visible.
    await Future.delayed(const Duration(milliseconds: 600));

    return 'This is a local placeholder response. '
        'The Samudra AI conversation agent is being developed '
        'and will be connected in a future update. '
        'Your message was: "$message"';
  }
}
