import 'package:flutter/material.dart';

import '../app/theme.dart';
import '../services/speech/speech_service.dart';

/// A self-contained microphone button for the search bars.
///
/// Behaviour:
///   • idle: a plain mic icon.
///   • tap: resolves microphone permission, initialises the recogniser and
///          starts listening (shows a pulsing red mic + "Listening…").
///   • listening tap: cancels recognition (no query is sent).
///   • recognised: calls [onText] with the transcribed text.
///
/// All permission / availability / error handling is encapsulated here and
/// surfaced as friendly SnackBars — the app never crashes on a voice failure.
///
/// It depends only on [SpeechService.instance] (a settable singleton), so
/// widget tests can inject a fake instead of touching the real recogniser.
class VoiceInputButton extends StatefulWidget {
  /// Called with the fully transcribed phrase when recognition finishes.
  final void Function(String text) onText;

  /// Notifies the parent when listening starts/stops so it can update
  /// placeholder text ("Listening…") in the search bar.
  final ValueChanged<bool>? onListeningChanged;

  /// Icon colour when idle. Defaults to the muted secondary text colour.
  final Color? idleColor;

  /// Icon colour while listening. Defaults to the danger/red status colour.
  final Color? listeningColor;

  const VoiceInputButton({
    super.key,
    required this.onText,
    this.onListeningChanged,
    this.idleColor,
    this.listeningColor,
  });

  @override
  State<VoiceInputButton> createState() => _VoiceInputButtonState();
}

class _VoiceInputButtonState extends State<VoiceInputButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;

  /// True while requesting permission / initialising the recogniser.
  bool _busy = false;

  /// True while capturing audio.
  bool _listening = false;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 850),
    );
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  void _setListening(bool value) {
    if (_listening == value) return;
    if (value) {
      if (!_pulse.isAnimating) _pulse.repeat(reverse: true);
    } else {
      _pulse.stop();
      _pulse.value = 0;
    }
    setState(() => _listening = value);
    widget.onListeningChanged?.call(value);
  }

  Future<void> _handleTap() async {
    if (_busy) return;

    // Cancel path — tap while listening.
    if (_listening) {
      await SpeechService.instance.cancel();
      _setListening(false);
      _showSnack('Voice input cancelled.');
      return;
    }

    _busy = true;
    if (mounted) setState(() {});

    // 1. Microphone permission.
    final permission =
        await SpeechService.instance.resolveMicrophonePermission();
    switch (permission) {
      case MicPermission.permanentlyDenied:
        _setBusyDone();
        _showSnack(
          'Microphone permission is disabled. Enable it in system settings to '
          'use voice input.',
          openSettings: true,
        );
        return;
      case MicPermission.denied:
        _setBusyDone();
        _showSnack('Microphone permission is needed for voice input.');
        return;
      case MicPermission.granted:
        break;
    }

    // 2. Recogniser availability.
    final available = await SpeechService.instance.initialize();
    if (!available) {
      _setBusyDone();
      _showSnack('Voice input isn\u2019t available on this device.');
      return;
    }

    // 3. Start listening.
    _setListening(true);
    if (mounted) setState(() => _busy = false);

    await SpeechService.instance.startListening(
      onResult: _onResult,
      onError: _onError,
    );
  }

  void _setBusyDone() {
    if (mounted) setState(() => _busy = false);
  }

  void _onResult(String text) {
    // Stop the recogniser and hand the text over. No further UI state needed —
    // the parent navigates to the Assistant.
    SpeechService.instance.stop();
    _setListening(false);
    widget.onText(text);
  }

  void _onError(String message) {
    _setListening(false);
    _showSnack(message);
  }

  void _showSnack(String message, {bool openSettings = false}) {
    if (!mounted) return;
    final messenger = ScaffoldMessenger.maybeOf(context);
    if (messenger == null) return;
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          behavior: SnackBarBehavior.floating,
          backgroundColor: SamudraColors.backgroundCard,
          content: Row(
            children: [
              Icon(
                openSettings ? Icons.settings : Icons.info_outline,
                color: SamudraColors.accentCyan,
                size: 18,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  message,
                  style: TextStyle(color: SamudraColors.textPrimary),
                ),
              ),
              if (openSettings)
                TextButton(
                  onPressed: () {
                    SpeechService.instance.openSettings();
                    messenger.hideCurrentSnackBar();
                  },
                  child: const Text('Open settings'),
                ),
            ],
          ),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final listening = _listening;
    final idleColor = widget.idleColor ?? SamudraColors.textSecondary;

    return Tooltip(
      message: listening ? 'Stop listening' : 'Voice input',
      child: InkWell(
        onTap: _handleTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: AnimatedBuilder(
            animation: _pulse,
            builder: (ctx, child) {
              if (listening) {
                final glow = 0.35 + 0.65 * _pulse.value;
                return Container(
                  width: 22,
                  height: 22,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: SamudraColors.statusDanger
                        .withValues(alpha: 0.15 + 0.35 * glow),
                    boxShadow: [
                      BoxShadow(
                        color: SamudraColors.statusDanger
                            .withValues(alpha: glow),
                        blurRadius: 8 * glow,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.mic,
                    size: 14,
                    color: SamudraColors.statusDanger,
                  ),
                );
              }
              return Icon(Icons.mic_outlined, size: 22, color: idleColor);
            },
          ),
        ),
      ),
    );
  }
}
