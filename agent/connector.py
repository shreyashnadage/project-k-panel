# -*- coding: utf-8 -*-
"""
TallyAPIConnector Manager

Startup order that MUST be followed:
  1. TallyPrime must already be open (Tally.exe listening on port 9000)
  2. TallyAPIConnectorV1.0.exe is started (activates Tally's HTTP API by
     establishing a persistent connection pool to port 9000)
  3. Wait until Tally actually responds to HTTP requests (not just TCP)

If this order is violated Tally's HTTP server will not respond to requests.
"""

import subprocess
import time
import logging
import socket
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

CONNECTOR_EXE = Path(r"D:\tally-shayak\installer\TallyAPIConnectorV1.0.exe")
TALLY_URL     = "http://127.0.0.1:9000"

STARTUP_TIMEOUT_SECONDS = 30   # time to wait for connector + Tally HTTP to be ready
HTTP_READY_POLL_INTERVAL = 1.0  # seconds between HTTP readiness checks


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _tally_tcp_up() -> bool:
    """Check if Tally.exe is open and listening on port 9000 (TCP level)."""
    return _tcp_open("127.0.0.1", 9000)


def _tally_http_ready() -> bool:
    """
    Check if Tally's HTTP API is actually responding to requests.
    TCP open is not enough — the connector must be running too.
    """
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


def _connector_port_up() -> bool:
    return _tcp_open("127.0.0.1", 3000)


def ensure_tally_ready(
    connector_exe: Path = CONNECTOR_EXE,
    timeout: int = STARTUP_TIMEOUT_SECONDS,
) -> bool:
    """
    Ensure Tally's HTTP API is ready to accept requests.

    Steps:
      1. Verify TallyPrime is open (port 9000 must be listening before we start)
      2. Start TallyAPIConnectorV1.0.exe if not already running
      3. Poll until Tally HTTP requests succeed (connector establishes its pool)

    Returns True when ready, False on timeout or missing prerequisites.
    """
    # Step 1: Tally must be open first
    if not _tally_tcp_up():
        logger.error(
            "TallyPrime is not running. "
            "Please open TallyPrime first, then start the agent."
        )
        return False

    # Step 2: Start connector if needed
    if _connector_port_up():
        logger.debug("TallyAPIConnector already running on port 3000")
    else:
        if not connector_exe.exists():
            logger.warning(
                f"TallyAPIConnectorV1.0.exe not found at {connector_exe}. "
                "Tally HTTP API may not respond."
            )
        else:
            logger.info(f"Starting TallyAPIConnector from {connector_exe}")
            _launch_connector(connector_exe)

            # Wait for connector to bind its port
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if _connector_port_up():
                    logger.info("TallyAPIConnector port 3000 is up")
                    break
                time.sleep(0.5)
            else:
                logger.warning("TallyAPIConnector port 3000 did not open in 10s")

    # Step 3: Wait for Tally HTTP to actually respond
    # The connector needs a moment to establish its connection pool to port 9000
    logger.info("Waiting for Tally HTTP API to become ready...")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _tally_http_ready():
            logger.info("Tally HTTP API is ready")
            return True
        time.sleep(HTTP_READY_POLL_INTERVAL)

    logger.error(
        f"Tally HTTP API did not become ready within {timeout}s. "
        "Make sure TallyPrime is open and TallyAPIConnectorV1.0.exe is running."
    )
    return False


def _launch_connector(exe: Path) -> None:
    """
    Launch TallyAPIConnectorV1.0.exe detached.

    The connector will open a browser tab the first time — users can close it.
    We cannot suppress this without breaking the connector's connection pool
    initialization (the browser load is what triggers the pool setup).
    """
    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008

    subprocess.Popen(
        [str(exe)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
    )


# Legacy alias kept for callers that used the old signature
def ensure_connector_running(connector_exe: Path = CONNECTOR_EXE) -> bool:
    return ensure_tally_ready(connector_exe=connector_exe)


def wait_for_tally(timeout: int = STARTUP_TIMEOUT_SECONDS) -> bool:
    """Block until Tally HTTP API responds (not just TCP). Use after ensure_tally_ready."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _tally_http_ready():
            return True
        time.sleep(1)
    return False
