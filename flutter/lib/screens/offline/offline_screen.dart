import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../services/database_service.dart';
import '../../models/marine_data.dart';
import '../../utils/demo_data.dart';

// ─────────────────────────────────────────────────────────────────────────────
// OfflineScreen — Milestone 3: SQLite offline data layer
//
// Shows database cache status and provides dev-test controls for
// inserting / clearing demo records.  The pack-download section
// remains as a placeholder for Milestone 8 (backend sync).
// ─────────────────────────────────────────────────────────────────────────────

class OfflineScreen extends StatelessWidget {
  const OfflineScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: _buildAppBar(context),
      body: const _OfflineBody(),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
        onPressed: () => Navigator.pop(context),
      ),
      title: Text('Offline Access',
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(fontSize: 17)),
      centerTitle: false,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _OfflineBody — stateful so it can refresh after DB operations
// ─────────────────────────────────────────────────────────────────────────────

class _OfflineBody extends StatefulWidget {
  const _OfflineBody();

  @override
  State<_OfflineBody> createState() => _OfflineBodyState();
}

class _OfflineBodyState extends State<_OfflineBody> {
  final _db = DatabaseService.instance;

  int _cachedCount = 0;
  DateTime? _lastUpdated;
  List<MarineData> _records = [];
  bool _loading = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  // ── DB helpers ────────────────────────────────────────────────────────────

  Future<void> _refresh() async {
    if (!mounted) return;
    setState(() => _loading = true);
    try {
      final count = await _db.count();
      final last = await _db.lastUpdated();
      final records = await _db.getAll();
      if (mounted) {
        setState(() {
          _cachedCount = count;
          _lastUpdated = last;
          _records = records;
          _loading = false;
          _statusMessage = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusMessage = 'Database error: $e';
        });
      }
    }
  }

