"""
Agent Telemetry Module

Event-driven telemetry service with Structlog integration.
Provides structured event emission, persistence, and cloud transmission.

Quick Start:
    from agent.telemetry import initialize_telemetry, emit_event
    from agent.telemetry.event_types import extraction_completed

    # Initialize (call once at agent startup)
    telemetry = initialize_telemetry()

    # Emit events from anywhere
    emit_event(extraction_completed(ledgers=150, vouchers=500, duration_ms=2340))
"""

from agent.telemetry.event_types import (
    EventType,
    Severity,
    TelemetryEvent,
    startup_event,
    shutdown_event,
    error_event,
    tally_connection_success,
    tally_connection_failed,
    extraction_completed,
    extraction_error,
    transmission_completed,
    transmission_error,
    sync_cycle_completed,
    cloud_connected,
    cloud_disconnected,
)

from agent.telemetry.service import (
    TelemetryService,
    initialize_telemetry,
    get_telemetry,
    emit_event,
)

from agent.telemetry.storage import TelemetryStorage

__all__ = [
    # Event types
    "EventType",
    "Severity",
    "TelemetryEvent",
    # Event factories
    "startup_event",
    "shutdown_event",
    "error_event",
    "tally_connection_success",
    "tally_connection_failed",
    "extraction_completed",
    "extraction_error",
    "transmission_completed",
    "transmission_error",
    "sync_cycle_completed",
    "cloud_connected",
    "cloud_disconnected",
    # Service
    "TelemetryService",
    "initialize_telemetry",
    "get_telemetry",
    "emit_event",
    # Storage
    "TelemetryStorage",
]
