import 'package:flutter/material.dart';
import '../app/theme.dart';
import '../screens/home/home_screen.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SamudraApp — root widget
// Sets up MaterialApp with the SAMUDRA AI dark theme and initial route.
// ─────────────────────────────────────────────────────────────────────────────

class SamudraApp extends StatelessWidget {
  const SamudraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Samudra AI',
      debugShowCheckedModeBanner: false,
      theme: SamudraTheme.dark,
      home: const HomeScreen(),
    );
  }
}
