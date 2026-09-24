"""Conversation-history endpoints for the existing (finalll) backend.

These read the SAME persistent store the chat flow already writes to, so the
app can retrieve a conversation's history after a restart. The store is
SQLite-backed (session_store.py), so history survives server restarts.

Endpoints:
    GET /api/conversations               -> list conversations (most recent first)
    GET /api/conversations/{id}/messages -> ordered history for one conversation
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _clean_message(raw: dict) -> dict | None:
    """Normalise a stored message to the chat history contract."""
    if not isinstance(raw, dict):
        return None
    role = raw.get("role")
    content = raw.get("message")
    if role not in ("user", "assistant") or not content:
        return None
    return {
        "role": role,
        "content": content,
        "created_at": raw.get("created_at"),
    }


@router.get("")
def list_conversations(request: Request) -> dict:
    store = request.app.state.orca.sessions
    conversations = []
    for sid, payload in store.list():
        try:
            messages = json.loads(payload) if payload else []
        except Exception:
            messages = []
        conversations.append({
            "conversation_id": sid,
            "message_count": len(messages),
            "last_message": messages[-1].get("message") if messages else None,
            "updated_at": messages[-1].get("created_at") if messages else None,
        })
    return {"conversations": conversations}


@router.get("/{conversation_id}/messages")
def get_messages(conversation_id: str, request: Request) -> dict:
    store = request.app.state.orca.sessions
    messages = store.get(conversation_id, [])
    cleaned = []
    for m in messages:
        clean = _clean_message(m)
        if clean:
            cleaned.append(clean)
    return {"conversation_id": conversation_id, "messages": cleaned}
