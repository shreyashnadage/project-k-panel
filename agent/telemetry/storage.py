"""
Telemetry Event Storage

Persistent SQLite storage for telemetry events.
Provides durability and offline resilience.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock

from agent.telemetry.event_types import TelemetryEvent

logger = logging.getLogger(__name__)


class TelemetryStorage:
    """SQLite-backed persistent event storage."""

    DB_PATH = Path("telemetry_events.db")
    RETENTION_DAYS = 7

    def __init__(self, db_path: Optional[Path] = None, retention_days: int = 7):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database (default: telemetry_events.db)
            retention_days: How long to keep events (default: 7 days)
        """
        self.db_path = db_path or self.DB_PATH
        self.retention_days = retention_days
        self._lock = Lock()
        self._conn = None

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        source TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        agent_version TEXT,
                        python_version TEXT,
                        platform TEXT,
                        hostname TEXT,
                        data TEXT NOT NULL,
                        error_message TEXT,
                        error_code TEXT,
                        error_stack TEXT,
                        transmitted INTEGER DEFAULT 0,
                        transmission_attempts INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        transmitted_at DATETIME
                    )
                """)

                # Indexes for common queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_event_type
                    ON telemetry_events(event_type)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON telemetry_events(timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_transmitted
                    ON telemetry_events(transmitted)
                """)

                # Metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
                logger.info(f"Telemetry database initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize telemetry database: {e}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                timeout=10,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def insert_event(self, event: TelemetryEvent) -> bool:
        """
        Insert event into storage.

        Args:
            event: TelemetryEvent instance

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    error_data = event.error or {}

                    cursor.execute("""
                        INSERT INTO telemetry_events (
                            event_id, event_type, timestamp, severity, source,
                            agent_id, tenant_id, agent_version, python_version,
                            platform, hostname, data, error_message, error_code,
                            error_stack
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id,
                        event.event_type.value,
                        event.timestamp,
                        event.severity.value,
                        event.source,
                        event.agent_id,
                        event.tenant_id,
                        event.agent_version,
                        event.python_version,
                        event.platform,
                        event.hostname,
                        json.dumps(event.data),
                        error_data.get("message"),
                        error_data.get("code"),
                        error_data.get("stack_trace"),
                    ))

                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Failed to insert telemetry event: {e}")
            return False

    def get_untransmitted_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events that haven't been transmitted to cloud yet.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT * FROM telemetry_events
                        WHERE transmitted = 0
                        ORDER BY created_at ASC
                        LIMIT ?
                    """, (limit,))

                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get untransmitted events: {e}")
            return []

    def mark_transmitted(self, event_ids: List[str]) -> bool:
        """
        Mark events as transmitted to cloud.

        Args:
            event_ids: List of event IDs to mark

        Returns:
            True if successful
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    for event_id in event_ids:
                        cursor.execute("""
                            UPDATE telemetry_events
                            SET transmitted = 1,
                                transmitted_at = CURRENT_TIMESTAMP,
                                transmission_attempts = transmission_attempts + 1
                            WHERE event_id = ?
                        """, (event_id,))

                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Failed to mark events as transmitted: {e}")
            return False

    def increment_transmission_attempt(self, event_id: str) -> bool:
        """
        Increment transmission attempt counter for an event.

        Args:
            event_id: Event ID

        Returns:
            True if successful
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        UPDATE telemetry_events
                        SET transmission_attempts = transmission_attempts + 1
                        WHERE event_id = ?
                    """, (event_id,))

                    conn.commit()
                    return True

        except Exception as e:
            logger.error(f"Failed to increment transmission attempt: {e}")
            return False

    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent events (for dashboard).

        Args:
            limit: Number of events to return
            event_type: Optional event type filter

        Returns:
            List of recent events
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    if event_type:
                        cursor.execute("""
                            SELECT * FROM telemetry_events
                            WHERE event_type = ?
                            ORDER BY timestamp DESC
                            LIMIT ?
                        """, (event_type, limit))
                    else:
                        cursor.execute("""
                            SELECT * FROM telemetry_events
                            ORDER BY timestamp DESC
                            LIMIT ?
                        """, (limit,))

                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []

    def get_event_count(self, event_type: Optional[str] = None) -> int:
        """
        Get count of events.

        Args:
            event_type: Optional filter by event type

        Returns:
            Number of events
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    if event_type:
                        cursor.execute(
                            "SELECT COUNT(*) as count FROM telemetry_events WHERE event_type = ?",
                            (event_type,)
                        )
                    else:
                        cursor.execute("SELECT COUNT(*) as count FROM telemetry_events")

                    result = cursor.fetchone()
                    return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Failed to get event count: {e}")
            return 0

    def cleanup_old_events(self) -> int:
        """
        Delete events older than retention period.

        Returns:
            Number of events deleted
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

                    cursor.execute("""
                        DELETE FROM telemetry_events
                        WHERE created_at < ?
                    """, (cutoff_date.isoformat(),))

                    deleted = cursor.rowcount
                    conn.commit()

                    if deleted > 0:
                        logger.info(f"Deleted {deleted} old telemetry events")

                    return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get telemetry storage statistics.

        Returns:
            Dictionary with stats
        """
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # Total events
                    cursor.execute("SELECT COUNT(*) as count FROM telemetry_events")
                    total = cursor.fetchone()['count']

                    # Untransmitted
                    cursor.execute("SELECT COUNT(*) as count FROM telemetry_events WHERE transmitted = 0")
                    untransmitted = cursor.fetchone()['count']

                    # By severity
                    cursor.execute("""
                        SELECT severity, COUNT(*) as count
                        FROM telemetry_events
                        GROUP BY severity
                    """)
                    by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}

                    # By event type (top 10)
                    cursor.execute("""
                        SELECT event_type, COUNT(*) as count
                        FROM telemetry_events
                        GROUP BY event_type
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    by_type = {row['event_type']: row['count'] for row in cursor.fetchall()}

                    return {
                        "total_events": total,
                        "untransmitted_events": untransmitted,
                        "by_severity": by_severity,
                        "by_event_type": by_type,
                    }

        except Exception as e:
            logger.error(f"Failed to get telemetry stats: {e}")
            return {}

    def close(self):
        """Close database connection."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
        except Exception as e:
            logger.error(f"Error closing telemetry database: {e}")
