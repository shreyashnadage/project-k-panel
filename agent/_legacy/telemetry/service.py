"""
Telemetry Service

Central event collection, emission, and management.
Integrates Structlog logging with event persistence and transmission.
"""

import logging
import structlog
import asyncio
import json
from typing import Callable, List, Dict, Any, Optional
from collections import deque
from threading import Thread, Event as ThreadEvent
from pathlib import Path

from agent.telemetry.event_types import TelemetryEvent
from agent.telemetry.storage import TelemetryStorage

logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Central telemetry service.

    Handles:
    - Event collection from all modules
    - Structured logging (Structlog)
    - In-memory ring buffer (recent events)
    - SQLite persistence (durability)
    - Pub-sub subscriptions
    - Async transmission to cloud
    """

    def __init__(
        self,
        buffer_size: int = 10000,
        batch_size: int = 100,
        batch_timeout_seconds: int = 5,
        storage: Optional[TelemetryStorage] = None,
    ):
        """
        Initialize telemetry service.

        Args:
            buffer_size: Max events in in-memory ring buffer
            batch_size: Events to batch before sending to cloud
            batch_timeout_seconds: Max wait before sending batch
            storage: TelemetryStorage instance (creates if None)
        """
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds

        # Storage
        self.storage = storage or TelemetryStorage()

        # In-memory ring buffer (fast access for dashboard)
        self.ring_buffer = deque(maxlen=buffer_size)

        # Subscribers
        self.subscribers: Dict[str, List[Callable]] = {}

        # Configuration
        self._enabled = True
        self._shutdown = ThreadEvent()

        # Setup Structlog
        self._setup_structlog()

        logger.info("Telemetry service initialized")

    def _setup_structlog(self):
        """Configure Structlog for JSON output."""
        try:
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.add_log_level,
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                cache_logger_on_first_use=True,
            )
            self.structured_logger = structlog.get_logger()
        except Exception as e:
            logger.warning(f"Failed to setup Structlog: {e}")
            self.structured_logger = None

    def emit(self, event: TelemetryEvent) -> bool:
        """
        Emit a telemetry event.

        Non-blocking operation that:
        1. Validates event
        2. Logs to Structlog
        3. Adds to ring buffer
        4. Persists to SQLite
        5. Notifies subscribers
        6. Queues for cloud transmission

        Args:
            event: TelemetryEvent instance

        Returns:
            True if successful, False otherwise
        """
        if not self._enabled:
            return False

        try:
            # 1. Validate event
            if not isinstance(event, TelemetryEvent):
                logger.error("Invalid event type")
                return False

            # 2. Log to Structlog (JSON)
            if self.structured_logger:
                try:
                    log_data = {
                        "event": event.event_type.value,
                        "severity": event.severity.value,
                        **event.data,
                    }
                    self.structured_logger.info("telemetry", **log_data)
                except Exception as e:
                    logger.debug(f"Failed to log to Structlog: {e}")

            # 3. Add to ring buffer
            self.ring_buffer.append(event)

            # 4. Persist to SQLite (non-blocking via thread)
            def persist():
                try:
                    self.storage.insert_event(event)
                except Exception as e:
                    logger.debug(f"Failed to persist event: {e}")

            thread = Thread(target=persist, daemon=True)
            thread.start()

            # 5. Notify subscribers
            self._notify_subscribers(event)

            return True

        except Exception as e:
            logger.error(f"Error emitting telemetry event: {e}")
            return False

    def subscribe(self, event_type: str, callback: Callable[[TelemetryEvent], None]):
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to
            callback: Function to call when event is emitted
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    def _notify_subscribers(self, event: TelemetryEvent):
        """Notify all subscribers of an event."""
        event_type = event.event_type.value

        # Specific subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")

        # Wildcard subscribers
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in wildcard subscriber: {e}")

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events from in-memory buffer."""
        events = list(self.ring_buffer)[-limit:]
        return [event.to_json_dict() for event in events]

    def get_untransmitted_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get untransmitted events from persistent storage."""
        events = self.storage.get_untransmitted_events(limit)
        # Parse JSON data field
        for event in events:
            if event.get("data"):
                try:
                    event["data"] = json.loads(event["data"])
                except:
                    pass
        return events

    def mark_transmitted(self, event_ids: List[str]) -> bool:
        """Mark events as transmitted to cloud."""
        return self.storage.mark_transmitted(event_ids)

    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        stats = self.storage.get_stats()
        stats["buffer_size"] = len(self.ring_buffer)
        stats["buffer_capacity"] = self.buffer_size
        return stats

    def cleanup_old_events(self) -> int:
        """Delete old events (maintenance)."""
        return self.storage.cleanup_old_events()

    def disable(self):
        """Disable telemetry (useful for testing)."""
        self._enabled = False
        logger.info("Telemetry disabled")

    def enable(self):
        """Re-enable telemetry."""
        self._enabled = True
        logger.info("Telemetry enabled")

    def shutdown(self):
        """Gracefully shutdown telemetry service."""
        try:
            self._shutdown.set()
            self.storage.close()
            logger.info("Telemetry service shutdown")
        except Exception as e:
            logger.error(f"Error shutting down telemetry: {e}")


# Global telemetry service instance
_telemetry_service: Optional[TelemetryService] = None


def initialize_telemetry(
    buffer_size: int = 10000,
    batch_size: int = 100,
    batch_timeout_seconds: int = 5,
) -> TelemetryService:
    """
    Initialize global telemetry service.

    Called once at agent startup.

    Args:
        buffer_size: Ring buffer size
        batch_size: Cloud transmission batch size
        batch_timeout_seconds: Cloud transmission timeout

    Returns:
        TelemetryService instance
    """
    global _telemetry_service

    if _telemetry_service is None:
        _telemetry_service = TelemetryService(
            buffer_size=buffer_size,
            batch_size=batch_size,
            batch_timeout_seconds=batch_timeout_seconds,
        )

    return _telemetry_service


def get_telemetry() -> TelemetryService:
    """
    Get global telemetry service instance.

    Must call initialize_telemetry() first.

    Returns:
        TelemetryService instance
    """
    global _telemetry_service

    if _telemetry_service is None:
        raise RuntimeError("Telemetry not initialized. Call initialize_telemetry() first.")

    return _telemetry_service


def emit_event(event: TelemetryEvent) -> bool:
    """
    Emit a telemetry event.

    Convenience function that uses global service.

    Args:
        event: TelemetryEvent instance

    Returns:
        True if successful
    """
    try:
        service = get_telemetry()
        return service.emit(event)
    except Exception as e:
        logger.error(f"Failed to emit telemetry event: {e}")
        return False
