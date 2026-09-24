import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../models/conversation/conversation_message.dart';
import '../../services/conversation/backend_conversation_service.dart';
import '../../services/conversation/conversation_service.dart';
import '../../widgets/agent_thinking_card.dart';
import '../../widgets/artifacts/artifact_renderer.dart';
import '../../widgets/samudra_drawer.dart';
import '../../widgets/voice_input_button.dart';

class AssistantScreen extends StatefulWidget {
  final bool embedded;
  final String? initialQuery;
  final String? initialConversationId;

  const AssistantScreen({
    super.key,
    this.embedded = false,
    this.initialQuery,
    this.initialConversationId,
  });

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  static const String _greeting =
      'Hi there! How can I help you today?\n'
      'Ask me about sea conditions, fishing zones or safety.';

  final List<ConversationMessage> _messages = [];
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  bool _hasText = false;
  bool _listening = false;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    _inputController.addListener(_onTextChanged);
    _messages.add(ConversationMessage.assistant(_greeting));

    if (widget.initialConversationId != null) {
      _loadSpecificConversation(widget.initialConversationId!);
    } else {
      _loadHistory();
    }

    if (widget.initialQuery != null && widget.initialQuery!.trim().isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _submit(widget.initialQuery!.trim());
      });
    }
  }

  Future<void> _loadHistory() async {
    if (widget.initialQuery != null) return;
    final service = ConversationService.instance;
    if (service is! ConversationHistoryProvider) return;
    final provider = service as ConversationHistoryProvider;
    try {
      final history = await provider.loadHistory();
      if (!mounted) return;
      setState(() {
        _messages.clear();
        _messages.addAll(history.isEmpty
            ? [ConversationMessage.assistant(_greeting)]
            : history);
      });
      _scrollToBottom();
    } catch (_) {
      if (!mounted) return;
      if (_messages.isEmpty) {
        setState(() => _messages.add(ConversationMessage.assistant(_greeting)));
      }
    }
  }

  Future<void> _loadSpecificConversation(String conversationId) async {
    final service = ConversationService.instance;
    if (service is BackendConversationService) {
      try {
        setState(() => _isLoading = true);
        final history = await service.loadHistoryFor(conversationId);
        if (!mounted) return;
        setState(() {
          _messages.clear();
          _messages.addAll(history.isEmpty
              ? [ConversationMessage.assistant(_greeting)]
              : history);
          _isLoading = false;
        });
        _scrollToBottom();
      } catch (_) {
        if (!mounted) return;
        setState(() => _isLoading = false);
      }
    }
  }

  void _startNewChat() {
    final service = ConversationService.instance;
    if (service is BackendConversationService) {
      service.newConversation();
    }
    setState(() {
      _messages.clear();
      _messages.add(ConversationMessage.assistant(_greeting));
      _errorText = null;
    });
  }

  void _onTextChanged() {
    final hasText = _inputController.text.trim().isNotEmpty;
    if (hasText != _hasText) setState(() => _hasText = hasText);
  }

  @override
  void dispose() {
    _inputController.removeListener(_onTextChanged);
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _submit(String text) async {
    final query = text.trim();
    if (query.isEmpty || _isLoading) return;

    setState(() {
      _messages.add(ConversationMessage.user(query));
      _isLoading = true;
      _errorText = null;
    });
    _inputController.clear();
    _scrollToBottom();

    try {
      final service = ConversationService.instance;
      ConversationMessage reply;
      if (service is BackendConversationService) {
        reply = await service.sendStructuredMessage(query);
      } else {
        final textReply = await service.sendMessage(query);
        reply = ConversationMessage.assistant(textReply);
      }

      if (!mounted) return;
      setState(() {
        _messages.add(reply);
        _isLoading = false;
      });
    } on ConversationException catch (e) {
      if (!mounted) return;
      setState(() {
        _errorText = e.message;
        _isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _errorText = 'I\u2019m having trouble connecting right now. '
            'Please try again in a moment.';
        _isLoading = false;
      });
    }

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SamudraColors.backgroundDark,
      appBar: widget.embedded ? null : _buildAppBar(context),
      drawer: widget.embedded
          ? null
          : SamudraDrawer(
              onSelectConversation: _loadSpecificConversation,
              onNewChat: _startNewChat,
            ),
      body: Column(
        children: [
          if (widget.embedded)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              child: Row(
                children: [
                  Text(
                    'Assistant',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.add_comment_outlined, color: SamudraColors.accentCyan),
                    onPressed: _startNewChat,
                    tooltip: 'New Conversation',
                  ),
                ],
              ),
            ),

          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
              itemCount: _messages.length,
              itemBuilder: (ctx, i) => _MessageBubble(message: _messages[i]),
            ),
          ),

          if (_errorText != null)
            _ErrorBanner(
              text: _errorText!,
              onDismiss: () => setState(() => _errorText = null),
            ),

          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: AgentThinkingCard(
                agentSteps: [],
                isThinking: true,
              ),
            ),

          _InputBar(
            controller: _inputController,
            hasText: _hasText,
            isLoading: _isLoading,
            listening: _listening,
            onSubmit: _submit,
            onVoiceText: (text) {
              _inputController.text = text;
              _submit(text);
            },
            onListeningChanged: (listening) {
              if (mounted) setState(() => _listening = listening);
            },
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      backgroundColor: SamudraColors.backgroundDark,
      leading: Builder(
        builder: (ctx) => IconButton(
          icon: const Icon(Icons.menu, color: SamudraColors.textSecondary),
          onPressed: () => Scaffold.of(ctx).openDrawer(),
        ),
      ),
      title: const _AppBarTitle(),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.add, color: SamudraColors.accentCyan),
          onPressed: _startNewChat,
          tooltip: 'New Chat',
        ),
      ],
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
            errorBuilder: (ctx, e, s) =>
                const Icon(Icons.waves, color: SamudraColors.accentCyan, size: 18),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          'Samudra AI',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontSize: 17,
                fontWeight: FontWeight.w700,
              ),
        ),
      ],
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final ConversationMessage message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    switch (message.role) {
      case MessageRole.user:
        return _UserBubble(text: message.text);
      case MessageRole.assistant:
        return _AssistantBubble(message: message);
    }
  }
}

