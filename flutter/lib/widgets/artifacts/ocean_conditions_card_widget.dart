import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../utils/map_navigation.dart';

class OceanConditionsCardWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const OceanConditionsCardWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Ocean Conditions';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final sst = data['sst'] ?? data['sea_surface_temperature'] ?? data['water_temp'];
    final sstUnit = data['sst_unit'] ?? '°C';
    final current = data['current_speed'] ?? data['current']?['speed'] ?? data['currents'];
    final currentUnit = data['current_unit'] ?? 'm/s';
    final salinity = data['salinity'];
    final wave = data['wave_height'] ?? data['wave'];
    final seaState = data['sea_state'] ?? data['sea_condition'] ?? 'Moderate';

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.accentBlue.withValues(alpha: 0.35)),
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
              const Icon(Icons.waves, size: 18, color: SamudraColors.accentBlue),
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
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: SamudraColors.accentBlue.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '$seaState',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.accentBlue,
                        fontWeight: FontWeight.w600,
                        fontSize: 11,
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              if (sst != null)
                _MetricTile(
                  icon: Icons.water,
                  label: 'Sea Temp (SST)',
                  value: '$sst $sstUnit',
                ),
              if (current != null)
                _MetricTile(
                  icon: Icons.speed,
                  label: 'Current Speed',
                  value: '$current $currentUnit',
                ),
              if (wave != null)
                _MetricTile(
                  icon: Icons.height,
                  label: 'Wave Height',
                  value: '$wave m',
                ),
              if (salinity != null)
                _MetricTile(
                  icon: Icons.science_outlined,
                  label: 'Salinity',
                  value: '$salinity PSU',
                ),
            ],
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerRight,
            child: InkWell(
              onTap: () => openMapArtifact(context, artifact),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'View on Map',
                      style: TextStyle(
                        color: SamudraColors.accentCyan,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(Icons.arrow_forward_ios, size: 10, color: SamudraColors.accentCyan),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _MetricTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, size: 16, color: SamudraColors.textSecondary),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: SamudraColors.textPrimary,
                fontWeight: FontWeight.w700,
                fontSize: 13,
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
