# -*- coding: utf-8 -*-
"""
Tally Sync Agent — entry point.

Startup:
1. Load config (env vars / .env)
2. Verify Tally is reachable
3. Start CommandPoller (background thread) — polls cloud, executes commands, uploads
4. Block until Ctrl-C / signal
"""

import signal
import sys
import logging

from .config import Config
from .engine import CommandEngine
from .poller import CommandPoller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 60)
    logger.info("Tally Sync Agent starting…")
    logger.info("=" * 60)

    try:
        Config.validate()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    engine = CommandEngine(tally_url=Config.TALLY_URL)

    # Best-effort connectivity check — don't block startup
    if engine.is_tally_ready():
        logger.info(f"Tally is reachable at {Config.TALLY_URL}")
    else:
        logger.warning(
            f"Tally not reachable at {Config.TALLY_URL}. "
            "Commands will fail until TallyPrime + TallyAPIConnectorV1.0.exe are running."
        )

    poller = CommandPoller(
        cloud_base_url=Config.CLOUD_URL,
        device_id=Config.DEVICE_ID,
        api_key=Config.API_KEY,
        engine=engine,
        poll_interval=Config.POLL_INTERVAL_SECONDS,
    )
    poller.start()

    def _shutdown(sig, _frame):
        logger.info(f"Signal {sig} received — stopping…")
        poller.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(f"Agent running. Polling {Config.CLOUD_URL} every {Config.POLL_INTERVAL_SECONDS}s")
    logger.info("Press Ctrl-C to stop.")

    # Keep main thread alive
    signal.pause()


if __name__ == "__main__":
    main()