  Future<void> _insertTestData() async {
    setState(() => _loading = true);
    try {
      await _db.insertAll(DemoData.sampleRecords());
      await _refresh();
      if (mounted) {
        setState(() => _statusMessage = 'Demo records inserted.');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusMessage = 'Insert failed: $e';
        });
      }
    }
  }

  Future<void> _clearTestData() async {
    setState(() => _loading = true);
    try {
      await _db.deleteByType('sea_surface_temp');
      await _db.deleteByType('chlorophyll');
      await _db.deleteByType('wave_height');
      await _db.deleteByType('wind_speed');
      await _db.deleteByType('salinity');
      await _refresh();
      if (mounted) {
        setState(() => _statusMessage = 'Demo records cleared.');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusMessage = 'Clear failed: $e';
        });
      }
    }
  }

  // ── IST display ───────────────────────────────────────────────────────────

  String _toIst(DateTime? utc) {
    if (utc == null) return '--';
    final ist = utc.toUtc().add(const Duration(hours: 5, minutes: 30));
    return '${ist.day.toString().padLeft(2, '0')}/'
        '${ist.month.toString().padLeft(2, '0')} '
        '${ist.hour.toString().padLeft(2, '0')}:'
        '${ist.minute.toString().padLeft(2, '0')} IST';
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Cache status card ────────────────────────────────────────
          _CacheStatusCard(
            cachedCount: _cachedCount,
            lastUpdated: _toIst(_lastUpdated),
            loading: _loading,
          ),
          const SizedBox(height: 16),

          // ── Dev test panel ───────────────────────────────────────────
          _DevTestPanel(
            statusMessage: _statusMessage,
            onInsert: _insertTestData,
            onClear: _clearTestData,
            onRefresh: _refresh,
            loading: _loading,
          ),
          const SizedBox(height: 20),

          // ── Cached records list ──────────────────────────────────────
          if (_records.isNotEmpty) ...[
            _SectionLabel(label: 'Cached Records'),
            const SizedBox(height: 10),
            ..._records
                .map((r) => _RecordCard(record: r, istFmt: _toIst)),
            const SizedBox(height: 20),
          ],

          if (_records.isEmpty && !_loading) ...[
            _EmptyState(),
            const SizedBox(height: 20),
          ],

          // ── Offline pack placeholders (future Milestone 8) ───────────
          _SectionLabel(label: 'Available Packs'),
          const SizedBox(height: 10),
          _PackCard(
            title: 'Kerala Coastal Zone',
            subtitle: 'Charts, zones, depth data',
            size: '~42 MB',
            icon: Icons.map_outlined,
            color: SamudraColors.accentCyan,
          ),
          const SizedBox(height: 10),
          _PackCard(
            title: 'Tamil Nadu Waters',
            subtitle: 'Charts, zones, depth data',
            size: '~38 MB',
            icon: Icons.map_outlined,
            color: SamudraColors.accentBlue,
          ),
          const SizedBox(height: 10),
          _PackCard(
            title: 'Lakshadweep Sea',
            subtitle: 'Reef maps, safe anchoring',
            size: '~25 MB',
            icon: Icons.anchor_outlined,
            color: SamudraColors.accentPurple,
          ),
          const SizedBox(height: 20),

          // ── Info banner ──────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: SamudraColors.accentCyan.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                  color: SamudraColors.accentCyan.withValues(alpha: 0.2)),
            ),
            child: Row(
              children: [
                const Icon(Icons.info_outline,
                    size: 18, color: SamudraColors.accentCyan),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Pack downloads will be available after '
                    'backend API integration (Milestone 8).',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color:
                              SamudraColors.accentCyan.withValues(alpha: 0.85),
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

// ─────────────────────────────────────────────────────────────────────────────
// Sub-widgets
// ─────────────────────────────────────────────────────────────────────────────

class _CacheStatusCard extends StatelessWidget {
  final int cachedCount;
  final String lastUpdated;
  final bool loading;

  const _CacheStatusCard({
    required this.cachedCount,
    required this.lastUpdated,
    required this.loading,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
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
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: SamudraColors.accentPurple.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.storage_outlined,
                    color: SamudraColors.accentPurple, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Offline Data',
                        style: Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(fontSize: 15)),
                    const SizedBox(height: 2),
                    Text('Local SQLite cache  ·  Milestone 3',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: SamudraColors.textMuted)),
                  ],
                ),
              ),
              if (loading)
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: SamudraColors.accentCyan,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(height: 1, color: SamudraColors.borderSubtle),
          const SizedBox(height: 12),
          _StatusRow(
            label: 'Cached Records',
            value: '$cachedCount',
            valueColor: cachedCount > 0
                ? SamudraColors.statusSafe
                : SamudraColors.textSecondary,
          ),
          const SizedBox(height: 8),
          _StatusRow(label: 'Last Updated', value: lastUpdated),
          const SizedBox(height: 8),
          _StatusRow(
            label: 'Storage Status',
            value: 'Available',
            valueColor: SamudraColors.statusSafe,
          ),
        ],
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String label;
  final String value;
  final Color valueColor;

  const _StatusRow({
    required this.label,
    required this.value,
    this.valueColor = SamudraColors.textPrimary,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: SamudraColors.textMuted, fontSize: 12)),
        Text(value,
            style: Theme.of(context)
                .textTheme
                .labelLarge
                ?.copyWith(color: valueColor, fontSize: 13)),
      ],
    );
  }
}

class _DevTestPanel extends StatelessWidget {
  final String? statusMessage;
  final VoidCallback onInsert;
  final VoidCallback onClear;
  final VoidCallback onRefresh;
  final bool loading;

