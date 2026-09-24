import 'package:flutter/material.dart';
import '../app/theme.dart';

class AgentThinkingCard extends StatefulWidget {
  final List<Map<String, dynamic>> agentSteps;
  final bool isThinking;
  final double? durationSeconds;

  const AgentThinkingCard({
    super.key,
    required this.agentSteps,
    this.isThinking = false,
    this.durationSeconds,
  });

  @override
  State<AgentThinkingCard> createState() => _AgentThinkingCardState();
}

class _AgentThinkingCardState extends State<AgentThinkingCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    if (widget.agentSteps.isEmpty && !widget.isThinking) {
      return const SizedBox.shrink();
    }

    final uniqueSteps = <Map<String, dynamic>>[];
    final seenKeys = <String>{};
    for (final s in widget.agentSteps) {
      final key = (s['id'] ?? s['node'] ?? s['label'] ?? '').toString();
      if (key.isNotEmpty && !seenKeys.contains(key)) {
        seenKeys.add(key);
        uniqueSteps.add(s);
      } else if (key.isEmpty) {
        uniqueSteps.add(s);
      }
    }

    final durationText = widget.durationSeconds != null
        ? '✦ Analyzed in ${widget.durationSeconds!.toStringAsFixed(1)}s'
        : (uniqueSteps.isNotEmpty ? '✦ Analyzed (${uniqueSteps.length} step${uniqueSteps.length == 1 ? '' : 's'})' : '✦ Analysis complete');

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: SamudraColors.borderSubtle.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Compact header bar
          InkWell(
            onTap: () {
              setState(() => _isExpanded = !_isExpanded);
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  Text(
                    '✦',
                    style: TextStyle(
                      color: SamudraColors.accentCyan,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    widget.isThinking
                        ? 'Samudra is analyzing...'
                        : durationText,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.textSecondary,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                  ),
                  const Spacer(),
                  Icon(
                    _isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    size: 16,
                    color: SamudraColors.textMuted,
                  ),
                ],
              ),
            ),
          ),

          // Expanded agent execution breakdown
          if (_isExpanded && uniqueSteps.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(height: 12, color: SamudraColors.borderSubtle),
                  Text(
                    'AGENT EXECUTION TRACE',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.accentCyan,
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.1,
                        ),
                  ),
                  const SizedBox(height: 8),
                  ...uniqueSteps.map((step) => _AgentStepItem(step: step)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _AgentStepItem extends StatelessWidget {
  final Map<String, dynamic> step;

  const _AgentStepItem({required this.step});

  @override
  Widget build(BuildContext context) {
    final icon = (step['icon'] ?? step['emoji'] ?? '🤖').toString();
    final label = (step['label'] ?? step['node'] ?? 'Agent').toString();
    final thought = (step['thought'] ?? step['message'] ?? 'Completed step').toString();

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(icon, style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      label,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: SamudraColors.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                    ),
                    const SizedBox(width: 6),
                    const Text('✓', style: TextStyle(color: SamudraColors.statusSafe, fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                ),
                if (thought.isNotEmpty)
                  Text(
                    thought,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.textMuted,
                          fontSize: 10,
                        ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
