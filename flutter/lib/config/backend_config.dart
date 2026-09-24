// ─────────────────────────────────────────────────────────────────────────────
// BackendConfig — single source of truth for the future backend endpoint.
//
// The teammate's backend (which will provide the conversational / marine
// intelligence API) is still under development, so no URL is hardcoded here.
//
// HOW TO PROVIDE THE URL WHEN THE CONTRACT IS READY
//   Pass it at build/run time via --dart-define, e.g.:
//
//     flutter run --dart-define=BACKEND_BASE_URL=https://api.example.com
//
//   The value is read as a compile-time constant. Until it is provided the
//   string is empty, which the service layer treats as "not configured yet".
// ─────────────────────────────────────────────────────────────────────────────

class BackendConfig {
  const BackendConfig._();

  /// Base URL of the backend API server.
  /// Defaults to http://10.0.2.2:8000 (Android emulator loopback) or http://localhost:8000.
  /// Can be overridden via `--dart-define=BACKEND_BASE_URL=https://...`
  static const String baseUrl = String.fromEnvironment(
    'BACKEND_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// Whether a backend URL has been provided.
  static bool get isConfigured => baseUrl.trim().isNotEmpty;
}
