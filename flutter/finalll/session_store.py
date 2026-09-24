import sqlite3
import json
from pathlib import Path

DB = Path("data/orca_sessions.db")
DB.parent.mkdir(exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    conn.commit()
    conn.close()


def get_session(session_id: str):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT payload FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else []


def save_session(session_id: str, history):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO sessions(id,payload) VALUES (?,?)", (session_id, json.dumps(history)))
    conn.commit()
    conn.close()


def list_sessions():
    """All conversations, most recently created/updated first.

    Persistent history is the whole point: these rows survive server restarts
    because they live in the SQLite file, never an in-memory dict.
    """
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, payload FROM sessions ORDER BY rowid DESC").fetchall()
    conn.close()
    return [(rid, payload) for rid, payload in rows]


class SessionStore:
    def get(self, session_id, default=None):
        data = get_session(session_id)
        return data if data else (default if default is not None else [])

    def __setitem__(self, session_id, history):
        save_session(session_id, history)

    def __getitem__(self, session_id):
        return self.get(session_id)

    def list(self):
        return list_sessions()
