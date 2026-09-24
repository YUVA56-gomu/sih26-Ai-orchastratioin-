import 'package:flutter/material.dart';
import '../app/theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SuggestionCard — tappable contextual suggestion chips
// UI placeholder; will pre-fill the AI input in Milestone 8.
// ─────────────────────────────────────────────────────────────────────────────

class SuggestionCard extends StatelessWidget {
  final String text;
  final VoidCallback? onTap;

  const SuggestionCard({
    super.key,
    required this.text,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: SamudraColors.backgroundCard,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: SamudraColors.borderSubtle),
        ),
        child: Text(
          text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: SamudraColors.textSecondary,
                fontSize: 13,
              ),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }
}
