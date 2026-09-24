import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/screens/home/home_screen.dart';
import 'package:samudra_ai/widgets/ask_samudra.dart';
import 'package:samudra_ai/services/conversation/conversation_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Navigation tests — Home → Assistant entry points and preserved tab flow.
//
// HomeScreen uses LocationService, which is transport-agnostic here but reads
// currentStatus synchronously; these tests only assert navigation/visibility,
// not any real GPS call. A stub ConversationService keeps messages offline.
//
// IndexedStack keeps every tab built, and several screens reuse the same icons
// (e.g. MarineMap has its own mic, a QuickActionCard also uses Icons.map), so
// finders are scoped to the widget that owns the control under test.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  setUp(() {
    ConversationService.setInstance(const LocalConversationService());
  });

  tearDown(() {
    ConversationService.setInstance(const LocalConversationService());
  });

  Future<void> pumpHome(WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: HomeScreen()));
    await tester.pump();
  }

  Finder inNavBar(Finder matching) => find.descendant(
        of: find.byType(BottomNavigationBar),
        matching: matching,
      );

  group('Microphone entry point', () {
    testWidgets('tapping microphone opens the voice dashboard', (tester) async {
      await pumpHome(tester);

      // The Home input bar's mic (scoped to AskSamudra — MarineMap tab is also
      // built and has its own mic icon).
      final mic = find.descendant(
        of: find.byType(AskSamudra),
        matching: find.byIcon(Icons.mic_outlined),
      );
      expect(mic, findsOneWidget);

      await tester.tap(mic);
      await tester.pump(); // start route transition
      await tester.pump(const Duration(milliseconds: 100));

      // The voice dashboard is now on top (its AppBar title is visible).
      expect(find.text('Samudra AI Voice'), findsOneWidget);
    });
  });

  group('Existing navigation', () {
    testWidgets('bottom navigation still moves between all tabs', (tester) async {
      await pumpHome(tester);

      // Home is the default tab.
      expect(find.text('Samudra AI'), findsWidgets);

      // → Assistant tab.
      await tester.tap(inNavBar(find.byIcon(Icons.chat_bubble_outline)));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.textContaining('How can I help you today?'), findsOneWidget);

      // → Map tab.
      await tester.tap(inNavBar(find.byIcon(Icons.map_outlined)));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // → Safety tab.
      await tester.tap(inNavBar(find.byIcon(Icons.shield_outlined)));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
    });
  });
}
