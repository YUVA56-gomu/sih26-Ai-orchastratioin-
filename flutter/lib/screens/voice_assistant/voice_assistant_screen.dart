import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../services/conversation/conversation_service.dart';
import '../../services/speech/speech_service.dart';
import '../../services/speech/speech_synthesis_service.dart';
import '../../widgets/agent_voice_orb.dart';

/// VoiceAssistantScreen — the dedicated voice-first Samudra AI dashboard.
///
/// Design:
///   • A large centred [AgentVoiceOrb] (logo + animated rounded speech waves).
///   • You *speak* your query (spoken → text via [SpeechService]).
///   • The backend reply is spoken back (text-to-speech via
///     [SpeechSynthesisService]) **and** shown as a compact transcript.
///   • No text input field — queries are voice-only.
///
/// It is decoupled from the backend: it talks only to
/// [ConversationService.instance.sendMessage]. It reuses [SpeechService]
/// (speech-to-text + microphone permission) and [SpeechSynthesisService]
/// (text-to-speech).
///
/// [pendingQuery] is used when the caller has already transcribed a phrase
/// (e.g. the Map search-bar mic): the screen skips listening and immediately
/// sends + speaks it. Otherwise it auto-starts listening on open.
class VoiceAssistantScreen extends StatefulWidget {
  const VoiceAssistantScreen({super.key, this.pendingQuery});

  /// A pre-transcribed query to send+speak immediately (no listening).
  final String? pendingQuery;

  @override
  State<VoiceAssistantScreen> createState() => _VoiceAssistantScreenState();
}

class _VoiceAssistantScreenState extends State<VoiceAssistantScreen> {
  AgentVoiceState _state = AgentVoiceState.idle;
  String? _userLast;
  String? _assistantLast;
  String? _errorText;
  bool _busy = false;

  static const _greeting =
      'Hi, I\u2019m Samudra AI. Tap the orb and ask about sea conditions, '
      'fishing zones or safety.';

  @override
  void initState() {
    super.initState();
    // Wire the TTS callbacks so the orb reflects "speaking" state and returns
    // to idle when the utterance completes.
    final tts = SpeechSynthesisService.instance;
    tts.onStart = () {
      if (mounted) setState(() => _state = AgentVoiceState.speaking);
    };
    tts.onComplete = () {
      if (mounted) setState(() => _state = AgentVoiceState.idle);
    };
    tts.onError = (message) {
      if (mounted) {
        setState(() {
          _state = AgentVoiceState.idle;
          _errorText = message;
        });
      }
    };

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final pending = widget.pendingQuery?.trim() ?? '';
      if (pending.isNotEmpty) {
        _sendQuery(pending);
      } else {
        _startListening();
      }
    });
  }

  @override
  void dispose() {
    // Detach TTS callbacks and stop anything in flight when the screen closes.
    final tts = SpeechSynthesisService.instance;
    tts.onStart = null;
    tts.onComplete = null;
    tts.onError = null;
    SpeechService.instance.stop();
    SpeechSynthesisService.instance.stop();
    super.dispose();
  }

  // ── Entry points ───────────────────────────────────────────────────────────

  /// Called by the orb tap. Behaviour depends on the current state.
  void _onOrbTap() {
    switch (_state) {
      case AgentVoiceState.idle:
        _startListening();
        break;
      case AgentVoiceState.listening:
        _cancelListening();
        break;
      case AgentVoiceState.speaking:
        _stopSpeaking();
        break;
      case AgentVoiceState.thinking:
        // In-flight request — don't interrupt. Ignore the tap.
        break;
    }
  }

  // ── Speech-to-text ─────────────────────────────────────────────────────────

  Future<void> _startListening() async {
    if (_busy) return;
    _busy = true;
    setState(() => _errorText = null);

    // 1. Microphone permission.
    final permission = await SpeechService.instance.resolveMicrophonePermission();
    if (!mounted) return;
    switch (permission) {
      case MicPermission.permanentlyDenied:
        _setIdle(
          'Microphone permission is disabled. Enable it in system settings to '
          'use voice input.',
        );
        return;
      case MicPermission.denied:
        _setIdle('Microphone permission is needed for voice input.');
        return;
      case MicPermission.granted:
        break;
    }

    // 2. Recogniser availability.
    final available = await SpeechService.instance.initialize();
    if (!mounted) return;
    if (!available) {
      _setIdle('Voice input isn\u2019t available on this device.');
      return;
    }

    // 3. Start listening.
    setState(() => _state = AgentVoiceState.listening);
    _busy = false;
    await SpeechService.instance.startListening(
      onResult: _onSpeechResult,
      onError: _onSpeechError,
      onEnded: _onListeningEnded,
    );
  }

  /// Fired when the recogniser stops without producing a result (user was
  /// silent, or the engine timed out). Only returns to idle if we're still
  /// "listening" — after a successful result the state is already thinking.
  void _onListeningEnded() {
    if (!mounted) return;
    if (_state == AgentVoiceState.listening) {
      _setIdle('I didn\u2019t catch that. Tap the orb and speak again.');
    }
  }

  void _onSpeechResult(String text) {
    final query = text.trim();
    SpeechService.instance.stop();
    if (query.isEmpty) {
      _setIdle('I didn\u2019t catch that. Tap the orb and try again.');
      return;
    }
    _sendQuery(query);
  }

  void _onSpeechError(String message) {
    _setIdle(message);
  }

  void _cancelListening() {
    SpeechService.instance.stop();
    _setIdle('Voice input cancelled.');
  }

  // ── Ask the backend + speak the reply ──────────────────────────────────────

  Future<void> _sendQuery(String text) async {
    final query = text.trim();
    if (query.isEmpty || _busy) return;
    _busy = true;
    setState(() {
      _state = AgentVoiceState.thinking;
      _userLast = query;
      _assistantLast = null;
      _errorText = null;
    });

    try {
      final reply =
          await ConversationService.instance.sendMessage(query);
      if (!mounted) return;
      setState(() {
        _assistantLast = reply;
        _state = AgentVoiceState.speaking;
      });
      _busy = false;
      // Spoken aloud; [SpeechSynthesisService.onComplete] returns us to idle.
      await SpeechSynthesisService.instance.speak(reply);
    } on ConversationException catch (e) {
      if (!mounted) return;
      setState(() {
        _state = AgentVoiceState.idle;
        _errorText = e.message;
      });
      _busy = false;
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _state = AgentVoiceState.idle;
        _errorText = 'I\u2019m having trouble connecting right now. '
            'Please try again in a moment.';
      });
      _busy = false;
    }
  }

  void _stopSpeaking() {
    SpeechSynthesisService.instance.stop();
    _setIdle(null);
  }

  void _setIdle(String? error) {
    if (!mounted) return;
    setState(() {
      _state = AgentVoiceState.idle;
      _errorText = error;
      _busy = false;
    });
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  String get _stateLabel {
    switch (_state) {
      case AgentVoiceState.idle:
        return 'Tap the orb to speak';
      case AgentVoiceState.listening:
        return 'Listening… speak now';
      case AgentVoiceState.thinking:
        return 'Samudra AI is thinking…';
      case AgentVoiceState.speaking:
        return 'Samudra AI is speaking…';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: AppBar(
        backgroundColor: SamudraColors.backgroundDark,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: SamudraColors.textSecondary),
          tooltip: 'Back',
          onPressed: () => Navigator.pop(context),
        ),
        title: const _AppBarTitle(),
        centerTitle: true,
      ),
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            // Viewport-filling Column (NOT a scroll view) so the orb block gets
            // a bounded height. The orb + label sit in an Expanded (centred in
            // the space *above* the transcript) and the transcript is pinned to
            // the bottom — so adding/clearing input never shifts the orb.
            return Column(
              children: [
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // ── Central orb ──────────────────────────────────────
                      AgentVoiceOrb(
                        state: _state,
                        size: 260,
                        onTap: _onOrbTap,
                      ),
                      const SizedBox(height: 28),

                      // ── State label ──────────────────────────────────────
                      Text(
                        _stateLabel,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(
                              color: SamudraColors.textPrimary,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                      const SizedBox(height: 12),

                      // ── Hint / error ─────────────────────────────────────
                      _HintOrError(error: _errorText, hint: _greeting),
                    ],
                  ),
                ),

                // ── Compact transcript (anchored to the bottom) ────────────
                ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: constraints.maxHeight * 0.45,
                  ),
                  child: _TranscriptCard(
                    user: _userLast,
                    assistant: _assistantLast,
                  ),
                ),
                const SizedBox(height: 16),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _AppBarTitle extends StatelessWidget {
  const _AppBarTitle();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 22,
          height: 22,
          child: Image.asset(
            'assets/images/samudra_logo.png',
            fit: BoxFit.contain,
            errorBuilder: (ctx, e, s) => const Icon(
              Icons.waves,
              color: SamudraColors.accentCyan,
              size: 18,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          'Samudra AI Voice',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: SamudraColors.textPrimary,
              ),
        ),
      ],
    );
  }
}

