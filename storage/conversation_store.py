"""
storage/conversation_store.py
───────────────────────────────
Repository class managing conversation metadata and persistent records.

Stores conversation records (conversation_id, thread_id, title, created_at, updated_at).
Works alongside SqliteSaver to provide full persistence for SAMUDRA.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional


def generate_deterministic_title(query: str) -> str:
    """Generate a clean title from the user's first query without an LLM call."""
    cleaned = " ".join((query or "").split())
    if not cleaned:
        return "New Marine Conversation"
    # Remove trailing punctuation
    cleaned = cleaned.rstrip("?.,! ")
    # Cap length
    if len(cleaned) > 50:
        cleaned = cleaned[:47] + "..."
    return cleaned[0].upper() + cleaned[1:] if cleaned else "New Marine Conversation"



class ConversationStore:
    """Repository for conversation metadata records."""

    def __init__(self, db_path: str = "samudra_storage.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    def get_or_create_conversation(self, conversation_id: str, first_query: str = "") -> dict[str, Any]:
        """Fetch an existing conversation or create a new persistent metadata record."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT conversation_id, thread_id, title, created_at, updated_at FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()

            if row:
                return dict(row)

            # Create new record
            title = generate_deterministic_title(first_query)
            conn.execute(
                """
                INSERT INTO conversations (conversation_id, thread_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (conversation_id, conversation_id, title, now, now),
            )
            return {
                "conversation_id": conversation_id,
                "thread_id": conversation_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
            }

    def touch_conversation(self, conversation_id: str) -> None:
        """Update updated_at timestamp when a turn executes."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now, conversation_id),
            )

    def list_conversations(self, query: Optional[str] = None) -> list[dict[str, Any]]:
        """Return lightweight metadata for all conversations sorted by updated_at descending."""
        with self._get_connection() as conn:
            if query and query.strip():
                term = f"%{query.strip()}%"
                rows = conn.execute(
                    "SELECT conversation_id, thread_id, title, created_at, updated_at FROM conversations WHERE title LIKE ? ORDER BY updated_at DESC",
                    (term,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT conversation_id, thread_id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def get_conversation(self, conversation_id: str) -> Optional[dict[str, Any]]:
        """Fetch single conversation metadata record."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT conversation_id, thread_id, title, created_at, updated_at FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            return dict(row) if row else None

    def rename_conversation(self, conversation_id: str, new_title: str) -> Optional[dict[str, Any]]:
        """Rename an existing conversation's title."""
        title = generate_deterministic_title(new_title)
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE conversation_id = ?",
                (title, now, conversation_id),
            )
            if cur.rowcount == 0:
                return None
            return self.get_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation record and its associated checkpoint data."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )
            deleted = cur.rowcount > 0

            # Try deleting checkpoints if checkpoint tables exist
            try:
                conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (conversation_id,))
                conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = ?", (conversation_id,))
                conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (conversation_id,))
            except Exception:
                pass

            return deleted
