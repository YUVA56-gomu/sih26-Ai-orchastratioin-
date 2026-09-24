import 'package:flutter/material.dart';
import 'dart:async';
import '../../app/theme.dart';
import '../../widgets/samudra_drawer.dart';
import '../../widgets/ask_samudra.dart';
import '../../widgets/suggestion_card.dart';
import '../../widgets/quick_action_card.dart';
import '../../widgets/safety_status_card.dart';
import '../../services/location_service.dart';
import '../assistant/assistant_screen.dart';
import '../marine_map/marine_map_screen.dart';
import '../voice_assistant/voice_assistant_screen.dart';
import '../trip_brief/trip_brief_screen.dart';
import '../safety/safety_screen.dart';
import '../offline/offline_screen.dart';

// ─────────────────────────────────────────────────────────────────────────────
// HomeScreen — main landing screen
//
// Navigation: bottom nav (Home / Assistant / Map / Safety) + hamburger Drawer.
//
// AskSamudra and SuggestionCards now route queries to AssistantScreen via
// _openAssistant(query), which bumps the _assistantKey so a fresh
// AssistantScreen is created with initialQuery pre-filled.
// ─────────────────────────────────────────────────────────────────────────────

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedNavIndex = 0;

  // Incrementing this key forces a fresh AssistantScreen when a query is
  // submitted from the Home tab.
  int _assistantKey = 0;
  String? _pendingQuery;

  List<Widget> get _navScreens => [
        const _HomeBody(),
        AssistantScreen(
          key: ValueKey(_assistantKey),
          embedded: true,
          initialQuery: _pendingQuery,
        ),
        MarineMapScreen(
          embedded: true,
          // Voice search-bar microphone → open the voice dashboard with the
          // already-transcribed query so it is sent + spoken immediately.
          onVoiceQuery: (query) => _openVoiceAssistant(query: query),
        ),
        const SafetyScreen(embedded: true),
      ];

  /// Navigate to the Assistant tab. If [query] is provided the screen
  /// auto-submits it.
  void _openAssistant({String? query}) {
    setState(() {
      _pendingQuery = query;
      if (query != null) _assistantKey++;
      _selectedNavIndex = 1;
    });
  }

  /// Push the voice-first dashboard. If [query] is already transcribed (e.g.
  /// from the Map search-bar mic) it is sent + spoken immediately; otherwise
  /// the dashboard auto-listens.
  void _openVoiceAssistant({String? query}) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => VoiceAssistantScreen(pendingQuery: query),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      drawer: const SamudraDrawer(),
      appBar: _buildAppBar(context),
      body: IndexedStack(
        index: _selectedNavIndex,
        children: _navScreens,
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      elevation: 0,
      leading: Builder(
        builder: (context) => IconButton(
          icon: const Icon(Icons.menu, color: SamudraColors.textSecondary),
          tooltip: 'Menu',
          onPressed: () => Scaffold.of(context).openDrawer(),
        ),
      ),
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 26,
            height: 26,
            child: Image.asset(
              'assets/images/samudra_logo.png',
              fit: BoxFit.contain,
              errorBuilder: (context, e, s) => const Icon(
                Icons.waves,
                color: SamudraColors.accentCyan,
                size: 20,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            'Samudra AI',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: SamudraColors.textPrimary,
                ),
          ),
        ],
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: Stack(
            clipBehavior: Clip.none,
            children: [
              const Icon(
                Icons.notifications_outlined,
                color: SamudraColors.textSecondary,
                size: 22,
              ),
              Positioned(
                top: -2,
                right: -2,
                child: Container(
                  width: 7,
                  height: 7,
                  decoration: const BoxDecoration(
                    color: SamudraColors.accentCyan,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ],
          ),
          tooltip: 'Notifications',
          onPressed: () {},
        ),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: GestureDetector(
            onTap: () {},
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: SamudraColors.accentCyan.withValues(alpha: 0.15),
                shape: BoxShape.circle,
                border: Border.all(
                  color: SamudraColors.accentCyan.withValues(alpha: 0.4),
                  width: 1.5,
                ),
              ),
              child: const Icon(
                Icons.person_outline,
                size: 16,
                color: SamudraColors.accentCyan,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: const BoxDecoration(
        color: SamudraColors.backgroundCard,
        border: Border(
            top: BorderSide(color: SamudraColors.borderSubtle, width: 0.5)),
      ),
      child: BottomNavigationBar(
        currentIndex: _selectedNavIndex,
        onTap: (i) => setState(() {
          _selectedNavIndex = i;
          if (i == 1) _pendingQuery = null;
        }),
        backgroundColor: Colors.transparent,
        selectedItemColor: SamudraColors.accentCyan,
        unselectedItemColor: SamudraColors.textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelStyle: const TextStyle(fontSize: 10),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_bubble_outline),
            activeIcon: Icon(Icons.chat_bubble),
            label: 'Assistant',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.map_outlined),
            activeIcon: Icon(Icons.map),
            label: 'Map',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.shield_outlined),
            activeIcon: Icon(Icons.shield),
            label: 'Safety',
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _HomeBody
// ─────────────────────────────────────────────────────────────────────────────

class _HomeBody extends StatefulWidget {
  const _HomeBody();

  @override
  State<_HomeBody> createState() => _HomeBodyState();
}

class _HomeBodyState extends State<_HomeBody> {
  final _ls = LocationService.instance;
  StreamSubscription<LocationStatus>? _statusSub;
  LocationStatus _locationStatus = LocationStatus.idle;

  @override
  void initState() {
    super.initState();
    _locationStatus = _ls.currentStatus;
    _statusSub = _ls.statusStream.listen((status) {
      if (mounted) setState(() => _locationStatus = status);
    });
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    super.dispose();
  }

  void _sendQuery(String query) {
    final homeState = context.findAncestorStateOfType<_HomeScreenState>();
    homeState?._openAssistant(query: query);
  }

  /// Microphone tap → open the voice-first dashboard (auto-listens).
  void _openAssistantFromMic() {
    final homeState = context.findAncestorStateOfType<_HomeScreenState>();
    homeState?._openVoiceAssistant();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),

          // Greeting
          _Greeting(),
          const SizedBox(height: 24),

          // AI Input — wired to AssistantScreen
          AskSamudra(
            onSubmit: _sendQuery,
            onMicTap: _openAssistantFromMic,
          ),
          const SizedBox(height: 20),

          // Suggestions — wired to AssistantScreen
          _SectionLabel(label: 'Suggested'),
          const SizedBox(height: 10),
          _SuggestionGrid(onQuerySelected: _sendQuery),
          const SizedBox(height: 24),

          // Quick actions
          _SectionLabel(label: 'Quick Actions'),
          const SizedBox(height: 10),
          _buildQuickActionsGrid(context),
          const SizedBox(height: 24),

          // Safety status card driven by LocationService
          SafetyStatusCard(
            status: _marineStatusFromLocation(_locationStatus),
            statusText: _statusTextFromLocation(_locationStatus),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  MarineStatus _marineStatusFromLocation(LocationStatus s) {
    switch (s) {
      case LocationStatus.active:
        return MarineStatus.safe;
      case LocationStatus.searching:
        return MarineStatus.warning;
      case LocationStatus.serviceDisabled:
      case LocationStatus.permissionDenied:
      case LocationStatus.permissionPermanentlyDenied:
      case LocationStatus.error:
        return MarineStatus.danger;
      case LocationStatus.idle:
        return MarineStatus.warning;
    }
  }

  String _statusTextFromLocation(LocationStatus s) {
    switch (s) {
      case LocationStatus.active:
        return 'Location Active';
      case LocationStatus.searching:
        return 'Searching for GPS Signal...';
      case LocationStatus.serviceDisabled:
        return 'Location Services Disabled';
      case LocationStatus.permissionDenied:
        return 'Location Permission Denied';
      case LocationStatus.permissionPermanentlyDenied:
        return 'Location Permission Blocked';
      case LocationStatus.error:
        return 'Location Unavailable';
      case LocationStatus.idle:
        return 'Initialising Location...';
    }
  }
}

// ── Greeting ──────────────────────────────────────────────────────────────────

class _Greeting extends StatelessWidget {
  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _getGreeting(),
          style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                color: SamudraColors.textPrimary,
              ),
        ),
        const SizedBox(height: 4),
        Text(
          'What would you like to do?',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: SamudraColors.textSecondary,
              ),
        ),
      ],
    );
  }
}

