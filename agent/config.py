# -*- coding: utf-8 -*-
"""
Agent configuration — reads from environment variables, .env file, or
Windows Credential Manager (set by the registration wizard during install).

Priority: env vars > .env file > Credential Manager
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


def _cred_manager_value(key: str) -> Optional[str]:
    """Try to read a value from Windows Credential Manager registration."""
    try:
        from .registration import get_credentials
        creds = get_credentials()
        if creds:
            mapping = {
                "AGENT_API_KEY": "api_key",
                "AGENT_DEVICE_ID": "device_id",
                "CLOUD_URL": "api_base_url",
                "AGENT_TENANT_ID": "client_id",
            }
            cred_key = mapping.get(key)
            if cred_key:
                return creds.get(cred_key)
    except Exception:
        pass
    return None


def _get(env_var: str, default: str = "") -> str:
    """Get config value: env var first, then credential manager, then default."""
    val = os.environ.get(env_var)
    if val:
        return val
    val = _cred_manager_value(env_var)
    if val:
        return val
    return default


class Config:
    # ── Tally ─────────────────────────────────────────────────────────────────
    TALLY_URL: str = os.environ.get("TALLY_URL", "http://localhost:9000")

    # ── Cloud platform ────────────────────────────────────────────────────────
    CLOUD_URL: str   = _get("CLOUD_URL", "http://localhost:8000")
    API_KEY: str     = _get("AGENT_API_KEY")
    DEVICE_ID: str   = _get("AGENT_DEVICE_ID")
    TENANT_ID: str   = _get("AGENT_TENANT_ID")

    # ── Connector ─────────────────────────────────────────────────────────────
    CONNECTOR_EXE_PATH: str = os.environ.get(
        "TALLY_CONNECTOR_EXE_PATH",
        r"D:\Downloads\integration-setup-lite\integration-setup-lite\TallyAPIConnectorV2.0.exe",
    )
    AUTO_LAUNCH_TALLY: bool = os.environ.get("AUTO_LAUNCH_TALLY", "0") == "1"

    # ── Poll settings ─────────────────────────────────────────────────────────
    POLL_INTERVAL_SECONDS: int = int(os.environ.get("POLL_INTERVAL", "15"))

    @classmethod
    def validate(cls) -> None:
        """Raise if required secrets are missing."""
        # Re-resolve from credential manager in case class attrs were empty at import time
        if not cls.API_KEY:
            cls.API_KEY = _get("AGENT_API_KEY")
        if not cls.DEVICE_ID:
            cls.DEVICE_ID = _get("AGENT_DEVICE_ID")
        if not cls.CLOUD_URL or cls.CLOUD_URL == "http://localhost:8000":
            resolved = _get("CLOUD_URL", "http://localhost:8000")
            if resolved:
                cls.CLOUD_URL = resolved
        if not cls.TENANT_ID:
            cls.TENANT_ID = _get("AGENT_TENANT_ID")

        missing = [k for k in ("API_KEY", "DEVICE_ID") if not getattr(cls, k)]
        if missing:
            raise RuntimeError(
                f"Missing required config: {', '.join('AGENT_' + m for m in missing)}\n"
                "Set them in .env, as environment variables, or run the registration wizard."
            )

    @classmethod
    def source_info(cls) -> str:
        """Return a human-readable description of where config came from."""
        try:
            from .registration import is_registered
            if is_registered():
                return "Windows Credential Manager (registration wizard)"
        except Exception:
            pass
        if os.environ.get("AGENT_API_KEY"):
            return "environment variables"
        return "unknown"
