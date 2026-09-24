import 'package:flutter/material.dart';
import '../app/theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SafetyStatusCard — compact marine status indicator on the home screen
// Status will be driven by real data in Milestone 5 (background monitoring).
// ─────────────────────────────────────────────────────────────────────────────

enum MarineStatus { safe, warning, danger }

class SafetyStatusCard extends StatelessWidget {
  final MarineStatus status;
  final String statusText;

  const SafetyStatusCard({
    super.key,
    this.status = MarineStatus.safe,
    this.statusText = 'Safe for Marine Activities',
  });

  Color get _statusColor {
    switch (status) {
      case MarineStatus.safe:
        return SamudraColors.statusSafe;
      case MarineStatus.warning:
        return SamudraColors.statusWarning;
      case MarineStatus.danger:
        return SamudraColors.statusDanger;
    }
  }

  IconData get _statusIcon {
    switch (status) {
      case MarineStatus.safe:
        return Icons.check_circle_outline;
      case MarineStatus.warning:
        return Icons.warning_amber_outlined;
      case MarineStatus.danger:
        return Icons.error_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          // Pulsing status dot
          _PulseDot(color: _statusColor),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Current Status',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.textMuted,
                        fontSize: 11,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  statusText,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontSize: 14,
                        color: SamudraColors.textPrimary,
                        fontWeight: FontWeight.w500,
                      ),
                ),
              ],
            ),
          ),
          Icon(_statusIcon, size: 20, color: _statusColor),
        ],
      ),
    );
  }
}

/// Small animated pulsing dot for the status indicator
class _PulseDot extends StatefulWidget {
  final Color color;
  const _PulseDot({required this.color});

  @override
  State<_PulseDot> createState() => _PulseDotState();
}

class _PulseDotState extends State<_PulseDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _scale = Tween<double>(begin: 0.85, end: 1.15).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scale,
      child: Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: widget.color,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: widget.color.withValues(alpha: 0.5),
              blurRadius: 6,
              spreadRadius: 1,
            ),
          ],
        ),
      ),
    );
  }
}
