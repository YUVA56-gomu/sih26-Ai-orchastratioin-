import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../utils/map_navigation.dart';

class WeatherCardWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const WeatherCardWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Weather Forecast';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final temp = data['temperature'] ?? data['temp'] ?? data['temperature_2m'];
    final tempUnit = data['temp_unit'] ?? data['temperature_unit'] ?? '°C';
    final wind = data['wind_speed'] ?? data['wind'] ?? data['wind_speed_10m'];
    final windUnit = data['wind_unit'] ?? data['wind_speed_unit'] ?? 'km/h';
    final wave = data['wave_height'] ?? data['waves'];
    final waveUnit = data['wave_unit'] ?? 'm';
    final condition = data['condition'] ?? data['weather_condition'] ?? 'Clear';
    final humidity = data['humidity'];

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
              const Icon(Icons.wb_sunny_outlined, size: 18, color: SamudraColors.accentCyan),
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
                  color: SamudraColors.accentCyan.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '$condition',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.accentCyan,
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
              if (temp != null)
                _MetricTile(
                  icon: Icons.thermostat_outlined,
                  label: 'Temperature',
                  value: '$temp $tempUnit',
                ),
              if (wind != null)
                _MetricTile(
                  icon: Icons.air,
                  label: 'Wind Speed',
                  value: '$wind $windUnit',
                ),
              if (wave != null)
                _MetricTile(
                  icon: Icons.waves,
                  label: 'Wave Height',
                  value: '$wave $waveUnit',
                ),
              if (humidity != null)
                _MetricTile(
                  icon: Icons.water_drop_outlined,
                  label: 'Humidity',
                  value: '$humidity%',
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