class _HintOrError extends StatelessWidget {
  const _HintOrError({required this.error, required this.hint});

  final String? error;
  final String hint;

  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Text(
          error!,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: SamudraColors.statusDanger,
                fontWeight: FontWeight.w500,
              ),
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Text(
        hint,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: SamudraColors.textMuted,
            ),
      ),
    );
  }
}

/// Compact, read-only record of the last user query and the spoken reply.
/// Always shown so the user can read what was said (fallback if TTS fails).
class _TranscriptCard extends StatelessWidget {
  const _TranscriptCard({required this.user, required this.assistant});

  final String? user;
  final String? assistant;

  @override
  Widget build(BuildContext context) {
    final hasAny = (user != null && user!.isNotEmpty) ||
        (assistant != null && assistant!.isNotEmpty);
    if (!hasAny) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 20),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: SamudraColors.borderSubtle),
      ),
      // Scroll internally so a long reply doesn't push the card beyond the
      // (capped) height and shift the orb above it.
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (user != null && user!.isNotEmpty) ...[
              _TranscriptLine(label: 'You', text: user!, isUser: true),
              if (assistant != null && assistant!.isNotEmpty)
                const SizedBox(height: 8),
            ],
            if (assistant != null && assistant!.isNotEmpty)
              _TranscriptLine(
                label: 'Samudra',
                text: assistant!,
                isUser: false,
              ),
          ],
        ),
      ),
    );
  }
}

class _TranscriptLine extends StatelessWidget {
  const _TranscriptLine({
    required this.label,
    required this.text,
    required this.isUser,
  });

  final String label;
  final String text;
  final bool isUser;

  @override
  Widget build(BuildContext context) {
    final color = isUser ? SamudraColors.accentCyan : SamudraColors.textPrimary;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 6,
          height: 6,
          margin: const EdgeInsets.only(top: 7, right: 8),
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: SamudraColors.textMuted,
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 2),
              Text(
                text,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: color,
                      fontSize: 14,
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
