import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../utils/map_navigation.dart';

class RiskSummaryCardWidget extends StatelessWidget {
  final Map<String, dynamic> artifact;

  const RiskSummaryCardWidget({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    final title = artifact['title'] as String? ?? 'Marine Risk Assessment';
    final data = (artifact['data'] as Map<String, dynamic>?) ?? artifact;

    final riskLevel = (data['risk_level'] ?? data['level'] ?? 'LOW').toString().toUpperCase();
    final riskScore = (data['risk_score'] ?? data['score'] ?? 15) as num;

    final factors = (data['risk_factors'] as List?)?.cast<String>() ??
        (data['factors'] as List?)?.cast<String>() ??
        [];

    final advice = (data['recommendations'] as List?)?.cast<String>() ??
        (data['advice'] as List?)?.cast<String>() ??
        [];

    final Color badgeColor;
    switch (riskLevel) {
      case 'CRITICAL':
      case 'HIGH':
        badgeColor = SamudraColors.statusDanger;
        break;
      case 'MODERATE':
      case 'MEDIUM':
        badgeColor = SamudraColors.statusWarning;
        break;
      case 'LOW':
      default:
        badgeColor = SamudraColors.statusSafe;
        break;
    }

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: badgeColor.withValues(alpha: 0.4)),
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
              Icon(Icons.shield_outlined, size: 18, color: badgeColor),
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
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: badgeColor.withValues(alpha: 0.5)),
                ),
                child: Text(
                  '$riskLevel ($riskScore/100)',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: badgeColor,
                        fontWeight: FontWeight.w700,
                        fontSize: 11,
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Risk score progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (riskScore / 100).clamp(0.0, 1.0),
              backgroundColor: SamudraColors.borderSubtle,
              valueColor: AlwaysStoppedAnimation<Color>(badgeColor),
              minHeight: 6,
            ),
          ),

          if (factors.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(
              'Risk Factors:',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.textMuted,
                    fontWeight: FontWeight.w600,
                    fontSize: 11,
                  ),
            ),
            const SizedBox(height: 4),
            ...factors.map(
              (f) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('• ', style: TextStyle(color: badgeColor, fontSize: 12)),
                    Expanded(
                      child: Text(
                        f,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.textSecondary,
                              fontSize: 11,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],

          if (advice.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Safety Recommendations:',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.textMuted,
                    fontWeight: FontWeight.w600,
                    fontSize: 11,
                  ),
            ),
            const SizedBox(height: 4),
            ...advice.map(
              (a) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('✓ ', style: TextStyle(color: SamudraColors.accentCyan, fontSize: 12)),
                    Expanded(
                      child: Text(
                        a,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.textPrimary,
                              fontSize: 11,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
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
