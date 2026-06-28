# -*- coding: utf-8 -*-
"""
Offline Queue — buffers upload payloads when the cloud is unreachable.

Each queued item is a complete upload payload (endpoint + JSON body) that
can be retried as-is. The queue persists across agent restarts via SQLite.

Lifecycle: pending -> sent | failed (after MAX_RETRIES)
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
QUEUE_DB_DEFAULT = "agent_queue.db"


class QueueManager:
    def __init__(self, db_path: str = QUEUE_DB_DEFAULT):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upload_queue (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint   TEXT    NOT NULL,
                    payload    TEXT    NOT NULL,
                    label      TEXT    NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    status     TEXT    DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error      TEXT,
                    created_at TEXT    DEFAULT (datetime('now')),
                    sent_at    TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS ix_queue_status
                ON upload_queue(status)
            """)
        logger.debug(f"Queue DB initialized at {self.db_path}")

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    # ── Enqueue ──────────────────────────────────────────────────────────────

    def enqueue(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        label: str,
        record_count: int = 0,
    ) -> int:
        """
        Add an upload payload to the queue.
        Returns the queue row ID.
        """
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO upload_queue (endpoint, payload, label, record_count) "
                "VALUES (?, ?, ?, ?)",
                (endpoint, json.dumps(payload, ensure_ascii=False), label, record_count),
            )
            row_id = cur.lastrowid
        logger.info(f"[Queue] Enqueued {label} ({record_count} records) -> {endpoint}")
        return row_id

    # ── Dequeue / flush ──────────────────────────────────────────────────────

    def get_pending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return pending items oldest-first, up to limit."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, endpoint, payload, label, record_count, retry_count "
                "FROM upload_queue WHERE status = 'pending' "
                "ORDER BY created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": r["id"],
                "endpoint": r["endpoint"],
                "payload": json.loads(r["payload"]),
                "label": r["label"],
                "record_count": r["record_count"],
                "retry_count": r["retry_count"],
            }
            for r in rows
        ]

    def mark_sent(self, queue_id: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE upload_queue SET status = 'sent', sent_at = datetime('now') "
                "WHERE id = ?",
                (queue_id,),
            )

    def mark_failed(self, queue_id: int, error: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE upload_queue SET retry_count = retry_count + 1, error = ? "
                "WHERE id = ?",
                (error, queue_id),
            )
            # Permanently fail after MAX_RETRIES
            conn.execute(
                "UPDATE upload_queue SET status = 'failed' "
                "WHERE id = ? AND retry_count >= ?",
                (queue_id, MAX_RETRIES),
            )

    # ── Stats ────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        with self._conn() as conn:
            stats = {}
            for status in ("pending", "sent", "failed"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM upload_queue WHERE status = ?",
                    (status,),
                ).fetchone()
                stats[status] = row[0]
            return stats

    def pending_count(self) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM upload_queue WHERE status = 'pending'"
            ).fetchone()
            return row[0]

    def clear_sent(self) -> int:
        """Remove successfully sent items. Returns count deleted."""
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM upload_queue WHERE status = 'sent'")
            return cur.rowcount

    def clear_all(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM upload_queue")
        logger.warning("[Queue] All items cleared")
