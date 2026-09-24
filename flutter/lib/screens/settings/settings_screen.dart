import 'dart:async';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart' as ph;
import '../../app/theme.dart';
import '../../services/location_service.dart';
import '../../services/imbl_boundary_service.dart';
import '../../services/background_monitor_service.dart';
import '../../models/location_data.dart';
import '../../models/boundary_check_result.dart';
import '../../utils/demo_imbl.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SettingsScreen
// Contains all previous app settings plus a GPS Development Test panel
// added in Milestone 2.
// ─────────────────────────────────────────────────────────────────────────────

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: AppBar(
        backgroundColor: SamudraColors.backgroundDark,
        leading: IconButton(
          icon:
              const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text('Settings',
            style: Theme.of(context)
                .textTheme
                .headlineSmall
                ?.copyWith(fontSize: 17)),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        physics: const BouncingScrollPhysics(),
        children: [
          // ── GPS Development Test ─────────────────────────────────────
          // Added Milestone 2 — live device GPS readout for testing.
          const _GpsTestPanel(),
          const SizedBox(height: 16),

          // ── IMBL Boundary Test ───────────────────────────────────────
          // Added Milestone 4 — offline boundary engine testing.
          const _ImblTestPanel(),
          const SizedBox(height: 16),

          // ── Background Safety Monitor Test ───────────────────────────
          // Added Milestone 5 — background IMBL monitoring development test.
          const _BackgroundMonitorPanel(),
          const SizedBox(height: 8),

          // ── Account ─────────────────────────────────────────────────
          _SettingsSection(label: 'Account', children: [
            _SettingsTile(
              icon: Icons.person_outline,
              label: 'Profile',
              sub: 'Manage your account',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.notifications_outlined,
              label: 'Notifications',
              sub: 'Alerts and reminders',
              onTap: () {},
            ),
          ]),

          // ── Marine ───────────────────────────────────────────────────
          _SettingsSection(label: 'Marine', children: [
            _SettingsTile(
              icon: Icons.gps_fixed_outlined,
              label: 'GPS & Location',
              sub: 'Active  ·  Milestone 2',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.warning_amber_outlined,
              label: 'IMBL Boundary',
              sub: 'Active  ·  Milestone 4',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.volume_up_outlined,
              label: 'Audio Alerts',
              sub: 'Available in Milestone 6',
              disabled: true,
              onTap: null,
            ),
          ]),

          // ── App ──────────────────────────────────────────────────────
          _SettingsSection(label: 'App', children: [
            _SettingsTile(
              icon: Icons.dark_mode_outlined,
              label: 'Appearance',
              sub: 'Dark  •  SAMUDRA theme',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.language_outlined,
              label: 'Language',
              sub: 'English',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.storage_outlined,
              label: 'Offline Data',
              sub: 'Active  ·  Milestone 3',
              onTap: () {},
            ),
          ]),

          // ── About ─────────────────────────────────────────────────────
          _SettingsSection(label: 'About', children: [
            _SettingsTile(
              icon: Icons.info_outline,
              label: 'Version',
              sub: '1.0.0  ·  Milestone 5',
              onTap: () {},
            ),
            _SettingsTile(
              icon: Icons.shield_outlined,
              label: 'Privacy Policy',
              sub: '',
              onTap: () {},
            ),
          ]),

          const SizedBox(height: 32),
          Center(
            child: Text(
              'Samudra AI  ·  v1.0.0-milestone4',
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: SamudraColors.textMuted),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _GpsTestPanel — development GPS readout
// Subscribes to LocationService streams and displays live data.
// ─────────────────────────────────────────────────────────────────────────────

class _GpsTestPanel extends StatefulWidget {
  const _GpsTestPanel();

  @override
  State<_GpsTestPanel> createState() => _GpsTestPanelState();
}

class _GpsTestPanelState extends State<_GpsTestPanel> {
  final _ls = LocationService.instance;

  StreamSubscription<LocationData>? _locationSub;
  StreamSubscription<LocationStatus>? _statusSub;

  LocationData? _fix;
  LocationStatus _status = LocationStatus.idle;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    // Stream is started in main.dart — subscribe to existing broadcasts only.
    _status = _ls.currentStatus;
    _fix = _ls.lastLocation;

    _statusSub = _ls.statusStream.listen((s) {
      if (mounted) setState(() => _status = s);
    });

    _locationSub = _ls.locationStream.listen((data) {
      if (mounted) setState(() => _fix = data);
    });
  }

  Future<void> _requestFix() async {
    setState(() => _errorMessage = null);

    final serviceOn = await _ls.checkLocationService();
    if (!serviceOn) {
      if (mounted) setState(() => _errorMessage = 'Location services are disabled.');
      return;
    }

    final perm = await _ls.checkPermission();
    if (perm == LocationPermission.denied) {
      final result = await _ls.requestPermission();
      if (result == LocationPermission.denied) {
        if (mounted) setState(() => _errorMessage = 'Permission denied.');
        return;
      }
      if (result == LocationPermission.deniedForever) {
        if (mounted) setState(() => _errorMessage = 'Permission permanently denied.\nOpen Settings to allow.');
        return;
      }
    }
    if (perm == LocationPermission.deniedForever) {
      if (mounted) setState(() => _errorMessage = 'Permission permanently denied.\nOpen Settings to allow.');
      return;
    }

    // Ensure stream is running — stop first so refresh forces a new fix
    await _ls.stopLocationStream();
    await _ls.startLocationStream();
  }

  @override
  void dispose() {
    _locationSub?.cancel();
    _statusSub?.cancel();
    super.dispose();
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  String _statusLabel() {
    switch (_status) {
      case LocationStatus.active:
        return 'Active';
      case LocationStatus.searching:
        return 'Searching…';
      case LocationStatus.serviceDisabled:
        return 'Service Disabled';
      case LocationStatus.permissionDenied:
        return 'Permission Denied';
      case LocationStatus.permissionPermanentlyDenied:
        return 'Permission Blocked';
      case LocationStatus.error:
        return 'Error';
      case LocationStatus.idle:
        return 'Idle';
    }
  }

  Color _statusColor() {
    switch (_status) {
      case LocationStatus.active:
        return SamudraColors.statusSafe;
      case LocationStatus.searching:
        return SamudraColors.statusWarning;
      default:
        return SamudraColors.statusDanger;
    }
  }

  String _fmt(double? v, {int decimals = 6, String suffix = ''}) {
    if (v == null) return '--';
    return '${v.toStringAsFixed(decimals)}$suffix';
  }

  String _fmtTime(DateTime? t) {
    if (t == null) return '--';
    // Keep the underlying timestamp in UTC (as stored in LocationData).
    // Convert to IST (Asia/Kolkata = UTC+05:30) for display only.
    // We add the fixed offset as a Duration — no extra packages needed and
    // the result is correct regardless of what timezone the device is set to.
    final ist = t.toUtc().add(const Duration(hours: 5, minutes: 30));
    return '${ist.hour.toString().padLeft(2, '0')}:'
        '${ist.minute.toString().padLeft(2, '0')}:'
        '${ist.second.toString().padLeft(2, '0')} IST';
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section label
        Padding(
          padding: const EdgeInsets.only(bottom: 8, top: 4),
          child: Row(
            children: [
              Text(
                'GPS DEVELOPMENT TEST',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.accentCyan,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
              ),
              const SizedBox(width: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: SamudraColors.accentCyan.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                      color: SamudraColors.accentCyan.withValues(alpha: 0.3)),
                ),
                child: Text(
                  'MILESTONE 2',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.accentCyan,
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                ),
              ),
            ],
          ),
        ),

        // Panel card
        Container(
          decoration: BoxDecoration(
            color: SamudraColors.backgroundCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: SamudraColors.accentCyan.withValues(alpha: 0.25),
            ),
          ),
          child: Column(
            children: [
              // ── Status header ─────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _statusColor(),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: _statusColor().withValues(alpha: 0.5),
                            blurRadius: 5,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'GPS Status',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: SamudraColors.textMuted,
                            fontSize: 11,
                          ),
                    ),
                    const Spacer(),
                    Text(
                      _statusLabel(),
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: _statusColor(),
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ],
                ),
              ),

              const Divider(
                  height: 1, color: SamudraColors.borderSubtle),

              // ── Data rows ─────────────────────────────────────────
              _DataRow(
                label: 'Latitude',
                value: _fmt(_fix?.latitude),
                unit: '°',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _DataRow(
                label: 'Longitude',
                value: _fmt(_fix?.longitude),
                unit: '°',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _DataRow(
                label: 'Accuracy',
                value: _fmt(_fix?.accuracy, decimals: 1),
                unit: 'm',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _DataRow(
                label: 'Speed',
                value: _fix != null
                    ? '${_fmt(_fix!.speedKnots, decimals: 2)} kn  '
                        '(${_fmt(_fix!.speed, decimals: 2)} m/s)'
                    : '--',
                unit: '',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _DataRow(
                label: 'Heading',
                value: _fmt(_fix?.heading, decimals: 1),
                unit: '°',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _DataRow(
                label: 'Last Updated',
                value: _fmtTime(_fix?.timestamp),
                unit: '',
              ),

              // ── Error message ─────────────────────────────────────
              if (_errorMessage != null) ...[
                const Divider(height: 1, color: SamudraColors.borderSubtle),
                Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline,
                          size: 16, color: SamudraColors.statusWarning),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: SamudraColors.statusWarning,
                                  ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // ── Action buttons ────────────────────────────────────
              const Divider(height: 1, color: SamudraColors.borderSubtle),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    // Refresh button
                    Expanded(
                      child: _ActionButton(
                        icon: Icons.refresh,
                        label: 'Refresh',
                        onTap: _requestFix,
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Open location settings if disabled or blocked
                    if (_status == LocationStatus.serviceDisabled)
                      Expanded(
                        child: _ActionButton(
                          icon: Icons.location_off_outlined,
                          label: 'Open Settings',
                          onTap: () => _ls.openLocationSettings(),
                          accent: SamudraColors.statusWarning,
                        ),
                      ),
                    if (_status == LocationStatus.permissionPermanentlyDenied)
                      Expanded(
                        child: _ActionButton(
                          icon: Icons.settings_outlined,
                          label: 'App Settings',
                          onTap: () => _ls.openAppSettings(),
                          accent: SamudraColors.statusWarning,
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Sub-widgets ───────────────────────────────────────────────────────────────

class _DataRow extends StatelessWidget {
  final String label;
  final String value;
  final String unit;

  const _DataRow({
    required this.label,
    required this.value,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SamudraColors.textMuted,
                    fontSize: 12,
                  ),
            ),
          ),
          Expanded(
            child: Text(
              value + unit,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: value == '--'
                        ? SamudraColors.textMuted
                        : SamudraColors.textPrimary,
                    fontSize: 13,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color accent;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.accent = SamudraColors.accentCyan,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
          color: accent.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: accent.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 14, color: accent),
            const SizedBox(width: 6),
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: accent,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Shared settings widgets ───────────────────────────────────────────────────

class _SettingsSection extends StatelessWidget {
  final String label;
  final List<Widget> children;
  const _SettingsSection({required this.label, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8, top: 4),
          child: Text(
            label.toUpperCase(),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: SamudraColors.textMuted,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: SamudraColors.backgroundCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: SamudraColors.borderSubtle),
          ),
          child: Column(
            children: List.generate(children.length, (i) {
              return Column(
                children: [
                  children[i],
                  if (i < children.length - 1)
                    const Divider(
                        height: 1,
                        indent: 50,
                        color: SamudraColors.borderSubtle),
                ],
              );
            }),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String sub;
  final bool disabled;
  final VoidCallback? onTap;

  const _SettingsTile({
    required this.icon,
    required this.label,
    required this.sub,
    this.disabled = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color =
        disabled ? SamudraColors.textMuted : SamudraColors.textSecondary;
    return InkWell(
      onTap: disabled ? null : onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontSize: 14,
                            color: disabled
                                ? SamudraColors.textMuted
                                : SamudraColors.textPrimary,
                          )),
                  if (sub.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(sub,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: disabled
                                ? SamudraColors.textMuted.withValues(alpha: 0.6)
                                : SamudraColors.textMuted)),
                  ],
                ],
              ),
            ),
            if (!disabled)
              const Icon(Icons.chevron_right,
                  size: 18, color: SamudraColors.textMuted),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _ImblTestPanel — DEVELOPMENT TEST for Milestone 4 IMBL boundary engine.
//
// Uses the current GPS position and the DEMO test polygon.
// NOT a production feature — clearly labelled as development-only.
// ─────────────────────────────────────────────────────────────────────────────

class _ImblTestPanel extends StatefulWidget {
  const _ImblTestPanel();

  @override
  State<_ImblTestPanel> createState() => _ImblTestPanelState();
}

class _ImblTestPanelState extends State<_ImblTestPanel> {
  final _ls = LocationService.instance;
  final _imbl = ImblBoundaryService.instance;

  StreamSubscription<LocationData>? _locSub;
  LocationData? _fix;
  BoundaryCheckResult? _result;
  bool _polygonLoaded = false;

  @override
  void initState() {
    super.initState();
    _fix = _ls.lastLocation;
    _locSub = _ls.locationStream.listen((d) {
      if (mounted) setState(() => _fix = d);
    });
    // Pre-load the demo polygon
    _loadDemoPolygon();
  }

  void _loadDemoPolygon() {
    try {
      _imbl.loadBoundary(DemoImbl.polygon());
      setState(() => _polygonLoaded = true);
    } catch (_) {
      setState(() => _polygonLoaded = false);
    }
  }

  void _runCheck() {
    if (!_polygonLoaded) _loadDemoPolygon();
    final result = _imbl.check(
      _fix,
      DemoImbl.id,
      config: const BoundaryCheckConfig(warningDistanceMeters: 500.0),
    );
    setState(() => _result = result);
  }

  @override
  void dispose() {
    _locSub?.cancel();
    super.dispose();
  }

  // ── Display helpers ───────────────────────────────────────────────────────

  Color _classColor(BoundaryClassification? c) {
    switch (c) {
      case BoundaryClassification.safe:
        return SamudraColors.statusSafe;
      case BoundaryClassification.nearBoundary:
        return SamudraColors.statusWarning;
      case BoundaryClassification.outside:
        return SamudraColors.accentBlue;
      case BoundaryClassification.unknown:
      case null:
        return SamudraColors.textMuted;
    }
  }

  String _classLabel(BoundaryClassification? c) {
    switch (c) {
      case BoundaryClassification.safe:
        return 'SAFE';
      case BoundaryClassification.nearBoundary:
        return 'NEAR BOUNDARY';
      case BoundaryClassification.outside:
        return 'OUTSIDE';
      case BoundaryClassification.unknown:
        return 'UNKNOWN';
      case null:
        return '--';
    }
  }

  String _fmtDist(double? d) {
    if (d == null) return '--';
    if (d >= 1000) return '${(d / 1000).toStringAsFixed(2)} km';
    return '${d.toStringAsFixed(0)} m';
  }

  String _fmtCoord(double? v, {int dp = 6}) =>
      v == null ? '--' : v.toStringAsFixed(dp);

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final cls = _result?.classification;
    final clsColor = _classColor(cls);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header with milestone badge
        Padding(
          padding: const EdgeInsets.only(bottom: 8, top: 4),
          child: Row(
            children: [
              Text(
                'IMBL BOUNDARY TEST',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.statusWarning,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: SamudraColors.statusWarning.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                      color: SamudraColors.statusWarning.withValues(alpha: 0.4)),
                ),
                child: Text(
                  'MILESTONE 4  ·  DEV ONLY',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.statusWarning,
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                ),
              ),
            ],
          ),
        ),

        // Panel card
        Container(
          decoration: BoxDecoration(
            color: SamudraColors.backgroundCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: SamudraColors.statusWarning.withValues(alpha: 0.25),
            ),
          ),
          child: Column(
            children: [
              // Boundary info row
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
                child: Row(
                  children: [
                    const Icon(Icons.fence_outlined,
                        size: 16, color: SamudraColors.statusWarning),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'DEMO IMBL TEST ZONE',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.textSecondary,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ),
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _polygonLoaded
                            ? SamudraColors.statusSafe
                            : SamudraColors.textMuted,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _polygonLoaded ? 'Loaded' : 'Not loaded',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: _polygonLoaded
                                ? SamudraColors.statusSafe
                                : SamudraColors.textMuted,
                            fontSize: 11,
                          ),
                    ),
                  ],
                ),
              ),

              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // Data rows
              _ImblDataRow(
                label: 'Latitude',
                value: _fmtCoord(_fix?.latitude),
                unit: '°',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _ImblDataRow(
                label: 'Longitude',
                value: _fmtCoord(_fix?.longitude),
                unit: '°',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _ImblDataRow(
                label: 'GPS Accuracy',
                value: _fmtCoord(_fix?.accuracy, dp: 1),
                unit: ' m',
              ),
              const Divider(
                  height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _ImblDataRow(
                label: 'Dist to Boundary',
                value: _result != null
                    ? _fmtDist(_result!.distanceToBoundaryMeters)
                    : '--',
                unit: '',
              ),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // Status result
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                child: Row(
                  children: [
                    Text(
                      'Status',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: SamudraColors.textMuted,
                            fontSize: 12,
                          ),
                    ),
                    const Spacer(),
                    if (_result != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: clsColor.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                              color: clsColor.withValues(alpha: 0.5)),
                        ),
                        child: Text(
                          _classLabel(cls),
                          style:
                              Theme.of(context).textTheme.labelLarge?.copyWith(
                                    color: clsColor,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.5,
                                  ),
                        ),
                      ),
                    ] else
                      Text('--',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: SamudraColors.textMuted)),
                  ],
                ),
              ),

              // Note (accuracy warning / error message)
              if (_result?.note != null) ...[
                const Divider(height: 1, color: SamudraColors.borderSubtle),
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 8, 14, 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        _result!.isUnknown
                            ? Icons.info_outline
                            : Icons.check_circle_outline,
                        size: 14,
                        color: _result!.isUnknown
                            ? SamudraColors.statusWarning
                            : SamudraColors.textMuted,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          _result!.note!,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                  color: _result!.isUnknown
                                      ? SamudraColors.statusWarning
                                      : SamudraColors.textMuted,
                                  fontSize: 11),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // Demo notice
              Container(
                margin: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: SamudraColors.statusWarning.withValues(alpha: 0.07),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: SamudraColors.statusWarning.withValues(alpha: 0.2)),
                ),
                child: Text(
                  '⚠ DEMO DATA ONLY — This is NOT the real IMBL. '
                  'The test polygon is a synthetic rectangle in the Arabian '
                  'Sea used only for algorithm verification. '
                  'Do not use for navigation or safety decisions.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.statusWarning.withValues(alpha: 0.85),
                        fontSize: 10,
                      ),
                ),
              ),

              // Run Check button
              const Divider(height: 1, color: SamudraColors.borderSubtle),
              Padding(
                padding: const EdgeInsets.all(12),
                child: SizedBox(
                  width: double.infinity,
                  child: GestureDetector(
                    onTap: _runCheck,
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      decoration: BoxDecoration(
                        color: SamudraColors.statusWarning.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: SamudraColors.statusWarning
                                .withValues(alpha: 0.4)),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.radar_outlined,
                              size: 15, color: SamudraColors.statusWarning),
                          const SizedBox(width: 8),
                          Text(
                            'Run Boundary Check',
                            style:
                                Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: SamudraColors.statusWarning,
                                      fontSize: 13,
                                      fontWeight: FontWeight.w700,
                                    ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Simple data row for the IMBL panel ────────────────────────────────────────

class _ImblDataRow extends StatelessWidget {
  final String label;
  final String value;
  final String unit;

  const _ImblDataRow({
    required this.label,
    required this.value,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.textMuted,
                      fontSize: 12,
                    )),
          ),
          Expanded(
            child: Text(
              value + unit,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: value == '--'
                        ? SamudraColors.textMuted
                        : SamudraColors.textPrimary,
                    fontSize: 13,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _BackgroundMonitorPanel — Milestone 5 development test UI.
//
// Displays monitor state, latest GPS fix, latest IMBL result, and the
// measured calculation time.  Start/Stop buttons control the monitor.
// ─────────────────────────────────────────────────────────────────────────────

class _BackgroundMonitorPanel extends StatefulWidget {
  const _BackgroundMonitorPanel();

  @override
  State<_BackgroundMonitorPanel> createState() =>
      _BackgroundMonitorPanelState();
}

class _BackgroundMonitorPanelState extends State<_BackgroundMonitorPanel> with WidgetsBindingObserver {
  final _monitor = BackgroundMonitorService.instance;

  StreamSubscription<MonitorState>? _stateSub;
  StreamSubscription<MonitorSnapshot>? _snapshotSub;

  MonitorState _state = MonitorState.stopped;
  MonitorSnapshot? _snapshot;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _state = _monitor.state;
    _snapshot = _monitor.latestSnapshot;

    // Initial check to ensure UI reflects current permission state
    _monitor.checkNotificationPermission().then((_) {
      if (mounted) setState(() {});
    });

    _stateSub = _monitor.stateStream.listen((s) {
      if (mounted) setState(() => _state = s);
    });
    _snapshotSub = _monitor.snapshotStream.listen((snap) {
      if (mounted) setState(() => _snapshot = snap);
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _stateSub?.cancel();
    _snapshotSub?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // Re-check notification permission when user returns from Settings
      _monitor.checkNotificationPermission().then((_) {
        if (mounted) setState(() {});
      });
    }
  }

  // Re-check notification permission or request it.
  Future<void> _grantNotification() async {
    final status = await _monitor.checkNotificationPermission();
    
    if (status == ph.PermissionStatus.permanentlyDenied) {
      // Handled: user previously tapped "Don't ask again"
      await _monitor.openNotificationSettings();
    } else {
      // Trigger the Android runtime permission dialog
      final result = await _monitor.requestNotificationPermission();
      if (result == ph.PermissionStatus.granted) {
        // Automatically start if they just granted it while we were in a blocked state
        if (_state == MonitorState.notificationPermissionBlocked) {
          await _monitor.start();
        }
      }
    }
    if (mounted) setState(() {});
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  String _stateLabel() {
    switch (_state) {
      case MonitorState.stopped:                    return 'Stopped';
      case MonitorState.starting:                   return 'Starting…';
      case MonitorState.monitoring:                 return 'Monitoring';
      case MonitorState.permissionRequired:         return 'Permission Required';
      case MonitorState.notificationPermissionBlocked: return 'Notification Blocked';
      case MonitorState.locationUnavailable:        return 'Location Unavailable';
      case MonitorState.error:                      return 'Error';
    }
  }

  Color _stateColor() {
    switch (_state) {
      case MonitorState.monitoring:  return SamudraColors.statusSafe;
      case MonitorState.starting:    return SamudraColors.statusWarning;
      case MonitorState.stopped:     return SamudraColors.textMuted;
      default:                       return SamudraColors.statusDanger;
    }
  }

  String _classLabel(BoundaryClassification? c) {
    switch (c) {
      case BoundaryClassification.safe:         return 'SAFE';
      case BoundaryClassification.nearBoundary: return 'NEAR BOUNDARY';
      case BoundaryClassification.outside:      return 'OUTSIDE';
      case BoundaryClassification.unknown:      return 'UNKNOWN';
      case null:                                return '--';
    }
  }

  Color _classColor(BoundaryClassification? c) {
    switch (c) {
      case BoundaryClassification.safe:         return SamudraColors.statusSafe;
      case BoundaryClassification.nearBoundary: return SamudraColors.statusWarning;
      case BoundaryClassification.outside:      return SamudraColors.accentBlue;
      default:                                  return SamudraColors.textMuted;
    }
  }

  String _fmtCoord(double? v) =>
      v == null ? '--' : v.toStringAsFixed(6);

  String _fmtDist(double? d) {
    if (d == null) return '--';
    return d >= 1000
        ? '${(d / 1000).toStringAsFixed(2)} km'
        : '${d.toStringAsFixed(0)} m';
  }

  String _fmtTime(DateTime? t) {
    if (t == null) return '--';
    final ist = t.toUtc().add(const Duration(hours: 5, minutes: 30));
    return '${ist.hour.toString().padLeft(2, '0')}:'
        '${ist.minute.toString().padLeft(2, '0')}:'
        '${ist.second.toString().padLeft(2, '0')} IST';
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final stateColor  = _stateColor();
    final snap        = _snapshot;
    final cls         = snap?.boundaryResult.classification;
    final clsColor    = _classColor(cls);
    final isRunning   = _state == MonitorState.monitoring;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Header ────────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.only(bottom: 8, top: 4),
          child: Row(
            children: [
              Text(
                'BACKGROUND SAFETY MONITOR',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.accentBlue,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: SamudraColors.accentBlue.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                      color: SamudraColors.accentBlue.withValues(alpha: 0.35)),
                ),
                child: Text(
                  'MILESTONE 5  ·  DEV ONLY',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.accentBlue,
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                ),
              ),
            ],
          ),
        ),

        // ── Panel card ────────────────────────────────────────────────
        Container(
          decoration: BoxDecoration(
            color: SamudraColors.backgroundCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
                color: SamudraColors.accentBlue.withValues(alpha: 0.25)),
          ),
          child: Column(
            children: [
              // Status row
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: stateColor,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: stateColor.withValues(alpha: 0.5),
                            blurRadius: 5,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text('Status',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: SamudraColors.textMuted,
                              fontSize: 11,
                            )),
                    const Spacer(),
                    Text(
                      _stateLabel(),
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: stateColor,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // Notification permission row
              _MonRow(
                label: 'Notification',
                value: _monitor.notificationGranted ? 'Enabled' : 'Permission Required',
                valueColor: _monitor.notificationGranted
                    ? SamudraColors.statusSafe
                    : SamudraColors.statusWarning,
              ),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // GPS rows
              _MonRow(label: 'Last GPS Lat',
                  value: '${_fmtCoord(snap?.location.latitude)}°'),
              const Divider(height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _MonRow(label: 'Last GPS Lon',
                  value: '${_fmtCoord(snap?.location.longitude)}°'),
              const Divider(height: 1, indent: 14, color: SamudraColors.borderSubtle),
              _MonRow(label: 'Accuracy',
                  value: snap?.location.accuracy != null
                      ? '${snap!.location.accuracy.toStringAsFixed(1)} m'
                      : '--'),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // IMBL result row
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: 14, vertical: 11),
                child: Row(
                  children: [
                    SizedBox(
                      width: 120,
                      child: Text('Last IMBL Result',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                  color: SamudraColors.textMuted,
                                  fontSize: 12)),
                    ),
                    const Spacer(),
                    if (snap != null)
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: clsColor.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(5),
                          border: Border.all(
                              color: clsColor.withValues(alpha: 0.45)),
                        ),
                        child: Text(
                          _classLabel(cls),
                          style: Theme.of(context)
                              .textTheme
                              .labelLarge
                              ?.copyWith(
                                  color: clsColor,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700),
                        ),
                      )
                    else
                      Text('--',
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: SamudraColors.textMuted)),
                  ],
                ),
              ),
              const Divider(height: 1, indent: 14, color: SamudraColors.borderSubtle),

              _MonRow(
                  label: 'Distance to Boundary',
                  value: _fmtDist(
                      snap?.boundaryResult.distanceToBoundaryMeters)),
              const Divider(height: 1, indent: 14, color: SamudraColors.borderSubtle),

              // Benchmark row
              _MonRow(
                label: 'IMBL Calculation',
                value: snap != null
                    ? '${snap.imblCalcMs.toStringAsFixed(2)} ms'
                    : '--',
                valueColor: snap != null
                    ? (snap.imblCalcMs < 15.0
                        ? SamudraColors.statusSafe
                        : SamudraColors.statusWarning)
                    : SamudraColors.textMuted,
              ),
              const Divider(height: 1, indent: 14, color: SamudraColors.borderSubtle),

              _MonRow(label: 'Last Updated',
                  value: _fmtTime(snap?.producedAt)),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // Error / note
              if (_monitor.errorMessage != null) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 8, 14, 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline,
                          size: 14,
                          color: SamudraColors.statusWarning),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          _monitor.errorMessage!,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(
                                  color: SamudraColors.statusWarning,
                                  fontSize: 11),
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1, color: SamudraColors.borderSubtle),
              ],

              // Demo notice
              Container(
                margin: const EdgeInsets.fromLTRB(12, 8, 12, 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: SamudraColors.statusWarning.withValues(alpha: 0.07),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color:
                          SamudraColors.statusWarning.withValues(alpha: 0.2)),
                ),
                child: Text(
                  '⚠ DEMO POLYGON ONLY — Not the real IMBL.\n'
                  'Background monitoring uses the synthetic test zone.\n'
                  'Do not use for real safety decisions.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SamudraColors.statusWarning
                            .withValues(alpha: 0.85),
                        fontSize: 10,
                      ),
                ),
              ),
              const Divider(height: 1, color: SamudraColors.borderSubtle),

              // Start / Stop buttons
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: _MonBtn(
                            label: 'Start Monitoring',
                            icon: Icons.play_arrow_outlined,
                            color: SamudraColors.statusSafe,
                            enabled: !isRunning &&
                                _state != MonitorState.starting,
                            onTap: () => _monitor.start(),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: _MonBtn(
                            label: 'Stop Monitoring',
                            icon: Icons.stop_outlined,
                            color: SamudraColors.statusDanger,
                            enabled: isRunning,
                            onTap: () => _monitor.stop(),
                          ),
                        ),
                      ],
                    ),
                    // Show Grant Notification button when blocked
                    if (_state ==
                        MonitorState.notificationPermissionBlocked) ...[
                      const SizedBox(height: 8),
                      _MonBtn(
                        label: 'Grant Notification Permission',
                        icon: Icons.notifications_outlined,
                        color: SamudraColors.statusWarning,
                        enabled: true,
                        onTap: _grantNotification,
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Small data row used by the monitor panel ──────────────────────────────────

class _MonRow extends StatelessWidget {
  final String label;
  final String value;
  final Color valueColor;

  const _MonRow({
    required this.label,
    required this.value,
    this.valueColor = SamudraColors.textPrimary,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          SizedBox(
            width: 150,
            child: Text(label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.textMuted,
                      fontSize: 12,
                    )),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: value == '--' ? SamudraColors.textMuted : valueColor,
                    fontSize: 13,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Button widget used inside the monitor panel ───────────────────────────────

class _MonBtn extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final bool enabled;
  final VoidCallback onTap;

  const _MonBtn({
    required this.label,
    required this.icon,
    required this.color,
    required this.enabled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      opacity: enabled ? 1.0 : 0.4,
      duration: const Duration(milliseconds: 150),
      child: GestureDetector(
        onTap: enabled ? onTap : null,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: color.withValues(alpha: 0.35)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 15, color: color),
              const SizedBox(width: 6),
              Text(label,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: color,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      )),
            ],
          ),
        ),
      ),
    );
  }
}