class _UserBubble extends StatelessWidget {
  final String text;
  const _UserBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(width: 48),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: SamudraColors.accentCyan.withValues(alpha: 0.15),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(4),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
                border: Border.all(
                  color: SamudraColors.accentCyan.withValues(alpha: 0.3),
                ),
              ),
              child: Text(
                text,
                style: Theme.of(context)
                    .textTheme
                    .bodyLarge
                    ?.copyWith(color: SamudraColors.textPrimary),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AssistantBubble extends StatelessWidget {
  final ConversationMessage message;
  const _AssistantBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final artifacts = message.artifacts ?? [];
    final agentSteps = message.agentSteps ?? [];

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: SamudraColors.accentCyan.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: ClipOval(
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Image.asset(
                  'assets/images/samudra_logo.png',
                  fit: BoxFit.contain,
                  errorBuilder: (ctx, e, s) => const Icon(
                    Icons.waves,
                    size: 16,
                    color: SamudraColors.accentCyan,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Agent execution trace dropdown
                if (agentSteps.isNotEmpty)
                  AgentThinkingCard(agentSteps: agentSteps),

                // Assistant response bubble
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: SamudraColors.backgroundCard,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(4),
                      topRight: Radius.circular(16),
                      bottomLeft: Radius.circular(16),
                      bottomRight: Radius.circular(16),
                    ),
                    border: Border.all(color: SamudraColors.borderSubtle),
                  ),
                  child: Text(
                    message.text,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: SamudraColors.textPrimary,
                          height: 1.5,
                        ),
                  ),
                ),

                // Turn-specific artifacts rendered directly under this turn
                if (artifacts.isNotEmpty)
                  ...artifacts.map((art) => ArtifactRenderer(artifact: art)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String text;
  final VoidCallback? onDismiss;

  const _ErrorBanner({required this.text, this.onDismiss});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: SamudraColors.statusDanger.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.error_outline,
              size: 16,
              color: SamudraColors.statusDanger,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: SamudraColors.statusDanger.withValues(alpha: 0.08),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(4),
                  topRight: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
                border: Border.all(
                    color: SamudraColors.statusDanger.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      text,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: SamudraColors.statusDanger,
                          ),
                    ),
                  ),
                  if (onDismiss != null)
                    InkWell(
                      onTap: onDismiss,
                      child: const Padding(
                        padding: EdgeInsets.only(left: 8),
                        child: Icon(
                          Icons.close,
                          size: 16,
                          color: SamudraColors.statusDanger,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool hasText;
  final bool isLoading;
  final bool listening;
  final void Function(String) onSubmit;
  final void Function(String) onVoiceText;
  final void Function(bool) onListeningChanged;

  const _InputBar({
    required this.controller,
    required this.hasText,
    required this.isLoading,
    required this.listening,
    required this.onSubmit,
    required this.onVoiceText,
    required this.onListeningChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 0),
      child: Container(
        decoration: BoxDecoration(
          color: SamudraColors.backgroundCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: listening ? SamudraColors.statusDanger : SamudraColors.borderSubtle,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                enabled: !isLoading,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: SamudraColors.textPrimary,
                      fontSize: 15,
                    ),
                decoration: InputDecoration(
                  hintText: listening ? 'Listening... speak now' : 'Ask Samudra AI...',
                  hintStyle: TextStyle(
                    color: listening ? SamudraColors.statusDanger : SamudraColors.textMuted,
                  ),
                  border: InputBorder.none,
                  enabledBorder: InputBorder.none,
                  focusedBorder: InputBorder.none,
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  isDense: true,
                  filled: false,
                ),
                maxLines: 4,
                minLines: 1,
                keyboardType: TextInputType.multiline,
                textInputAction: TextInputAction.newline,
                onSubmitted: (_) {
                  final t = controller.text.trim();
                  if (t.isNotEmpty && !isLoading) onSubmit(t);
                },
              ),
            ),

            // Microphone button
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: VoiceInputButton(
                onText: onVoiceText,
                onListeningChanged: onListeningChanged,
              ),
            ),

            // Send button
            Padding(
              padding: const EdgeInsets.all(8),
              child: isLoading
                  ? const SizedBox(
                      width: 36,
                      height: 36,
                      child: Center(
                        child: SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: SamudraColors.accentCyan,
                          ),
                        ),
                      ),
                    )
                  : GestureDetector(
                      onTap: hasText ? () => onSubmit(controller.text.trim()) : null,
                      child: Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: hasText
                              ? SamudraColors.accentCyan
                              : SamudraColors.borderSubtle,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          Icons.arrow_upward_rounded,
                          size: 18,
                          color: hasText
                              ? SamudraColors.backgroundDark
                              : SamudraColors.textMuted,
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
