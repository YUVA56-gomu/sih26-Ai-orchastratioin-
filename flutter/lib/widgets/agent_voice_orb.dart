import 'package:flutter/material.dart';

import '../app/theme.dart';

/// The functional state of the voice dashboard's central orb.
enum AgentVoiceState { idle, listening, thinking, speaking }

/// The centrepiece of the voice dashboard: the Samudra AI logo inside a
/// glowing disc, surrounded by concentric **rounded ripple waves** that expand
/// outward to indicate speech (listening / thinking / speaking).
///
/// The whole orb is tappable ([onTap]) — that is the "mic" action in the
/// dashboard — and shows a small state icon (`mic`, speaker, `…`) overlay.
///
/// Wave animation runs continuously while [state] != [AgentVoiceState.idle];
/// in the idle state only a subtle breathing glow remains. Widget tests must
/// therefore pump by duration (never `pumpAndSettle`) while a state is active.
class AgentVoiceOrb extends StatefulWidget {
  const AgentVoiceOrb({
    super.key,
    required this.state,
    this.onTap,
    this.size = 240,
  });

  final AgentVoiceState state;

  /// Invoked when the orb is tapped. `null` disables the tap/ripple.
  final VoidCallback? onTap;

  /// Diameter of the whole control (logo disc + waves). Defaults to 240.
  final double size;

  @override
  State<AgentVoiceOrb> createState() => _AgentVoiceOrbState();
}

class _AgentVoiceOrbState extends State<AgentVoiceOrb>
    with SingleTickerProviderStateMixin {
  late final AnimationController _anim;

  bool get _isActive => widget.state != AgentVoiceState.idle;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    if (_isActive) _anim.repeat();
  }

  @override
  void didUpdateWidget(AgentVoiceOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_isActive && !_anim.isAnimating) {
      _anim.repeat();
    } else if (!_isActive && _anim.isAnimating) {
      _anim.stop();
      _anim.value = 0;
    }
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final disc = widget.size * 0.42; // logo disc diameter (~100 for 240 orb)
    final discColor = _discColor(widget.state);
    final icon = _stateIcon(widget.state);
    final iconColor = _iconColor(widget.state);

    return GestureDetector(
      onTap: widget.onTap,
      child: SizedBox(
        width: widget.size,
        height: widget.size,
        child: Stack(
          alignment: Alignment.center,
          children: [
            // ── Rounded ripple waves ──────────────────────────────────────────
            AnimatedBuilder(
              animation: _anim,
              builder: (ctx, _) {
                final value = _isActive ? _anim.value : 0.0;
                return Stack(
                  alignment: Alignment.center,
                  children: List.generate(4, (i) {
                    // Stagger each ring so the waves roll outward one after
                    // another, creating a continuous "speech" pulse.
                    final t = (value * 1.25 + i * 0.25) % 1.0;
                    final radius =
                        disc * 0.5 + t * (widget.size * 0.5 - disc * 0.5);
                    final opacity = (1.0 - t) * 0.35 +
                        (_isActive ? 0.0 : 0.08);
                    return Container(
                      width: radius * 2,
                      height: radius * 2,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: discColor.withValues(alpha: opacity),
                          width: 2,
                        ),
                      ),
                    );
                  }),
                );
              },
            ),

            // ── Subtle idle breathing glow ────────────────────────────────────
            AnimatedContainer(
              duration: const Duration(milliseconds: 600),
              width: disc,
              height: disc,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: discColor.withValues(alpha: 0.12),
                boxShadow: [
                  BoxShadow(
                    color: discColor.withValues(alpha: _isActive ? 0.25 : 0.15),
                    blurRadius: _isActive ? 40 : 24,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: Center(
                child: Container(
                  width: disc * 0.86,
                  height: disc * 0.86,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: SamudraColors.backgroundCard,
                    border: Border.all(
                      color: discColor.withValues(alpha: 0.5),
                      width: 2,
                    ),
                  ),
                  child: ClipOval(
                    child: Image.asset(
                      'assets/images/samudra_logo.png',
                      fit: BoxFit.contain,
                      errorBuilder: (ctx, e, s) => Icon(
                        Icons.waves,
                        color: SamudraColors.accentCyan,
                        size: disc * 0.5,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            // ── State icon overlay (microphone / speaker / …) ────────────────
            Positioned(
              bottom: disc * 0.32,
              child: Container(
                width: disc * 0.34,
                height: disc * 0.34,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: iconColor.withValues(alpha: 0.2),
                  border: Border.all(
                    color: iconColor.withValues(alpha: 0.5),
                    width: 1.5,
                  ),
                ),
                child: Icon(icon, size: disc * 0.2, color: iconColor),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _discColor(AgentVoiceState state) {
    switch (state) {
      case AgentVoiceState.listening:
        return SamudraColors.statusDanger;
      case AgentVoiceState.thinking:
        return SamudraColors.accentBlue;
      case AgentVoiceState.speaking:
        return SamudraColors.accentCyan;
      case AgentVoiceState.idle:
        return SamudraColors.accentCyan;
    }
  }

  Color _iconColor(AgentVoiceState state) {
    switch (state) {
      case AgentVoiceState.listening:
        return SamudraColors.statusDanger;
      case AgentVoiceState.thinking:
        return SamudraColors.accentBlue;
      case AgentVoiceState.speaking:
        return SamudraColors.accentCyan;
      case AgentVoiceState.idle:
        return SamudraColors.accentCyan;
    }
  }

  IconData _stateIcon(AgentVoiceState state) {
    switch (state) {
      case AgentVoiceState.listening:
        return Icons.mic;
      case AgentVoiceState.thinking:
        return Icons.more_horiz;
      case AgentVoiceState.speaking:
        return Icons.volume_up;
      case AgentVoiceState.idle:
        return Icons.mic_none;
    }
  }
}
