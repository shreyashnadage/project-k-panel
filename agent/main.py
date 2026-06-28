"""
Tally Sync Agent Entry Point.

Startup flow:
1. Initialize telemetry service
2. Ensure Tally API is available (starts TallyAPIConnector if needed)
3. Run sync orchestrator (extract → queue → transmit)
"""

import sys
import logging
import os
from dotenv import load_dotenv

from agent.orchestrator import main as orchestrator_main
from agent.setup import ensure_tally_ready
from agent.telemetry import (
    initialize_telemetry,
    initialize_transmitter,
    startup_event,
    shutdown_event,
    emit_event,
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Load environment
    load_dotenv('.env.local')

    # Initialize telemetry
    logger.info("=" * 60)
    logger.info("TALLY SYNC AGENT STARTUP")
    logger.info("=" * 60)

    telemetry = initialize_telemetry(
        buffer_size=int(os.getenv("TELEMETRY_BUFFER_SIZE", "10000")),
        batch_size=int(os.getenv("TELEMETRY_BATCH_SIZE", "100")),
        batch_timeout_seconds=int(os.getenv("TELEMETRY_BATCH_TIMEOUT_SECONDS", "5")),
    )

    # Initialize cloud transmitter
    cloud_api_url = os.getenv("CLOUD_API_URL", "http://localhost:8000")
    cloud_api_key = os.getenv("CLOUD_API_KEY", "")
    if cloud_api_key:
        transmitter = initialize_transmitter(
            cloud_api_url=cloud_api_url,
            cloud_api_key=cloud_api_key,
        )
        transmitter.start()
        logger.info("Telemetry transmitter started")

    # Emit startup event
    emit_event(startup_event(success=True))

    try:
        # Step 1: Ensure Tally API is ready
        if not ensure_tally_ready():
            logger.warning("Tally API setup failed, proceeding anyway...")
            logger.warning("Make sure TallyPrime is running and accessible at localhost:9000")

        # Step 2: Run orchestrator
        logger.info("Starting sync orchestrator...")
        orchestrator_main()

    except KeyboardInterrupt:
        logger.info("\nSync stopped by user.")
        emit_event(shutdown_event())
        sys.exit(0)

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        emit_event(shutdown_event())
        sys.exit(1)

    finally:
        # Cleanup
        if telemetry:
            telemetry.shutdown()
        logger.info("Agent stopped")