  const _DevTestPanel({
    required this.statusMessage,
    required this.onInsert,
    required this.onClear,
    required this.onRefresh,
    required this.loading,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section header with DEV badge
        Row(
          children: [
            Text('Database Test',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: SamudraColors.textSecondary,
                      fontSize: 12,
                      letterSpacing: 0.5,
                    )),
            const SizedBox(width: 8),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: SamudraColors.statusWarning.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(
                    color:
                        SamudraColors.statusWarning.withValues(alpha: 0.4)),
              ),
              child: Text('DEV ONLY',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.statusWarning,
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      )),
            ),
          ],
        ),
        const SizedBox(height: 8),

        Container(
          decoration: BoxDecoration(
            color: SamudraColors.backgroundCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
                color: SamudraColors.statusWarning.withValues(alpha: 0.2)),
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Insert and clear demo records to verify SQLite '
                'persistence across app restarts.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.textMuted,
                    ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _DevButton(
                      label: 'Insert Test Data',
                      icon: Icons.add_circle_outline,
                      color: SamudraColors.statusSafe,
                      onTap: loading ? null : onInsert,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _DevButton(
                      label: 'Clear Test Data',
                      icon: Icons.delete_outline,
                      color: SamudraColors.statusDanger,
                      onTap: loading ? null : onClear,
                    ),
                  ),
                  const SizedBox(width: 8),
                  _DevButton(
                    label: '',
                    icon: Icons.refresh,
                    color: SamudraColors.accentCyan,
                    onTap: loading ? null : onRefresh,
                    compact: true,
                  ),
                ],
              ),
              if (statusMessage != null) ...[
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(Icons.check_circle_outline,
                        size: 14, color: SamudraColors.statusSafe),
                    const SizedBox(width: 6),
                    Text(statusMessage!,
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(
                                color: SamudraColors.statusSafe,
                                fontSize: 12)),
                  ],
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _DevButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;
  final bool compact;

  const _DevButton({
    required this.label,
    required this.icon,
    required this.color,
    this.onTap,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedOpacity(
        opacity: onTap == null ? 0.5 : 1.0,
        duration: const Duration(milliseconds: 150),
        child: Container(
          padding: EdgeInsets.symmetric(
              vertical: 9, horizontal: compact ? 10 : 0),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: color.withValues(alpha: 0.3)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 14, color: color),
              if (!compact) ...[
                const SizedBox(width: 6),
                Flexible(
                  child: Text(label,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(
                              color: color,
                              fontSize: 11,
                              fontWeight: FontWeight.w600),
                      overflow: TextOverflow.ellipsis),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 28),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Column(
        children: [
          Icon(Icons.cloud_off_outlined,
              size: 36,
              color: SamudraColors.textMuted.withValues(alpha: 0.5)),
          const SizedBox(height: 10),
          Text('No offline data available.',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: SamudraColors.textMuted)),
          const SizedBox(height: 4),
          Text('Tap "Insert Test Data" to populate the cache.',
              style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _RecordCard extends StatelessWidget {
  final MarineData record;
  final String Function(DateTime?) istFmt;

  const _RecordCard({required this.record, required this.istFmt});

  IconData _iconForType(String type) {
    switch (type) {
      case 'sea_surface_temp':
        return Icons.thermostat_outlined;
      case 'chlorophyll':
        return Icons.eco_outlined;
      case 'wave_height':
        return Icons.waves_outlined;
      case 'wind_speed':
        return Icons.air_outlined;
      case 'salinity':
        return Icons.water_drop_outlined;
      default:
        return Icons.data_object_outlined;
    }
  }

  Color _colorForSource(String source) {
    if (source == 'demo') return SamudraColors.statusWarning;
    return SamudraColors.accentCyan;
  }

  @override
  Widget build(BuildContext context) {
    final srcColor = _colorForSource(record.source);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: srcColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(9),
            ),
            child: Icon(_iconForType(record.dataType),
                size: 17, color: srcColor),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(record.title,
                          style: Theme.of(context)
                              .textTheme
                              .bodyLarge
                              ?.copyWith(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600)),
                    ),
                    // Source badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: srcColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(record.source.toUpperCase(),
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                  color: srcColor,
                                  fontSize: 8,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.6)),
                    ),
                  ],
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    if (record.value != null) ...[
                      Text(
                        '${record.value} ${record.unit ?? ''}',
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(
                                color: SamudraColors.accentCyan,
                                fontWeight: FontWeight.w600,
                                fontSize: 12),
                      ),
                      const SizedBox(width: 8),
                    ],
                    if (record.latitude != null && record.longitude != null)
                      Text(
                        '${record.latitude!.toStringAsFixed(2)}°N  '
                        '${record.longitude!.toStringAsFixed(2)}°E',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(
                                color: SamudraColors.textMuted,
                                fontSize: 10),
                      ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  'Cached: ${istFmt(record.createdAt)}',
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(
                          color: SamudraColors.textMuted, fontSize: 10),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: SamudraColors.textSecondary,
              fontSize: 12,
              letterSpacing: 0.5,
            ));
  }
}

class _PackCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String size;
  final IconData icon;
  final Color color;

  const _PackCard({
    required this.title,
    required this.subtitle,
    required this.size,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        )),
                const SizedBox(height: 2),
                Text(subtitle,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: SamudraColors.textMuted,
                        )),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(size,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.textMuted,
                        fontSize: 11,
                      )),
              const SizedBox(height: 6),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: color.withValues(alpha: 0.3), width: 0.5),
                ),
                child: Text('Download',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: color,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        )),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
