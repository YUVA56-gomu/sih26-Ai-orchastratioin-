import 'package:flutter/material.dart';
import '../../app/theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SafetyScreen — marine safety alerts placeholder
// Real alerts will be sourced from API + background monitoring in Milestone 5/8.
// `embedded` suppresses the AppBar when used in the bottom nav IndexedStack.
// ─────────────────────────────────────────────────────────────────────────────

class SafetyScreen extends StatelessWidget {
  final bool embedded;
  const SafetyScreen({super.key, this.embedded = false});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: embedded ? null : _buildAppBar(context),
      body: _SafetyBody(embedded: embedded),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
        onPressed: () => Navigator.pop(context),
      ),
      title: const _NavTitle(label: 'Safety Alerts'),
      centerTitle: false,
    );
  }
}

class _SafetyBody extends StatelessWidget {
  final bool embedded;
  const _SafetyBody({required this.embedded});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (embedded) ...[
            Text('Safety Alerts',
                style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 16),
          ],

          // ── Current Status Banner ────────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: SamudraColors.statusSafe.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                  color: SamudraColors.statusSafe.withValues(alpha: 0.4)),
            ),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: SamudraColors.statusSafe.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.shield_outlined,
                      color: SamudraColors.statusSafe, size: 22),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('All Clear',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                  color: SamudraColors.statusSafe,
                                  fontSize: 16)),
                      const SizedBox(height: 2),
                      Text('No active marine alerts in your region.',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                  color: SamudraColors.statusSafe
                                      .withValues(alpha: 0.8))),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Alert Categories ─────────────────────────────────────────
          Text('Alert Categories',
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: SamudraColors.textSecondary,
                    fontSize: 12,
                    letterSpacing: 0.5,
                  )),
          const SizedBox(height: 10),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 2.2,
            children: const [
              _AlertCategoryCard(
                  icon: Icons.waves_outlined,
                  label: 'Sea State',
                  count: '0',
                  color: SamudraColors.accentCyan),
              _AlertCategoryCard(
                  icon: Icons.storm_outlined,
                  label: 'Weather',
                  count: '0',
                  color: SamudraColors.accentBlue),
              _AlertCategoryCard(
                  icon: Icons.warning_amber_outlined,
                  label: 'IMBL Zone',
                  count: '0',
                  color: SamudraColors.statusWarning),
              _AlertCategoryCard(
                  icon: Icons.directions_boat_outlined,
                  label: 'Traffic',
                  count: '0',
                  color: SamudraColors.accentPurple),
            ],
          ),
          const SizedBox(height: 24),

          // ── Recent Alerts ────────────────────────────────────────────
          Text('Recent Alerts',
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: SamudraColors.textSecondary,
                    fontSize: 12,
                    letterSpacing: 0.5,
                  )),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 32),
            decoration: BoxDecoration(
              color: SamudraColors.backgroundCard,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: SamudraColors.borderSubtle),
            ),
            child: Column(
              children: [
                Icon(Icons.notifications_none_outlined,
                    size: 36,
                    color: SamudraColors.textMuted.withValues(alpha: 0.5)),
                const SizedBox(height: 12),
                Text('No recent alerts',
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: SamudraColors.textMuted)),
                const SizedBox(height: 4),
                Text('Live alerts available after backend integration.',
                    style: Theme.of(context).textTheme.bodySmall,
                    textAlign: TextAlign.center),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── IMBL Notice ───────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: SamudraColors.accentCyan.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(14),
              border:
                  Border.all(color: SamudraColors.accentCyan.withValues(alpha: 0.2)),
            ),
            child: Row(
              children: [
                const Icon(Icons.info_outline,
                    size: 18, color: SamudraColors.accentCyan),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'IMBL boundary monitoring will be active after GPS and geofencing modules are enabled (Milestone 4).',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.accentCyan.withValues(alpha: 0.85),
                        ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _AlertCategoryCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String count;
  final Color color;

  const _AlertCategoryCard({
    required this.icon,
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 16, color: color),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(label,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: SamudraColors.textMuted, fontSize: 10)),
                Text(count,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: SamudraColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w700)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _NavTitle extends StatelessWidget {
  final String label;
  const _NavTitle({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(label,
        style:
            Theme.of(context).textTheme.headlineSmall?.copyWith(fontSize: 17));
  }
}
