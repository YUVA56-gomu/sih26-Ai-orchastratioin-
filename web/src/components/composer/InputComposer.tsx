import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Mic, Sparkles } from 'lucide-react';

interface InputComposerProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isLoading: boolean;
}

export const InputComposer: React.FC<InputComposerProps> = ({ onSend, onStop, isLoading }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 pt-2">
      <form
        onSubmit={handleSubmit}
        className="relative rounded-2xl p-2.5 bg-ocean-900/90 border border-slate-800 focus-within:border-cyan-500/50 shadow-2xl transition-all backdrop-blur-lg"
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask SAMUDRA AI about ocean conditions, weather forecasts, fishing zones, or marine routes..."
          rows={1}
          className="w-full bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none resize-none max-h-40 scrollbar-thin"
        />

        <div className="flex items-center justify-between px-2 pt-1 border-t border-slate-800/40 mt-1">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-400">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for newline</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Voice microphone button integration point */}
            <button
              type="button"
              className="p-2 rounded-xl text-slate-400 hover:text-cyan-400 hover:bg-ocean-800 transition-colors"
              title="Voice input (Microphone integration point)"
            >
              <Mic className="w-4 h-4" />
            </button>

            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="py-2 px-3 rounded-xl bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30 transition-colors flex items-center gap-1.5 text-xs font-semibold"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!text.trim()}
                className="p-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:from-blue-500 hover:to-cyan-500 shadow-md transition-all flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

