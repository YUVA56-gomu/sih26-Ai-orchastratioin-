import 'package:flutter/material.dart';
import '../app/theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// AskSamudra — the primary AI input bar shown on HomeScreen.
//
// [onSubmit] is called with the trimmed query text when the user taps Send.
// [onMicTap] is called when the microphone icon is tapped. It is a navigation
// trigger (open the Assistant) — this widget does NOT do speech-to-text.
// When null (default) the button remains visible but non-functional —
// backward-compatible with any call site that doesn't wire the callback.
// ─────────────────────────────────────────────────────────────────────────────

class AskSamudra extends StatefulWidget {
  /// Called with the trimmed query text when the user submits.
  /// If null the send button does nothing.
  final void Function(String query)? onSubmit;

  /// Called when the microphone (voice) icon is tapped. Use this to navigate
  /// to the Assistant — no audio capability is enabled here.
  final VoidCallback? onMicTap;

  const AskSamudra({super.key, this.onSubmit, this.onMicTap});

  @override
  State<AskSamudra> createState() => _AskSamudraState();
}

class _AskSamudraState extends State<AskSamudra> {
  final TextEditingController _controller = TextEditingController();
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onChanged);
  }

  void _onChanged() {
    final hasText = _controller.text.trim().isNotEmpty;
    if (hasText != _hasText) setState(() => _hasText = hasText);
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    widget.onSubmit?.call(text);
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: SamudraColors.backgroundCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: SamudraColors.borderSubtle),
        boxShadow: [
          BoxShadow(
            color: SamudraColors.accentCyanGlow,
            blurRadius: 20,
            spreadRadius: 0,
          ),
        ],
      ),
      child: Column(
        children: [
          // ── Text field ────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 8, 0),
            child: TextField(
              controller: _controller,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: SamudraColors.textPrimary,
                    fontSize: 15,
                  ),
              decoration: const InputDecoration(
                hintText: 'Ask Samudra AI...',
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                contentPadding: EdgeInsets.zero,
                isDense: true,
                filled: false,
              ),
              maxLines: 4,
              minLines: 1,
              textInputAction: TextInputAction.newline,
              keyboardType: TextInputType.multiline,
              onSubmitted: (_) => _submit(),
            ),
          ),

          // ── Action row ────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Mic (navigation trigger → Assistant; no STT in this task)
                _InputIconButton(
                  icon: Icons.mic_outlined,
                  tooltip: 'Voice input',
                  onTap: widget.onMicTap,
                ),
                // Send
                _SendButton(
                  active: _hasText,
                  onTap: _hasText ? _submit : null,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InputIconButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;

  const _InputIconButton({
    required this.icon,
    required this.tooltip,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Icon(icon, size: 20, color: SamudraColors.textSecondary),
        ),
      ),
    );
  }
}

class _SendButton extends StatelessWidget {
  final bool active;
  final VoidCallback? onTap;

  const _SendButton({required this.active, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: active ? SamudraColors.accentCyan : SamudraColors.borderSubtle,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(
          Icons.arrow_upward_rounded,
          size: 18,
          color:
              active ? SamudraColors.backgroundDark : SamudraColors.textMuted,
        ),
      ),
    );
  }
}
