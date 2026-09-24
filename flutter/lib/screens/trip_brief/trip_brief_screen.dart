import 'package:flutter/material.dart';
import '../../app/theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// TripBriefScreen — voyage planning placeholder
// Based on the UI reference: shows trip metrics, route, forecast, pre-departure.
// Full implementation in Milestone 8 (backend API + GPS data).
// ─────────────────────────────────────────────────────────────────────────────

class TripBriefScreen extends StatelessWidget {
  final bool embedded;
  const TripBriefScreen({super.key, this.embedded = false});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: _buildAppBar(context),
      body: const _TripBriefBody(),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
        onPressed: () => Navigator.pop(context),
      ),
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 22,
            height: 22,
            child: Image.asset(
              'assets/images/samudra_logo.png',
              fit: BoxFit.contain,
              errorBuilder: (ctx, e, s) =>
                  const Icon(Icons.waves, color: SamudraColors.accentCyan, size: 18),
            ),
          ),
          const SizedBox(width: 8),
          Text('Samudra AI',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(fontSize: 17, fontWeight: FontWeight.w700)),
        ],
      ),
      centerTitle: true,
    );
  }
}

class _TripBriefBody extends StatelessWidget {
  const _TripBriefBody();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header ────────────────────────────────────────────────────
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Trip Brief',
                      style: Theme.of(context).textTheme.headlineLarge),
                  const SizedBox(height: 2),
                  Text('ID: EX-0000  •  Generated: --:--Z',
                      style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
              // Save for offline toggle placeholder
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: SamudraColors.backgroundCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: SamudraColors.borderSubtle),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.download_outlined,
                        size: 14, color: SamudraColors.accentCyan),
                    const SizedBox(width: 6),
                    Text('Save Offline',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: SamudraColors.textSecondary, fontSize: 12)),
                    const SizedBox(width: 6),
                    Container(
                      width: 28,
                      height: 16,
                      decoration: BoxDecoration(
                        color: SamudraColors.accentCyan.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: SamudraColors.accentCyan, width: 0.5),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ── Metrics row ───────────────────────────────────────────────
          Row(
            children: [
              Expanded(child: _MetricCard(label: 'Est. Time', value: '--:--', icon: Icons.schedule_outlined)),
              const SizedBox(width: 10),
              Expanded(child: _MetricCard(label: 'Distance', value: '-- nm', icon: Icons.straighten_outlined)),
              const SizedBox(width: 10),
              Expanded(child: _MetricCard(label: 'Est. Fuel', value: '-- L', icon: Icons.local_gas_station_outlined)),
            ],
          ),
          const SizedBox(height: 16),

          // ── Route map placeholder ──────────────────────────────────────
          Container(
            height: 160,
            decoration: BoxDecoration(
              color: const Color(0xFF071525),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: SamudraColors.borderSubtle),
            ),
            child: Stack(
              children: [
                Center(
                  child: Text(
                    'Route map available after\nGPS integration',
                    style: Theme.of(context).textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  ),
                ),
                Positioned(
                  top: 10,
                  left: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: SamudraColors.accentCyan.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: SamudraColors.accentCyan, width: 0.5),
                    ),
                    child: Row(
                      children: [
                        Container(width: 6, height: 6,
                            decoration: const BoxDecoration(
                                color: SamudraColors.accentCyan, shape: BoxShape.circle)),
                        const SizedBox(width: 5),
                        Text('ROUTE PLOTTED',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: SamudraColors.accentCyan, fontSize: 9, letterSpacing: 1)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── Environmental Forecast ─────────────────────────────────────
          _SectionHeader(icon: Icons.waves_outlined, label: 'Environmental Forecast'),
          const SizedBox(height: 10),
          Container(
            decoration: BoxDecoration(
              color: SamudraColors.backgroundCard,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: SamudraColors.borderSubtle),
            ),
            padding: const EdgeInsets.all(14),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: ['0800', '1100', '1400', '1630']
                  .map((t) => _ForecastSlot(time: t))
                  .toList(),
            ),
          ),
          const SizedBox(height: 16),

          // ── Pre-Departure checklist ────────────────────────────────────
          _SectionHeader(icon: Icons.checklist_outlined, label: 'Pre-Departure'),
          const SizedBox(height: 10),
          Container(
            decoration: BoxDecoration(
              color: SamudraColors.backgroundCard,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: SamudraColors.borderSubtle),
            ),
            child: Column(
              children: [
                _ChecklistItem(label: 'Comms check', sub: 'VHF Channels 16 & 72'),
                _ChecklistItem(label: 'Fuel level', sub: 'Main tanks — not verified'),
                _ChecklistItem(label: 'Life vests', sub: 'Count not verified'),
                _ChecklistItem(label: 'Nav Systems', sub: 'GPS sync pending', last: true),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Start Voyage CTA ──────────────────────────────────────────
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: null, // disabled until GPS + backend ready
              icon: const Icon(Icons.sailing_outlined, size: 18),
              label: const Text('Start Voyage'),
              style: ElevatedButton.styleFrom(
                backgroundColor: SamudraColors.accentCyan,
                foregroundColor: SamudraColors.backgroundDark,
                disabledBackgroundColor: SamudraColors.accentCyan.withValues(alpha: 0.4),
                disabledForegroundColor: SamudraColors.backgroundDark.withValues(alpha: 0.6),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _MetricCard({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 12, color: SamudraColors.accentCyan),
              const SizedBox(width: 4),
              Flexible(
                child: Text(label,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: SamudraColors.textMuted, fontSize: 10),
                    overflow: TextOverflow.ellipsis),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(value,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: SamudraColors.textPrimary,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                  )),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String label;
  const _SectionHeader({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: SamudraColors.accentCyan),
        const SizedBox(width: 8),
        Text(label, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontSize: 15)),
      ],
    );
  }
}

class _ForecastSlot extends StatelessWidget {
  final String time;
  const _ForecastSlot({required this.time});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(time,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: SamudraColors.textMuted, fontSize: 10)),
        const SizedBox(height: 6),
        Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
                color: SamudraColors.borderSubtle,
                shape: BoxShape.circle,
                border: Border.all(color: SamudraColors.textMuted, width: 0.5))),
        const SizedBox(height: 6),
        Text('--',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: SamudraColors.textSecondary)),
        Text('-- kn',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: SamudraColors.textMuted, fontSize: 10)),
      ],
    );
  }
}

class _ChecklistItem extends StatelessWidget {
  final String label;
  final String sub;
  final bool last;
  const _ChecklistItem({required this.label, required this.sub, this.last = false});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 18,
                height: 18,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: SamudraColors.borderSubtle, width: 1.5),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: Theme.of(context)
                            .textTheme
                            .bodyLarge
                            ?.copyWith(fontSize: 14, fontWeight: FontWeight.w500)),
                    Text(sub,
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: SamudraColors.textMuted)),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (!last)
          const Divider(height: 1, indent: 44, endIndent: 0, color: SamudraColors.borderSubtle),
      ],
    );
  }
}
