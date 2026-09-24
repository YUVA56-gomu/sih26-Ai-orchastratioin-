import 'package:flutter/material.dart';
import '../../app/theme.dart';
import 'weather_card_widget.dart';
import 'ocean_conditions_card_widget.dart';
import 'pfz_card_widget.dart';
import 'route_map_widget.dart';
import 'risk_summary_card_widget.dart';
import 'tide_card_widget.dart';

class ArtifactRenderer extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const ArtifactRenderer({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final rawType = (artifact['type'] ?? artifact['category'] ?? '').toString().toLowerCase();

    if (rawType == 'weather' || rawType.contains('weather')) {
      return WeatherCardWidget(artifact: artifact);
    }

    if (rawType == 'ocean' || rawType == 'marine' || rawType.contains('ocean') || rawType.contains('marine')) {
      return OceanConditionsCardWidget(artifact: artifact);
    }

    if (rawType == 'pfz' || rawType.contains('pfz') || rawType.contains('fish')) {
      return PFZCardWidget(artifact: artifact);
    }

    if (rawType == 'route' || rawType.contains('route') || rawType.contains('nav')) {
      return RouteMapWidget(artifact: artifact);
    }

    if (rawType == 'risk' || rawType.contains('risk') || rawType.contains('safety')) {
      return RiskSummaryCardWidget(artifact: artifact);
    }

    if (rawType == 'tide' || rawType.contains('tide')) {
      return TideCardWidget(artifact: artifact);
    }

    // Generic fallback card for any unrecognized artifact type
    final title = artifact['title'] as String? ?? 'Marine Artifact';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.insert_drive_file_outlined, size: 18, color: SamudraColors.accentCyan),
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
            ],
          ),
          const SizedBox(height: 8),
          Text(
            data.entries
                .where((e) => e.key != 'title' && e.key != 'type')
                .take(4)
                .map((e) => '${e.key}: ${e.value}')
                .join(' • '),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: SamudraColors.textSecondary,
                ),
          ),
        ],
      ),
    );
  }
}
