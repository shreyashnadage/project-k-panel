# -*- coding: utf-8 -*-
"""
Tally Sync Agent — entry point.

Startup:
1. Load config (env vars / .env)
2. Auto-launch TallyAPIConnectorV2.0.exe (and optionally TallyPrime)
3. Verify Tally HTTP API is responding
4. Start CommandPoller (background thread) — polls cloud, executes commands, uploads
5. Block until Ctrl-C
"""

import sys
import logging
from pathlib import Path

from .config import Config
from .telemetry import init as init_telemetry, set_user_context, capture_exception, add_breadcrumb
from .connector import ensure_tally_ready
from .engine import CommandEngine
from .poller import CommandPoller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    init_telemetry(component="agent")

    logger.info("=" * 60)
    logger.info("Tally Sync Agent starting...")
    logger.info("=" * 60)

    try:
        Config.validate()
    except RuntimeError as e:
        capture_exception(e, stage="config_validation")
        logger.error(str(e))
        logger.error("Run the registration wizard or set AGENT_API_KEY / AGENT_DEVICE_ID")
        sys.exit(1)

    set_user_context(client_id=Config.TENANT_ID, device_id=Config.DEVICE_ID)
    logger.info(f"Config source: {Config.source_info()}")

    # Auto-launch connector (and optionally TallyPrime)
    connector_exe = Path(Config.CONNECTOR_EXE_PATH)
    tally_ok = ensure_tally_ready(
        connector_exe=connector_exe,
        auto_launch_tally=Config.AUTO_LAUNCH_TALLY,
    )

    if tally_ok:
        logger.info("Tally HTTP API is ready — starting poller")
    else:
        logger.warning(
            "Tally HTTP API not ready. Agent will start anyway — "
            "commands will fail until Tally is available."
        )

    engine = CommandEngine(tally_url=Config.TALLY_URL)

    poller = CommandPoller(
        cloud_base_url=Config.CLOUD_URL,
        device_id=Config.DEVICE_ID,
        api_key=Config.API_KEY,
        tenant_id=Config.TENANT_ID,
        engine=engine,
        poll_interval=Config.POLL_INTERVAL_SECONDS,
    )
    poller.start()

    logger.info(f"Agent running. Polling {Config.CLOUD_URL} every {Config.POLL_INTERVAL_SECONDS}s")
    logger.info("Press Ctrl-C to stop.")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Ctrl-C received — stopping...")
        poller.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
