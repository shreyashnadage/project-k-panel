# -*- coding: utf-8 -*-
"""
Agent configuration — reads from environment variables or a local .env file.

Secrets are NEVER stored in this file; they come from the environment or
Windows Credential Manager (via keyring, added in Phase 4).
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv is optional for dev; required for packaged agent


class Config:
    # ── Tally ─────────────────────────────────────────────────────────────────
    TALLY_URL: str = os.environ.get("TALLY_URL", "http://localhost:9000")

    # ── Cloud platform ────────────────────────────────────────────────────────
    CLOUD_URL: str   = os.environ.get("CLOUD_URL", "http://localhost:8000")
    API_KEY: str     = os.environ.get("AGENT_API_KEY", "")
    DEVICE_ID: str   = os.environ.get("AGENT_DEVICE_ID", "")
    TENANT_ID: str   = os.environ.get("AGENT_TENANT_ID", "")

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
        missing = [k for k in ("API_KEY", "DEVICE_ID") if not getattr(cls, k)]
        if missing:
            raise RuntimeError(
                f"Missing required env vars: {', '.join('AGENT_' + m for m in missing)}\n"
                "Set them in .env or as environment variables."
            )
