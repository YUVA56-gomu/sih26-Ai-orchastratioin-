import React, { useRef, useEffect } from 'react';
import { ChatMessageItem, ChatMessage } from './ChatMessageItem';
import { WelcomeScreen } from './WelcomeScreen';

interface ChatMessageListProps {
  messages: ChatMessage[];
  onQuickAction: (query: string) => void;
}

export const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages, onQuickAction }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!messages || messages.length === 0) {
    return <WelcomeScreen onQuickAction={onQuickAction} />;
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 max-w-4xl w-full mx-auto scrollbar-thin">
      {messages.map((msg) => (
        <ChatMessageItem key={msg.id} message={msg} onQuickAction={onQuickAction} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
