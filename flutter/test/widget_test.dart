import 'package:flutter_test/flutter_test.dart';
import 'package:samudra_ai/app/app.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Smoke test — the root widget tree must build without throwing.
//
// The previous version searched for 'SAMUDRA AI' (all-caps) which the app
// never renders. Updated to find the actual 'Samudra AI' mixed-case text
// present in HomeScreen's AppBar.
// ─────────────────────────────────────────────────────────────────────────────

void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SamudraApp());

    // HomeScreen AppBar renders 'Samudra AI' (mixed case).
    expect(find.text('Samudra AI'), findsWidgets);
  });
}
