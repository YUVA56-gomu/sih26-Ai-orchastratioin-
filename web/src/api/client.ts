import { ChatRequest, ChatResponse, ConversationSummary, ConversationDetail } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Network response was not ok' }));
    throw new Error(errData.detail || `Server error ${res.status}`);
  }
  return res.json();
}

export async function fetchConversations(searchQuery?: string): Promise<ConversationSummary[]> {
  const url = searchQuery && searchQuery.trim() 
    ? `${API_BASE}/conversations?q=${encodeURIComponent(searchQuery.trim())}`
    : `${API_BASE}/conversations`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch conversations (${res.status})`);
  }
  return res.json();
}

export async function fetchConversationDetail(convId: string): Promise<ConversationDetail> {
  const res = await fetch(`${API_BASE}/conversations/${encodeURIComponent(convId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch conversation details (${res.status})`);
  }
  return res.json();
}

export async function renameConversation(convId: string, newTitle: string): Promise<ConversationSummary> {
  const res = await fetch(`${API_BASE}/conversations/${encodeURIComponent(convId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: newTitle }),
  });
  if (!res.ok) {
    throw new Error(`Failed to rename conversation (${res.status})`);
  }
  return res.json();
}

export async function deleteConversation(convId: string): Promise<{ status: string; conversation_id: string }> {
  const res = await fetch(`${API_BASE}/conversations/${encodeURIComponent(convId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete conversation (${res.status})`);
  }
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; service: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error('Health check failed');
  }
  return res.json();
}
