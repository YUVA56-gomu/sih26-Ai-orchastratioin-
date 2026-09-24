import 'package:flutter/material.dart';
import '../../app/theme.dart';

class TideCardWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const TideCardWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Tide & Sea Level Forecast';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final highTide = data['high_tide'] ?? data['high_tide_time'] ?? '06:45 AM (1.8m)';
    final lowTide = data['low_tide'] ?? data['low_tide_time'] ?? '01:20 PM (0.4m)';
    final currentLevel = data['current_level'] ?? data['water_level'] ?? '1.2m';
    final coefficient = data['tidal_coefficient'] ?? data['coefficient'] ?? '75';

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.accentCyan.withValues(alpha: 0.3)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x22000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.water_outlined, size: 18, color: SamudraColors.accentCyan),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: SamudraColors.textPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                ),
              ),
              Text(
                'Coeff: $coefficient',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.textMuted,
                      fontSize: 11,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _TideTile(icon: Icons.arrow_upward, label: 'High Tide', value: '$highTide'),
              _TideTile(icon: Icons.arrow_downward, label: 'Low Tide', value: '$lowTide'),
              _TideTile(icon: Icons.height, label: 'Current Level', value: '$currentLevel'),
            ],
          ),
        ],
      ),
    );
  }
}

class _TideTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _TideTile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, size: 16, color: SamudraColors.accentCyan),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: SamudraColors.textPrimary,
                fontWeight: FontWeight.w700,
                fontSize: 12,
              ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SamudraColors.textMuted,
                fontSize: 10,
              ),
        ),
      ],
    );
  }
}
