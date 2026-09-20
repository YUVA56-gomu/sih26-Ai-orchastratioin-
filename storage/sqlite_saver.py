"""
storage/sqlite_saver.py
────────────────────────
Durable SQLite implementation of LangGraph BaseCheckpointSaver.

Saves checkpoints, blobs, and pending writes to an SQLite database file.
Survives application process restarts and multi-turn request execution.
"""

from __future__ import annotations

import sqlite3
from typing import Any, AsyncIterator, Iterator, Optional, Sequence, Tuple

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    WRITES_IDX_MAP,
    get_checkpoint_id,
    get_checkpoint_metadata,
)
from langchain_core.runnables import RunnableConfig


class SqliteSaver(BaseCheckpointSaver):
    """SQLite-backed checkpointer for LangGraph state persistence."""

    def __init__(self, db_path: str = "samudra_storage.db"):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT NOT NULL,
                    checkpoint BLOB NOT NULL,
                    metadata_type TEXT NOT NULL,
                    metadata BLOB NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                );

                CREATE TABLE IF NOT EXISTS checkpoint_blobs (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    channel TEXT NOT NULL,
                    version TEXT NOT NULL,
                    type TEXT NOT NULL,
                    blob BLOB NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
                );

                CREATE TABLE IF NOT EXISTS checkpoint_writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    type TEXT NOT NULL,
                    blob BLOB NOT NULL,
                    task_path TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                );
            """)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)

        with self._get_connection() as conn:
            if checkpoint_id:
                row = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata_type, metadata
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata_type, metadata
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY checkpoint_id DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

            if not row:
                return None

            checkpoint_id = row["checkpoint_id"]
            parent_id = row["parent_checkpoint_id"]
            checkpoint_dict = self.serde.loads_typed((row["type"], row["checkpoint"]))
            metadata_dict = self.serde.loads_typed((row["metadata_type"], row["metadata"]))

            # Load channel values from checkpoint_blobs
            blob_rows = conn.execute(
                """
                SELECT channel, version, type, blob
                FROM checkpoint_blobs
                WHERE thread_id = ? AND checkpoint_ns = ?
                """,
                (thread_id, checkpoint_ns),
            ).fetchall()

            channel_values = {}
            for b in blob_rows:
                if b["type"] != "empty":
                    channel_values[b["channel"]] = self.serde.loads_typed((b["type"], b["blob"]))

            checkpoint_dict["channel_values"] = channel_values

            # Load pending writes
            write_rows = conn.execute(
                """
                SELECT task_id, channel, type, blob, task_path
                FROM checkpoint_writes
                WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                """,
                (thread_id, checkpoint_ns, checkpoint_id),
            ).fetchall()

            pending_writes = [
                (w["task_id"], w["channel"], self.serde.loads_typed((w["type"], w["blob"])))
                for w in write_rows
            ]

            parent_config = (
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": parent_id,
                    }
                }
                if parent_id
                else None
            )

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": checkpoint_id,
                    }
                },
                checkpoint=checkpoint_dict,
                metadata=metadata_dict,
                parent_config=parent_config,
                pending_writes=pending_writes,
            )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        if not config or "configurable" not in config:
            return
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        query = """
            SELECT checkpoint_id
            FROM checkpoints
            WHERE thread_id = ? AND checkpoint_ns = ?
        """
        params = [thread_id, checkpoint_ns]

        if before and get_checkpoint_id(before):
            query += " AND checkpoint_id < ?"
            params.append(get_checkpoint_id(before))

        query += " ORDER BY checkpoint_id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        for r in rows:
            t = self.get_tuple(
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": r["checkpoint_id"],
                    }
                }
            )
            if t:
                yield t

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        c = checkpoint.copy()
        values: dict[str, Any] = c.pop("channel_values", {})

        c_type, c_blob = self.serde.dumps_typed(c)
        m_type, m_blob = self.serde.dumps_typed(get_checkpoint_metadata(config, metadata))

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints
                (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint["id"],
                    parent_checkpoint_id,
                    c_type,
                    c_blob,
                    m_type,
                    m_blob,
                ),
            )

            for k, v in new_versions.items():
                if k in values:
                    b_type, b_blob = self.serde.dumps_typed(values[k])
                else:
                    b_type, b_blob = "empty", b""

                conn.execute(
                    """
                    INSERT OR REPLACE INTO checkpoint_blobs
                    (thread_id, checkpoint_ns, channel, version, type, blob)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, k, str(v), b_type, b_blob),
                )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        with self._get_connection() as conn:
            for idx, (channel, val) in enumerate(writes):
                idx_val = WRITES_IDX_MAP.get(channel, idx)
                w_type, w_blob = self.serde.dumps_typed(val)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO checkpoint_writes
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, blob, task_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id,
                        checkpoint_ns,
                        checkpoint_id,
                        task_id,
                        idx_val,
                        channel,
                        w_type,
                        w_blob,
                        task_path,
                    ),
                )

    def delete_thread(self, thread_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = ?", (thread_id,))
            conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (thread_id,))

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self.get_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)
