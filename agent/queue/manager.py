"""
Local Queue Manager

Stores extracted records in SQLite queue for reliable transmission.
Handles:
- Queue persistence across crashes
- Batch processing (send N records at a time)
- Duplicate detection
- Status tracking
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class RecordStatus(Enum):
    """Status of a queued record."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class QueueManager:
    """
    Local SQLite queue for reliable data transmission.
    Persists records even if agent crashes before transmission.
    """

    def __init__(self, db_path: str = "agent_queue.db"):
        """
        Initialize queue manager.

        Args:
            db_path: Path to SQLite queue database
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Create queue tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_type TEXT NOT NULL,
                record_guid TEXT NOT NULL,
                company_guid TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)

        # Unique constraint: only one pending record per guid
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_guid
            ON queue(record_type, company_guid, record_guid)
            WHERE status = 'pending'
        """)

        conn.commit()
        conn.close()
        logger.debug(f"Queue initialized at {self.db_path}")

    def enqueue_voucher(self, voucher: Dict[str, Any]) -> bool:
        """
        Add voucher to queue.

        Args:
            voucher: Voucher dict from parser

        Returns:
            True if enqueued, False if already pending
        """
        return self._enqueue(
            record_type="voucher",
            record_guid=voucher["voucher_guid"],
            company_guid=voucher["company_guid"],
            data=voucher,
        )

    def enqueue_ledger(self, ledger: Dict[str, Any]) -> bool:
        """
        Add ledger to queue.

        Args:
            ledger: Ledger dict from parser

        Returns:
            True if enqueued, False if already pending
        """
        return self._enqueue(
            record_type="ledger",
            record_guid=ledger["ledger_guid"],
            company_guid=ledger["company_guid"],
            data=ledger,
        )

    def _enqueue(self, record_type: str, record_guid: str, company_guid: str,
                 data: Dict[str, Any]) -> bool:
        """
        Add record to queue.

        Args:
            record_type: 'voucher' or 'ledger'
            record_guid: Unique record identifier
            company_guid: Company identifier
            data: Record data

        Returns:
            True if enqueued, False if already pending
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO queue (record_type, record_guid, company_guid, data, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (record_type, record_guid, company_guid, json.dumps(data)))
            conn.commit()
            logger.debug(f"Enqueued {record_type} {record_guid}")
            return True
        except sqlite3.IntegrityError:
            # Record already pending
            logger.debug(f"Record already pending: {record_type} {record_guid}")
            return False
        finally:
            conn.close()

    def get_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get pending records from queue.

        Args:
            limit: Maximum records to return

        Returns:
            List of pending record dicts with {id, type, data}
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, record_type, data
                FROM queue
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))

            records = []
            for row in cursor.fetchall():
                records.append({
                    "id": row["id"],
                    "type": row["record_type"],
                    "data": json.loads(row["data"]),
                })
            return records
        finally:
            conn.close()

    def mark_sent(self, queue_id: int):
        """
        Mark record as successfully sent.

        Args:
            queue_id: Queue record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE queue
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (queue_id,))
            conn.commit()
            logger.debug(f"Marked {queue_id} as sent")
        finally:
            conn.close()

    def mark_failed(self, queue_id: int, error_message: str):
        """
        Mark record as failed transmission.

        Args:
            queue_id: Queue record ID
            error_message: Reason for failure
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE queue
                SET status = 'failed', error_message = ?, retry_count = retry_count + 1
                WHERE id = ?
            """, (error_message, queue_id))
            conn.commit()
            logger.warning(f"Marked {queue_id} as failed: {error_message}")
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.

        Returns:
            {pending: N, sent: N, failed: N}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            stats = {}
            for status in ["pending", "sent", "failed"]:
                cursor.execute(
                    "SELECT COUNT(*) FROM queue WHERE status = ?",
                    (status,)
                )
                stats[status] = cursor.fetchone()[0]
            return stats
        finally:
            conn.close()

    def clear(self):
        """Clear all queue records (use with caution)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM queue")
            conn.commit()
            logger.warning("Queue cleared")
        finally:
            conn.close()
