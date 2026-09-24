import React, { useState, useEffect } from 'react';
import { Sidebar } from '../sidebar/Sidebar';
import { ChatMessageList } from '../chat/ChatMessageList';
import { ChatMessage } from '../chat/ChatMessageItem';
import { InputComposer } from '../composer/InputComposer';
import { fetchConversations, fetchConversationDetail, renameConversation, deleteConversation } from '../../api/client';
import { startChatStream } from '../../api/sse';
import { ConversationSummary, Artifact, AgentStepPayload } from '../../api/types';
import { Logo } from '../brand/Logo';
import { Menu, X, ShieldAlert } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState<boolean>(false);

  const [userCoords, setUserCoords] = useState<{ lat: number; lon: number } | null>(null);

  // Request browser geolocation on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && 'geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserCoords({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
          });
        },
        (err) => {
          console.log('Browser geolocation notice:', err.message);
        },
        { timeout: 10000 }
      );
    }
  }, []);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async (searchQuery?: string) => {
    try {
      const list = await fetchConversations(searchQuery);
      setConversations(list);
    } catch (e) {
      console.warn('Failed to load conversation history:', e);
    }
  };

  const handleSelectConversation = async (convId: string) => {
    setActiveConvId(convId);
    setIsMobileSidebarOpen(false);
    try {
      const detail = await fetchConversationDetail(convId);
      const allArtifacts = detail.artifacts || [];

      // Intelligently associate artifacts with assistant messages based on turn topic
      const converted: ChatMessage[] = (detail.messages || []).map((m, idx) => {
        if (m.role !== 'assistant') {
          return {
            id: `msg_${idx}`,
            role: 'user',
            content: m.content,
            timestamp: m.timestamp,
          };
        }

        const textLower = (m.content || '').toLowerCase();
        const turnArtifacts = allArtifacts.filter((a) => {
          const type = (a.type || '').toLowerCase();
          if (type === 'weather_card' && (textLower.includes('weather') || textLower.includes('temp') || textLower.includes('wind'))) return true;
          if (type === 'pfz_map' && (textLower.includes('pfz') || textLower.includes('fish') || textLower.includes('zone'))) return true;
          if (type === 'ocean_card' && (textLower.includes('ocean') || textLower.includes('sst') || textLower.includes('current'))) return true;
          if (type === 'route_map' && (textLower.includes('route') || textLower.includes('path') || textLower.includes('navigate'))) return true;
          if (type === 'risk_summary' && (textLower.includes('safe') || textLower.includes('risk') || textLower.includes('level'))) return true;
          return false;
        });

        // If no specific topic matched or this is the last assistant message, attach unassigned artifacts
        const isLastAssistant = idx === detail.messages.length - 1 || idx === detail.messages.length - 2;
        const finalArtifacts = turnArtifacts.length > 0 ? turnArtifacts : (isLastAssistant ? allArtifacts : []);

        return {
          id: `msg_${idx}`,
          role: 'assistant',
          content: m.content,
          timestamp: m.timestamp,
          artifacts: finalArtifacts,
        };
      });

      setMessages(converted);
    } catch (e) {
      console.error('Failed to load conversation detail:', e);
    }
  };

  const handleNewChat = () => {
    if (activeStreamStop) activeStreamStop();
    setActiveConvId(undefined);
    setMessages([]);
    setIsLoading(false);
    setIsMobileSidebarOpen(false);
  };

  const handleRenameConversation = async (convId: string, newTitle: string) => {
    try {
      await renameConversation(convId, newTitle);
      await loadConversations();
    } catch (e) {
      console.error('Failed to rename conversation:', e);
    }
  };

  const handleDeleteConversation = async (convId: string) => {
    try {
      await deleteConversation(convId);
      if (activeConvId === convId) {
        handleNewChat();
      }
      await loadConversations();
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  };

  const handleSendMessage = (text: string) => {
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `assistant_${Date.now()}`;

    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      agentSteps: [],
      artifacts: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    const stepsMap: AgentStepPayload[] = [];
    let accumContent = '';
    const artifactsList: Artifact[] = [];

    const stopFn = startChatStream(
      text,
      activeConvId,
      userCoords?.lat,
      userCoords?.lon,
      {
      onStart: (data) => {
        if (!activeConvId) {
          setActiveConvId(data.conversation_id);
        }
      },
      onAgentStep: (step) => {
        const stepKey = step.id || step.node || step.label;
        if (!stepsMap.some((s) => (s.id || s.node || s.label) === stepKey)) {
          stepsMap.push(step);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, agentSteps: [...stepsMap] }
                : msg
            )
          );
        }
      },
      onArtifact: (art) => {
        if (!artifactsList.some((a) => a.id === art.id)) {
          artifactsList.push(art);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, artifacts: [...artifactsList] }
                : msg
            )
          );
        }
      },
      onResponseChunk: (chunk) => {
        if (chunk.content) {
          accumContent = chunk.content;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: accumContent }
                : msg
            )
          );
        }
      },
      onDone: (data) => {
        setIsLoading(false);
        setActiveStreamStop(null);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: data.response || accumContent,
                  artifacts: data.artifacts || artifactsList,
                  isStreaming: false,
                  riskLevel: data.risk_level,
                  riskScore: data.risk_score,
                }
              : msg
          )
        );
        loadConversations();
      },
      onError: (err) => {
        setIsLoading(false);
        setActiveStreamStop(null);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: `Error: ${err.error || 'Connection failed'}`,
                  isStreaming: false,
                }
              : msg
          )
        );
      },
    });

    setActiveStreamStop(() => stopFn);
  };

  const handleStopGeneration = () => {
    if (activeStreamStop) {
      activeStreamStop();
      setActiveStreamStop(null);
    }
    setIsLoading(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  };

  return (
    <div className="flex h-screen w-screen bg-ocean-950 text-slate-100 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      <div className="sm:hidden">
        {isMobileSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/60 z-30 backdrop-blur-sm"
            onClick={() => setIsMobileSidebarOpen(false)}
          />
        )}
        <div
          className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-300 ${
            isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <Sidebar
            conversations={conversations}
            activeConvId={activeConvId}
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
            onRenameConversation={handleRenameConversation}
            onDeleteConversation={handleDeleteConversation}
            onSearchChange={loadConversations}
            isCollapsed={false}
            onToggleCollapse={() => setIsMobileSidebarOpen(false)}
          />
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden sm:block">
        <Sidebar
          conversations={conversations}
          activeConvId={activeConvId}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          onRenameConversation={handleRenameConversation}
          onDeleteConversation={handleDeleteConversation}
          onSearchChange={loadConversations}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      </div>

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-ocean-950 relative">
        {/* Header Bar */}
        <header className="h-14 border-b border-slate-800/80 px-4 flex items-center justify-between bg-ocean-900/60 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              className="sm:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-200"
            >
              <Menu className="w-5 h-5" />
            </button>
            <Logo variant="blue" size="sm" showText={true} />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleNewChat}
              className="px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 border border-cyan-500/20 text-xs font-semibold transition-colors"
            >
              + New Chat
            </button>
          </div>
        </header>

        {/* Chat Message Stream Stage */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <ChatMessageList messages={messages} onQuickAction={handleSendMessage} />
        </div>

        {/* Composer Footer */}
        <InputComposer
          onSend={handleSendMessage}
          onStop={handleStopGeneration}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
