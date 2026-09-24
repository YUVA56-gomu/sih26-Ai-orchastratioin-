import 'package:flutter/material.dart';
import '../app/theme.dart';
import '../models/conversation/conversation_summary.dart';
import '../screens/assistant/assistant_screen.dart';
import '../screens/marine_map/marine_map_screen.dart';
import '../screens/trip_brief/trip_brief_screen.dart';
import '../screens/safety/safety_screen.dart';
import '../screens/offline/offline_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../services/conversation/backend_conversation_service.dart';
import '../services/conversation/conversation_service.dart';

class SamudraDrawer extends StatefulWidget {
  final void Function(String conversationId)? onSelectConversation;
  final VoidCallback? onNewChat;

  const SamudraDrawer({
    super.key,
    this.onSelectConversation,
    this.onNewChat,
  });

  @override
  State<SamudraDrawer> createState() => _SamudraDrawerState();
}

class _SamudraDrawerState extends State<SamudraDrawer> {
  List<ConversationSummary> _conversations = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadConversations();
  }

  Future<void> _loadConversations() async {
    final service = ConversationService.instance;
    if (service is! ConversationHistoryProvider) return;
    final provider = service as ConversationHistoryProvider;

    setState(() => _isLoading = true);
    try {
      final list = await provider.loadConversations();
      if (mounted) {
        setState(() {
          _conversations = list;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      width: MediaQuery.of(context).size.width * 0.82,
      backgroundColor: SamudraColors.backgroundDrawer,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _DrawerHeader(),
            const Divider(height: 1, color: SamudraColors.borderSubtle),
            const SizedBox(height: 8),

            // ── New Conversation ──────────────────────────────────────────
            _DrawerNavTile(
              icon: Icons.add,
              label: 'New Conversation',
              onTap: () {
                Navigator.pop(context);
                final service = ConversationService.instance;
                if (service is BackendConversationService) {
                  service.newConversation();
                }
                if (widget.onNewChat != null) {
                  widget.onNewChat!();
                } else {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const AssistantScreen()),
                  );
                }
              },
            ),

            const SizedBox(height: 12),

            // ── Recent conversations ──────────────────────────────────────
            _DrawerSectionLabel(label: 'RECENT CONVERSATIONS'),

            Expanded(
              child: _isLoading
                  ? const Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: SamudraColors.accentCyan,
                        ),
                      ),
                    )
                  : _conversations.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          child: Text(
                            'No past conversations yet.',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: SamudraColors.textMuted,
                                ),
                          ),
                        )
                      : ListView.builder(
                          padding: EdgeInsets.zero,
                          itemCount: _conversations.length,
                          itemBuilder: (ctx, i) {
                            final conv = _conversations[i];
                            final title = conv.title ?? conv.lastMessage ?? 'Conversation #${i + 1}';
                            return _DrawerRecentTile(
                              label: title,
                              onTap: () {
                                Navigator.pop(context);
                                if (widget.onSelectConversation != null) {
                                  widget.onSelectConversation!(conv.conversationId);
                                } else {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => AssistantScreen(
                                        initialConversationId: conv.conversationId,
                                      ),
                                    ),
                                  );
                                }
                              },
                            );
                          },
                        ),
            ),

            const Divider(
              height: 1,
              indent: 16,
              endIndent: 16,
              color: SamudraColors.borderSubtle,
            ),
            const SizedBox(height: 8),

            // ── Features ─────────────────────────────────────────────────
            _DrawerSectionLabel(label: 'FEATURES'),
            _DrawerNavTile(
              icon: Icons.map_outlined,
              label: 'Marine Map',
              onTap: () => _navigate(context, const MarineMapScreen()),
            ),
            _DrawerNavTile(
              icon: Icons.directions_boat_outlined,
              label: 'Trip Briefs',
              onTap: () => _navigate(context, const TripBriefScreen()),
            ),
            _DrawerNavTile(
              icon: Icons.warning_amber_outlined,
              label: 'Safety Alerts',
              onTap: () => _navigate(context, const SafetyScreen()),
            ),
            _DrawerNavTile(
              icon: Icons.download_outlined,
              label: 'Offline Packs',
              onTap: () => _navigate(context, const OfflineScreen()),
            ),

            const Divider(height: 1, color: SamudraColors.borderSubtle),

            // ── Bottom: Settings & Profile ────────────────────────────────
            _DrawerNavTile(
              icon: Icons.settings_outlined,
              label: 'Settings',
              onTap: () => _navigate(context, const SettingsScreen()),
            ),
            _DrawerNavTile(
              icon: Icons.person_outline,
              label: 'Profile',
              onTap: () => Navigator.pop(context),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  void _navigate(BuildContext context, Widget screen) {
    Navigator.pop(context);
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }
}

class _DrawerHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: SamudraColors.accentCyan.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: SamudraColors.accentCyan.withValues(alpha: 0.3),
                width: 1,
              ),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(9),
              child: Image.asset(
                'assets/images/samudra_logo.png',
                fit: BoxFit.contain,
                errorBuilder: (ctx, e, s) => const Icon(
                  Icons.waves,
                  color: SamudraColors.accentCyan,
                  size: 20,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Samudra AI',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: SamudraColors.textPrimary,
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                    ),
              ),
              Text(
                'Marine Intelligence',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: SamudraColors.accentCyan,
                      fontSize: 10,
                    ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DrawerSectionLabel extends StatelessWidget {
  final String label;
  const _DrawerSectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: SamudraColors.textMuted,
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
            ),
      ),
    );
  }
}

class _DrawerNavTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _DrawerNavTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Icon(icon, size: 18, color: SamudraColors.textSecondary),
            const SizedBox(width: 12),
            Text(
              label,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontSize: 14,
                    color: SamudraColors.textPrimary,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DrawerRecentTile extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _DrawerRecentTile({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            const Icon(
              Icons.chat_bubble_outline,
              size: 15,
              color: SamudraColors.textMuted,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontSize: 13,
                      color: SamudraColors.textSecondary,
                    ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
