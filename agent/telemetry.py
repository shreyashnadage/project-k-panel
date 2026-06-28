# -*- coding: utf-8 -*-
"""
Sentry-based telemetry for error reporting and performance monitoring.

Initialised once at agent startup. Captures unhandled exceptions, breadcrumbs,
and structured context (device_id, client_id, agent version) so we can
diagnose failures on client machines without SSH access.

DSN is read from SENTRY_DSN env var or agent.env. When empty, Sentry is
disabled — no data leaves the machine.
"""

from __future__ import annotations

import os
import sys
import socket
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_initialised = False


def init(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    component: str = "agent",
):
    """
    Initialise Sentry SDK. Safe to call multiple times — only the first
    call takes effect.

    Args:
        dsn: Sentry DSN. Falls back to SENTRY_DSN env var. If empty, Sentry
             is silently disabled.
        environment: "production", "staging", "development". Falls back to
                     SENTRY_ENVIRONMENT env var, then "production".
        component: Which part of the system ("agent", "service", "wizard").
    """
    global _initialised
    if _initialised:
        return

    dsn = dsn or os.environ.get("SENTRY_DSN", "")
    if not dsn:
        logger.debug("Sentry DSN not configured — telemetry disabled")
        _initialised = True
        return

    environment = environment or os.environ.get("SENTRY_ENVIRONMENT", "production")

    try:
        import sentry_sdk

        from agent import __version__

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=f"tally-sync-agent@{__version__}",
            traces_sample_rate=0.2,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            attach_stacktrace=True,
            max_breadcrumbs=50,
            before_send=_before_send,
        )

        sentry_sdk.set_tag("component", component)
        sentry_sdk.set_tag("os.version", platform.version())
        sentry_sdk.set_tag("hostname", socket.gethostname())
        sentry_sdk.set_tag("frozen", str(getattr(sys, "frozen", False)))

        _initialised = True
        logger.info(f"Sentry telemetry initialised (env={environment}, component={component})")

    except Exception as e:
        logger.warning(f"Failed to initialise Sentry: {e}")
        _initialised = True


def set_user_context(client_id: str, device_id: str):
    """Set user/device context after config is loaded."""
    try:
        import sentry_sdk
        sentry_sdk.set_user({"id": device_id})
        sentry_sdk.set_tag("client_id", client_id)
        sentry_sdk.set_tag("device_id", device_id)
    except Exception:
        pass


def capture_event(message: str, level: str = "error", **extra):
    """Send a structured event (not an exception)."""
    try:
        import sentry_sdk
        with sentry_sdk.new_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def capture_exception(exc: Optional[BaseException] = None, **extra):
    """Capture an exception with optional extra context."""
    try:
        import sentry_sdk
        with sentry_sdk.new_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def add_breadcrumb(message: str, category: str = "agent", level: str = "info"):
    """Add a navigation breadcrumb for debugging context."""
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
        )
    except Exception:
        pass


def _before_send(event, hint):
    """Scrub sensitive data before sending to Sentry."""
    # Remove API keys from breadcrumbs and extra data
    sensitive_keys = {"api_key", "registration_token", "password", "secret", "authorization"}

    if "extra" in event:
        for key in list(event["extra"].keys()):
            if any(s in key.lower() for s in sensitive_keys):
                event["extra"][key] = "[REDACTED]"

    if "breadcrumbs" in event:
        for crumb in event["breadcrumbs"].get("values", []):
            msg = crumb.get("message", "")
            if any(s in msg.lower() for s in sensitive_keys):
                crumb["message"] = "[REDACTED]"

    return event
