import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SAMUDRA AI Design System
// All colours, text styles, and component decorations live here.
// Screens and widgets must import this file instead of hardcoding values.
// ─────────────────────────────────────────────────────────────────────────────

class SamudraColors {
  SamudraColors._();

  // Backgrounds
  static const Color backgroundDark = Color(0xFF0A0E1A); // near-black navy
  static const Color backgroundCard = Color(0xFF111827); // dark blue card
  static const Color backgroundElevated = Color(0xFF1A2035); // slightly lighter card
  static const Color backgroundDrawer = Color(0xFF0D1220); // sidebar bg

  // Borders
  static const Color borderSubtle = Color(0xFF1E2D45); // thin card border
  static const Color borderFocus = Color(0xFF2A4A7A); // focused input border

  // Primary accent — cyan/teal
  static const Color accentCyan = Color(0xFF00C6FF);
  static const Color accentCyanDim = Color(0xFF0A8FB5);
  static const Color accentCyanGlow = Color(0x2000C6FF); // for subtle glow effects

  // Secondary accent — blue
  static const Color accentBlue = Color(0xFF3B82F6);
  static const Color accentBlueDim = Color(0xFF1D4ED8);

  // Purple accent (restrained)
  static const Color accentPurple = Color(0xFF7C3AED);
  static const Color accentPurpleDim = Color(0xFF4C1D95);

  // Status colours
  static const Color statusSafe = Color(0xFF10B981);   // green
  static const Color statusWarning = Color(0xFFF59E0B); // amber
  static const Color statusDanger = Color(0xFFEF4444);  // red

  // Text
  static const Color textPrimary = Color(0xFFF0F4FF);
  static const Color textSecondary = Color(0xFF8BA0BC);
  static const Color textMuted = Color(0xFF4A6080);
  static const Color textAccent = accentCyan;
}

class SamudraTheme {
  SamudraTheme._();

  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: SamudraColors.backgroundDark,
      colorScheme: const ColorScheme.dark(
        primary: SamudraColors.accentCyan,
        secondary: SamudraColors.accentBlue,
        surface: SamudraColors.backgroundCard,
        onPrimary: SamudraColors.backgroundDark,
        onSecondary: SamudraColors.textPrimary,
        onSurface: SamudraColors.textPrimary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: SamudraColors.backgroundDark,
        foregroundColor: SamudraColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        systemOverlayStyle: SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: Brightness.light,
        ),
      ),
      drawerTheme: const DrawerThemeData(
        backgroundColor: SamudraColors.backgroundDrawer,
        elevation: 16,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: SamudraColors.backgroundCard,
        selectedItemColor: SamudraColors.accentCyan,
        unselectedItemColor: SamudraColors.textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      dividerTheme: const DividerThemeData(
        color: SamudraColors.borderSubtle,
        thickness: 0.5,
      ),
      textTheme: const TextTheme(
        // Headlines
        headlineLarge: TextStyle(
          color: SamudraColors.textPrimary,
          fontSize: 26,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.5,
        ),
        headlineMedium: TextStyle(
          color: SamudraColors.textPrimary,
          fontSize: 22,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.3,
        ),
        headlineSmall: TextStyle(
          color: SamudraColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
        // Body
        bodyLarge: TextStyle(
          color: SamudraColors.textPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w400,
        ),
        bodyMedium: TextStyle(
          color: SamudraColors.textSecondary,
          fontSize: 13,
          fontWeight: FontWeight.w400,
        ),
        bodySmall: TextStyle(
          color: SamudraColors.textMuted,
          fontSize: 11,
          fontWeight: FontWeight.w400,
        ),
        // Labels
        labelLarge: TextStyle(
          color: SamudraColors.textPrimary,
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
        labelMedium: TextStyle(
          color: SamudraColors.textSecondary,
          fontSize: 12,
          fontWeight: FontWeight.w400,
        ),
      ),
      iconTheme: const IconThemeData(
        color: SamudraColors.textSecondary,
        size: 22,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: SamudraColors.backgroundCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: SamudraColors.borderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: SamudraColors.borderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: SamudraColors.accentCyan, width: 1.5),
        ),
        hintStyle: const TextStyle(color: SamudraColors.textMuted, fontSize: 14),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }
}
