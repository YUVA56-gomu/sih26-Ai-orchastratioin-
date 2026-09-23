import React, { useState } from 'react';
import { Logo } from '../brand/Logo';
import {
  Plus,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Compass,
  Search,
  MoreVertical,
  Edit2,
  Trash2,
  Check,
  X,
  User,
} from 'lucide-react';
import { ConversationSummary } from '../../api/types';

interface SidebarProps {
  conversations: ConversationSummary[];
  activeConvId?: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onDeleteConversation: (id: string) => void;
  onSearchChange?: (query: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

function groupConversationsByDate(conversations: ConversationSummary[]) {
  const today: ConversationSummary[] = [];
  const yesterday: ConversationSummary[] = [];
  const last7Days: ConversationSummary[] = [];
  const older: ConversationSummary[] = [];

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 86400000;
  const startOf7Days = startOfToday - 6 * 86400000;

  conversations.forEach((conv) => {
    const updated = new Date(conv.updated_at).getTime();
    if (isNaN(updated) || updated >= startOfToday) {
      today.push(conv);
    } else if (updated >= startOfYesterday) {
      yesterday.push(conv);
    } else if (updated >= startOf7Days) {
      last7Days.push(conv);
    } else {
      older.push(conv);
    }
  });

  return { today, yesterday, last7Days, older };
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations = [],
  activeConvId,
  onSelectConversation,
  onNewChat,
  onRenameConversation,
  onDeleteConversation,
  onSearchChange,
  isCollapsed,
  onToggleCollapse,
}) => {
  const [filter, setFilter] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleSearch = (val: string) => {
    setFilter(val);
    if (onSearchChange) {
      onSearchChange(val);
    }
  };

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(filter.toLowerCase())
  );

  const grouped = groupConversationsByDate(filtered);

  const startRename = (conv: ConversationSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.conversation_id);
    setEditTitle(conv.title);
    setMenuOpenId(null);
  };

  const saveRename = (id: string, e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (editTitle.trim()) {
      onRenameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const cancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const startDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmDeleteId(id);
    setMenuOpenId(null);
  };

  const executeDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onDeleteConversation(id);
    setConfirmDeleteId(null);
  };

  const renderGroup = (label: string, items: ConversationSummary[]) => {
    if (items.length === 0) return null;

    return (
      <div key={label} className="mb-4">
        {!isCollapsed && (
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {label}
          </div>
        )}
        <div className="space-y-0.5">
          {items.map((conv) => {
            const isActive = conv.conversation_id === activeConvId;
            const isEditing = editingId === conv.conversation_id;
            const isConfirmingDelete = confirmDeleteId === conv.conversation_id;
            const isMenuOpen = menuOpenId === conv.conversation_id;

            if (isEditing) {
              return (
                <form
                  key={conv.conversation_id}
                  onSubmit={(e) => saveRename(conv.conversation_id, e)}
                  className="px-2 py-1 flex items-center gap-1.5 bg-ocean-800 rounded-xl border border-cyan-500/50"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    autoFocus
                    className="flex-1 bg-transparent text-xs text-white focus:outline-none px-1"
                  />
                  <button
                    type="submit"
                    className="p-1 text-emerald-400 hover:text-emerald-300 rounded"
                    title="Save"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={cancelRename}
                    className="p-1 text-slate-400 hover:text-slate-200 rounded"
                    title="Cancel"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </form>
              );
            }

            if (isConfirmingDelete) {
              return (
                <div
                  key={conv.conversation_id}
                  className="p-2 bg-rose-950/80 border border-rose-800 rounded-xl flex items-center justify-between gap-2 text-xs"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="text-rose-200 text-[11px] font-medium truncate">Delete conversation?</span>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={(e) => executeDelete(conv.conversation_id, e)}
                      className="px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-semibold text-[10px]"
                    >
                      Delete
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDeleteId(null);
                      }}
                      className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={conv.conversation_id}
                className="relative group"
              >
                <button
                  onClick={() => onSelectConversation(conv.conversation_id)}
                  className={`w-full p-2.5 rounded-xl text-left text-xs transition-all flex items-center gap-2.5 ${
                    isActive
                      ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-200 font-medium shadow-sm'
                      : 'text-slate-300 hover:bg-ocean-800/80 hover:text-slate-100'
                  } ${isCollapsed ? 'justify-center px-0' : 'pr-8'}`}
                  title={conv.title}
                >
                  <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  {!isCollapsed && <span className="truncate flex-1">{conv.title}</span>}
                </button>

                {/* Context Menu Trigger */}
                {!isCollapsed && (
                  <div className="absolute right-1.5 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpenId(isMenuOpen ? null : conv.conversation_id);
                      }}
                      className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-ocean-700/80"
                      title="Options"
                    >
                      <MoreVertical className="w-3.5 h-3.5" />
                    </button>

                    {/* Popover Dropdown */}
                    {isMenuOpen && (
                      <div
                        className="absolute right-0 top-6 w-36 bg-ocean-900 border border-slate-700/80 rounded-xl shadow-xl z-30 py-1 text-xs"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={(e) => startRename(conv, e)}
                          className="w-full px-3 py-1.5 text-left text-slate-300 hover:bg-ocean-800 hover:text-cyan-300 flex items-center gap-2"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-slate-400" />
                          <span>Rename</span>
                        </button>
                        <button
                          onClick={(e) => startDelete(conv.conversation_id, e)}
                          className="w-full px-3 py-1.5 text-left text-rose-400 hover:bg-rose-950/50 flex items-center gap-2 border-t border-slate-800/80 mt-0.5 pt-1.5"
                        >
                          <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                          <span>Delete</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <aside
      className={`h-full bg-ocean-900 border-r border-slate-800/80 flex flex-col transition-all duration-300 relative z-20 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        {!isCollapsed && <Logo variant="blue" size="md" showText={true} />}
        {isCollapsed && <Logo variant="blue" size="sm" showText={false} className="mx-auto" />}
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-ocean-800 transition-colors hidden sm:flex"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className={`w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 ${
            isCollapsed ? 'px-0' : ''
          }`}
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Search Input Bar */}
      {!isCollapsed && (
        <div className="px-3 mb-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={filter}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full bg-ocean-950 text-xs text-slate-200 pl-8 pr-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500/40 placeholder-slate-500"
            />
          </div>
        </div>
      )}

      {/* Conversation List Grouped by Date */}
      <div className="flex-1 overflow-y-auto px-2 scrollbar-thin">
        {filtered.length > 0 ? (
          <>
            {renderGroup('Today', grouped.today)}
            {renderGroup('Yesterday', grouped.yesterday)}
            {renderGroup('Previous 7 Days', grouped.last7Days)}
            {renderGroup('Older', grouped.older)}
          </>
        ) : (
          !isCollapsed && (
            <div className="p-6 text-center text-xs text-slate-500">
              {filter ? 'No matching conversations' : 'No conversations yet'}
            </div>
          )
        )}
      </div>

      {/* User / Account Footer Area */}
      {!isCollapsed && (
        <div className="p-3 border-t border-slate-800/80 bg-ocean-950/40 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-inner">
              <User className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-slate-200 text-xs">Marine Analyst</span>
              <span className="text-[10px] text-slate-400">SAMUDRA v1.0.0</span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
          </div>
        </div>
      )}
    </aside>
  );
};