// ── Section label ─────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: Theme.of(context).textTheme.labelLarge?.copyWith(
            color: SamudraColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
    );
  }
}

// ── Suggestion grid ───────────────────────────────────────────────────────────

class _SuggestionGrid extends StatelessWidget {
  static const _suggestions = [
    'Is it safe to fish today?',
    'Find nearby fishing zones',
    "Plan tomorrow's trip",
    'Show sea conditions',
  ];

  final void Function(String query) onQuerySelected;
  const _SuggestionGrid({required this.onQuerySelected});

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      childAspectRatio: 2.6,
      children: _suggestions
          .map((s) => SuggestionCard(text: s, onTap: () => onQuerySelected(s)))
          .toList(),
    );
  }
}

// ── Quick actions ─────────────────────────────────────────────────────────────

Widget _buildQuickActionsGrid(BuildContext context) {
  return GridView.count(
    crossAxisCount: 2,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    crossAxisSpacing: 10,
    mainAxisSpacing: 10,
    childAspectRatio: 1.55,
    children: [
      QuickActionCard(
        icon: Icons.map_outlined,
        label: 'Marine Map',
        accentColor: SamudraColors.accentCyan,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const MarineMapScreen()),
        ),
      ),
      QuickActionCard(
        icon: Icons.directions_boat_outlined,
        label: 'Trip Brief',
        accentColor: SamudraColors.accentBlue,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const TripBriefScreen()),
        ),
      ),
      QuickActionCard(
        icon: Icons.warning_amber_outlined,
        label: 'Safety Alerts',
        accentColor: SamudraColors.statusWarning,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const SafetyScreen()),
        ),
      ),
      QuickActionCard(
        icon: Icons.download_outlined,
        label: 'Offline Access',
        accentColor: SamudraColors.accentPurple,
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const OfflineScreen()),
        ),
      ),
    ],
  );
}
