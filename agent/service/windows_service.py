"""
Windows Service Wrapper for Tally Sync Agent

Allows the orchestrator to run as a Windows Service.
Handles service lifecycle, logging, and crash recovery.

Installation:
    nssm install TallySyncAgent python -m agent.service.windows_service

Control:
    nssm start TallySyncAgent
    nssm stop TallySyncAgent
    nssm status TallySyncAgent
"""

import sys
import logging
import logging.handlers
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

from agent.orchestrator import SyncOrchestrator


logger = logging.getLogger(__name__)


class TallySyncService:
    """
    Windows Service wrapper for the Tally Sync Agent.

    Runs the sync orchestrator in a continuous loop with:
    - Configurable sync interval
    - Graceful shutdown
    - Comprehensive logging
    - Crash recovery
    """

    def __init__(self, sync_interval_hours: int = 6, log_dir: str = "logs"):
        """
        Initialize service.

        Args:
            sync_interval_hours: Hours between sync cycles (default 6)
            log_dir: Directory for service logs
        """
        self.sync_interval_hours = sync_interval_hours
        self.sync_interval_seconds = sync_interval_hours * 3600
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Service state
        self.running = False
        self.shutdown_event = threading.Event()
        self.next_sync_time = None

        self._setup_logging()

    def _setup_logging(self):
        """Configure rotating file logging for the service."""
        log_file = self.log_dir / "tally_sync_service.log"

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info("=" * 70)
        logger.info("TALLY SYNC SERVICE STARTED")
        logger.info("=" * 70)

    def start(self):
        """Start the service and begin sync loop."""
        logger.info(f"Starting Tally Sync Service (interval: {self.sync_interval_hours}h)")
        self.running = True
        self.shutdown_event.clear()
        self.next_sync_time = datetime.now()

        # Run in main thread (NSSM expects blocking call)
        self._run_loop()

    def stop(self):
        """Gracefully stop the service."""
        logger.info("Shutdown signal received")
        self.running = False
        self.shutdown_event.set()

    def _run_loop(self):
        """Main service loop - runs sync cycles on schedule."""
        try:
            while self.running:
                now = datetime.now()

                # Check if it's time to sync
                if now >= self.next_sync_time:
                    self._run_sync_cycle()
                    self.next_sync_time = now + timedelta(seconds=self.sync_interval_seconds)
                    logger.info(
                        f"Next sync scheduled for {self.next_sync_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                # Sleep briefly to avoid busy-waiting
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in service loop: {e}", exc_info=True)
            raise
        finally:
            logger.info("Service stopped")

    def _run_sync_cycle(self):
        """Execute one sync cycle (extraction, queue, transmission)."""
        logger.info("-" * 70)
        logger.info("SYNC CYCLE STARTING")
        logger.info("-" * 70)

        try:
            # Step 1: Ensure Tally API is ready
            from agent.setup import ensure_tally_ready
            if not ensure_tally_ready():
                logger.warning("Tally API setup failed, but proceeding with sync...")

            # Step 2: Initialize orchestrator
            import os
            from pathlib import Path
            from dotenv import load_dotenv

            # Load config
            env_file = Path(".env.local")
            if env_file.exists():
                load_dotenv(env_file)

            orchestrator = SyncOrchestrator(
                tally_url=os.getenv("TALLY_URL", "http://localhost:9000"),
                tally_company_name=os.getenv("TALLY_COMPANY_NAME", ""),
                tally_company_guid=os.getenv("TALLY_COMPANY_GUID", ""),
                cloud_api_url=os.getenv("CLOUD_API_URL", "http://localhost:8000"),
                cloud_api_key=os.getenv("CLOUD_API_KEY", ""),
                cloud_tenant_id=os.getenv("CLOUD_TENANT_ID", ""),
            )

            # Step 3: Run sync
            result = orchestrator.run_once()

            # Log result
            logger.info(f"Sync result: {result}")
            logger.info("-" * 70)
            logger.info(f"SYNC CYCLE COMPLETE - Status: {result.get('status', 'unknown')}")
            logger.info("-" * 70)

        except Exception as e:
            logger.error(f"Error during sync cycle: {e}", exc_info=True)
            # Continue running despite sync errors (don't crash service)

    def get_status(self) -> dict:
        """Get current service status."""
        return {
            "running": self.running,
            "next_sync": self.next_sync_time.isoformat() if self.next_sync_time else None,
            "sync_interval_hours": self.sync_interval_hours,
            "log_file": str(self.log_dir / "tally_sync_service.log"),
        }


# Global service instance (required by NSSM)
_service_instance = None


def main():
    """Main entry point for NSSM/Windows Service."""
    global _service_instance

    # Get config from environment
    import os
    sync_interval = int(os.getenv("TALLY_SYNC_INTERVAL_HOURS", "6"))
    log_dir = os.getenv("TALLY_SYNC_LOG_DIR", "logs")

    # Create and start service
    _service_instance = TallySyncService(
        sync_interval_hours=sync_interval,
        log_dir=log_dir,
    )

    # Signal handlers for graceful shutdown
    import signal

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        _service_instance.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start service (blocks until stop)
    _service_instance.start()


if __name__ == "__main__":
    main()
