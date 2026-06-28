"""
Telemetry Event Types and Schemas

Strongly-typed event definitions for the entire agent lifecycle.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid


class EventType(str, Enum):
    """All event types the agent can emit."""

    # Agent Lifecycle
    AGENT_STARTUP = "agent.startup"
    AGENT_SHUTDOWN = "agent.shutdown"
    AGENT_ERROR = "agent.error"
    AGENT_HEALTH_CHECK = "agent.health_check"

    # Tally Integration
    TALLY_SETUP_STARTED = "tally.setup_started"
    TALLY_SETUP_COMPLETED = "tally.setup_completed"
    TALLY_CONNECTION_SUCCESS = "tally.connection_success"
    TALLY_CONNECTION_FAILED = "tally.connection_failed"

    # Extraction
    EXTRACTION_STARTED = "extraction.started"
    EXTRACTION_COMPLETED = "extraction.completed"
    EXTRACTION_ERROR = "extraction.error"

    # Queue
    QUEUE_RECORDS_ENQUEUED = "queue.records_enqueued"
    QUEUE_ERROR = "queue.error"

    # Transmission
    TRANSMISSION_STARTED = "transmission.started"
    TRANSMISSION_COMPLETED = "transmission.completed"
    TRANSMISSION_ERROR = "transmission.error"
    TRANSMISSION_RETRY = "transmission.retry"

    # Sync Cycle
    SYNC_CYCLE_STARTED = "sync.cycle_started"
    SYNC_CYCLE_COMPLETED = "sync.cycle_completed"

    # Cloud API
    CLOUD_HEALTH_CHECK = "cloud.health_check"
    CLOUD_CONNECTED = "cloud.connected"
    CLOUD_DISCONNECTED = "cloud.disconnected"
    CLOUD_API_ERROR = "cloud.api_error"

    # Service
    SERVICE_SYNC_SCHEDULED = "service.sync_scheduled"
    SERVICE_SHUTDOWN = "service.shutdown"


class Severity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TelemetryEvent:
    """Base telemetry event."""

    event_type: EventType
    data: Dict[str, Any]
    severity: Severity = Severity.INFO
    source: str = "agent"
    error: Optional[Dict[str, str]] = None

    # Auto-populated
    event_id: str = None
    timestamp: str = None
    agent_id: str = None
    tenant_id: str = None
    agent_version: str = None
    python_version: str = None
    platform: str = None
    hostname: str = None

    def __post_init__(self):
        """Populate auto fields."""
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

        if self.agent_id is None:
            import os
            self.agent_id = os.getenv("AGENT_ID", "unknown")

        if self.tenant_id is None:
            import os
            self.tenant_id = os.getenv("CLOUD_TENANT_ID", "unknown")

        if self.agent_version is None:
            self.agent_version = "0.4.0"  # From pyproject.toml

        if self.python_version is None:
            import sys
            self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        if self.platform is None:
            import platform
            self.platform = platform.system()

        if self.hostname is None:
            import socket
            self.hostname = socket.gethostname()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = self.to_dict()
        d['event_type'] = d['event_type'].value
        d['severity'] = d['severity'].value
        return d


# Factory functions for common events

def startup_event(success: bool = True) -> TelemetryEvent:
    """Agent startup event."""
    return TelemetryEvent(
        event_type=EventType.AGENT_STARTUP,
        data={"success": success},
        severity=Severity.INFO,
    )


def shutdown_event() -> TelemetryEvent:
    """Agent shutdown event."""
    return TelemetryEvent(
        event_type=EventType.AGENT_SHUTDOWN,
        data={},
        severity=Severity.INFO,
    )


def error_event(error_message: str, error_code: str = "UNKNOWN", stack_trace: str = None) -> TelemetryEvent:
    """Agent error event."""
    return TelemetryEvent(
        event_type=EventType.AGENT_ERROR,
        data={"message": error_message},
        severity=Severity.ERROR,
        error={
            "message": error_message,
            "code": error_code,
            "stack_trace": stack_trace,
        },
    )


def tally_connection_success() -> TelemetryEvent:
    """Tally connected event."""
    return TelemetryEvent(
        event_type=EventType.TALLY_CONNECTION_SUCCESS,
        data={},
        severity=Severity.INFO,
    )


def tally_connection_failed(reason: str) -> TelemetryEvent:
    """Tally connection failed event."""
    return TelemetryEvent(
        event_type=EventType.TALLY_CONNECTION_FAILED,
        data={"reason": reason},
        severity=Severity.ERROR,
    )


def extraction_completed(ledgers_count: int, vouchers_count: int, duration_ms: int) -> TelemetryEvent:
    """Extraction completed event."""
    return TelemetryEvent(
        event_type=EventType.EXTRACTION_COMPLETED,
        data={
            "ledgers_extracted": ledgers_count,
            "vouchers_extracted": vouchers_count,
            "duration_ms": duration_ms,
        },
        severity=Severity.INFO,
    )


def extraction_error(error_message: str) -> TelemetryEvent:
    """Extraction error event."""
    return TelemetryEvent(
        event_type=EventType.EXTRACTION_ERROR,
        data={"error": error_message},
        severity=Severity.ERROR,
    )


def transmission_completed(records_sent: int, duration_ms: int) -> TelemetryEvent:
    """Transmission completed event."""
    return TelemetryEvent(
        event_type=EventType.TRANSMISSION_COMPLETED,
        data={
            "records_sent": records_sent,
            "duration_ms": duration_ms,
        },
        severity=Severity.INFO,
    )


def transmission_error(error_message: str, attempt: int = 1) -> TelemetryEvent:
    """Transmission error event."""
    return TelemetryEvent(
        event_type=EventType.TRANSMISSION_ERROR,
        data={
            "error": error_message,
            "attempt": attempt,
        },
        severity=Severity.WARNING if attempt < 3 else Severity.ERROR,
    )


def sync_cycle_completed(status: str, extracted: int, transmitted: int, errors: int, duration_ms: int) -> TelemetryEvent:
    """Sync cycle completed event."""
    return TelemetryEvent(
        event_type=EventType.SYNC_CYCLE_COMPLETED,
        data={
            "status": status,
            "extracted": extracted,
            "transmitted": transmitted,
            "errors": errors,
            "duration_ms": duration_ms,
        },
        severity=Severity.INFO if status == "success" else Severity.WARNING,
    )


def cloud_connected() -> TelemetryEvent:
    """Cloud API connected event."""
    return TelemetryEvent(
        event_type=EventType.CLOUD_CONNECTED,
        data={},
        severity=Severity.INFO,
    )


def cloud_disconnected(reason: str) -> TelemetryEvent:
    """Cloud API disconnected event."""
    return TelemetryEvent(
        event_type=EventType.CLOUD_DISCONNECTED,
        data={"reason": reason},
        severity=Severity.WARNING,
    )
