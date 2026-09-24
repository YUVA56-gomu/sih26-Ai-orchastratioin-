import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'app/app.dart';
import 'config/backend_config.dart';
import 'services/conversation/conversation_service.dart';
import 'services/conversation/backend_conversation_service.dart';
import 'services/location_service.dart';
import 'services/database_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Force portrait orientation on phones
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Transparent status bar so the app background shows through
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));

  // Milestone 3: initialise local SQLite database before UI renders.
  await DatabaseService.instance.initialize();

  // Milestone 2: start GPS stream once at app launch.
  LocationService.instance.startLocationStream();

  // Conversation backend: use the real teammate backend when a base URL is
  // provided via --dart-define=BACKEND_BASE_URL=...; otherwise fall back to the
  // offline local placeholder so the app still runs.
  ConversationService.setInstance(
    BackendConfig.isConfigured
        ? BackendConversationService()
        : const LocalConversationService(),
  );

  runApp(const SamudraApp());
}
