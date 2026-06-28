# -*- coding: utf-8 -*-
"""
TallyAPIConnector Manager — auto-launches TallyPrime and the API Connector.

Startup order that MUST be followed:
  1. TallyPrime must be open (Tally.exe listening on port 9000)
  2. TallyAPIConnectorV2.0.exe is started (activates Tally's HTTP API)
  3. Wait until Tally actually responds to HTTP requests (not just TCP)

If this order is violated Tally's HTTP server will not respond.
"""

from __future__ import annotations

import os
import subprocess
import time
import logging
import socket
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_CONNECTOR_EXE = Path(
    r"D:\Downloads\integration-setup-lite\integration-setup-lite\TallyAPIConnectorV2.0.exe"
)
TALLY_URL = "http://127.0.0.1:9000"

STARTUP_TIMEOUT_SECONDS = 30
HTTP_READY_POLL_INTERVAL = 1.0

# Common TallyPrime install locations (checked in order)
TALLY_EXE_SEARCH_PATHS = [
    Path(r"C:\Program Files\TallyPrime\tally.exe"),
    Path(r"C:\TallyPrime\tally.exe"),
    Path(r"C:\Tally\TallyPrime\tally.exe"),
    Path(r"D:\TallyPrime\tally.exe"),
    Path(r"D:\Program Files\TallyPrime\tally.exe"),
]


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _tally_tcp_up() -> bool:
    return _tcp_open("127.0.0.1", 9000)


def _tally_http_ready() -> bool:
    xml = (
        "<ENVELOPE><HEADER><VERSION>1</VERSION>"
        "<TALLYREQUEST>Export</TALLYREQUEST>"
        "<TYPE>Data</TYPE><ID>Trial Balance</ID></HEADER>"
        "<BODY><DESC><STATICVARIABLES>"
        "<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
        "</STATICVARIABLES></DESC></BODY></ENVELOPE>"
    )
    try:
        resp = requests.post(
            TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            timeout=4,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _connector_process_running() -> bool:
    """Check if TallyAPIConnector is already running via tasklist."""
    try:
        result = subprocess.run(
            ["tasklist", "/NH"], capture_output=True, text=True, timeout=5,
        )
        # The exe registers under either V1.0 or V2.0 name depending on version
        return "TallyAPIConnector" in result.stdout
    except Exception:
        return False


def _find_tally_exe() -> Optional[Path]:
    env_path = os.environ.get("TALLY_EXE_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    for p in TALLY_EXE_SEARCH_PATHS:
        if p.exists():
            return p

    return None


def _launch_tally(tally_exe: Path, timeout: int = 45) -> bool:
    """
    Launch TallyPrime and wait until port 9000 is listening.
    Returns True when TCP port is up, False on timeout.
    """
    logger.info(f"Launching TallyPrime from {tally_exe}")

    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008

    subprocess.Popen(
        [str(tally_exe)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=DETACHED_PROCESS,
        cwd=str(tally_exe.parent),
    )

    logger.info(f"Waiting up to {timeout}s for TallyPrime to open (port 9000)...")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _tally_tcp_up():
            logger.info("TallyPrime is up (port 9000 listening)")
            return True
        time.sleep(2)

    logger.error(f"TallyPrime did not start within {timeout}s")
    return False


def _launch_connector(exe: Path) -> None:
    """Launch TallyAPIConnectorV2.0.exe detached."""
    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008

    subprocess.Popen(
        [str(exe)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
        cwd=str(exe.parent),
    )


def _get_connector_exe() -> Path:
    env_path = os.environ.get("TALLY_CONNECTOR_EXE_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_CONNECTOR_EXE


def ensure_tally_ready(
    connector_exe: Optional[Path] = None,
    auto_launch_tally: bool = False,
    timeout: int = STARTUP_TIMEOUT_SECONDS,
) -> bool:
    """
    Ensure Tally's HTTP API is ready to accept requests.

    Steps:
      1. If auto_launch_tally=True and Tally isn't running, launch it
      2. Verify TallyPrime is open (port 9000 must be listening)
      3. Start TallyAPIConnectorV2.0.exe if not already running
      4. Poll until Tally HTTP requests succeed

    Returns True when ready, False on timeout or missing prerequisites.
    """
    if connector_exe is None:
        connector_exe = _get_connector_exe()

    # Step 1: Optionally launch TallyPrime
    if not _tally_tcp_up():
        if auto_launch_tally:
            tally_exe = _find_tally_exe()
            if tally_exe:
                if not _launch_tally(tally_exe):
                    return False
            else:
                logger.error(
                    "Cannot auto-launch TallyPrime — tally.exe not found. "
                    "Set TALLY_EXE_PATH env var or open TallyPrime manually."
                )
                return False
        else:
            logger.error(
                "TallyPrime is not running (port 9000 closed). "
                "Open TallyPrime first, or set AUTO_LAUNCH_TALLY=1."
            )
            return False

    # Step 2: Start connector if not running
    if _connector_process_running():
        logger.debug("TallyAPIConnectorV2.0.exe already running")
    else:
        if not connector_exe.exists():
            logger.error(
                f"TallyAPIConnectorV2.0.exe not found at {connector_exe}. "
                "Set TALLY_CONNECTOR_EXE_PATH env var."
            )
            return False

        logger.info(f"Starting TallyAPIConnectorV2.0.exe from {connector_exe}")
        _launch_connector(connector_exe)
        time.sleep(3)

        if not _connector_process_running():
            logger.warning("TallyAPIConnectorV2.0.exe may not have started — continuing anyway")

    # Step 3: Wait for Tally HTTP to respond
    logger.info("Waiting for Tally HTTP API to become ready...")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _tally_http_ready():
            logger.info("Tally HTTP API is ready")
            return True
        time.sleep(HTTP_READY_POLL_INTERVAL)

    logger.error(
        f"Tally HTTP API did not become ready within {timeout}s. "
        "Ensure TallyPrime is open with a company loaded."
    )
    return False


def wait_for_tally(timeout: int = STARTUP_TIMEOUT_SECONDS) -> bool:
    """Block until Tally HTTP API responds. Use after ensure_tally_ready."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _tally_http_ready():
            return True
        time.sleep(1)
    return False
