"""
Tally API Connector Setup Module

Ensures TallyAPIConnector is running before extraction.
This exposes the Tally HTTP API on port 9000.
"""

import logging
import subprocess
import time
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TallySetupError(Exception):
    """Raised when Tally setup fails."""
    pass


class TallySetup:
    """Manages Tally API Connector startup and verification."""

    DEFAULT_CONNECTOR_PATH = (
        r"D:\Downloads\integration-setup\integration-setup\TallyAPIConnectorV1.0.exe"
    )
    DEFAULT_SETUP_SCRIPT = (
        r"D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1"
    )
    TALLY_API_URL = "http://localhost:9000"
    HEALTH_CHECK_TIMEOUT = 30  # seconds
    HEALTH_CHECK_INTERVAL = 1   # seconds

    def __init__(
        self,
        connector_path: Optional[str] = None,
        setup_script: Optional[str] = None,
    ):
        """
        Initialize Tally setup manager.

        Args:
            connector_path: Path to TallyAPIConnectorV1.0.exe
            setup_script: Path to RunWithoutBrowser.ps1
        """
        self.connector_path = connector_path or self.DEFAULT_CONNECTOR_PATH
        self.setup_script = setup_script or self.DEFAULT_SETUP_SCRIPT
        self.process: Optional[subprocess.Popen] = None

    def _check_connector_exists(self) -> bool:
        """Check if connector exe exists."""
        exists = os.path.exists(self.connector_path)
        if not exists:
            logger.warning(f"Tally connector not found: {self.connector_path}")
        return exists

    def _check_script_exists(self) -> bool:
        """Check if setup script exists."""
        exists = os.path.exists(self.setup_script)
        if not exists:
            logger.warning(f"Tally setup script not found: {self.setup_script}")
        return exists

    def start_via_powershell(self) -> bool:
        """
        Start TallyAPIConnector using PowerShell script.

        The script:
        1. Runs TallyAPIConnectorV1.0.exe
        2. Kills any browser windows it opens
        3. Keeps the connector process running

        Returns:
            True if started successfully, False otherwise
        """
        if not self._check_script_exists():
            logger.error(f"Setup script not found: {self.setup_script}")
            return False

        try:
            logger.info(f"Starting Tally API Connector via PowerShell script...")
            logger.info(f"Script: {self.setup_script}")

            # Run PowerShell script in background
            self.process = subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    self.setup_script,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

            logger.info(f"Tally setup process started (PID: {self.process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start Tally setup: {e}")
            return False

    def start_direct(self) -> bool:
        """
        Start TallyAPIConnector directly (without PowerShell wrapper).

        Returns:
            True if started successfully, False otherwise
        """
        if not self._check_connector_exists():
            logger.error(f"Connector exe not found: {self.connector_path}")
            return False

        try:
            logger.info(f"Starting Tally API Connector directly...")
            logger.info(f"Exe: {self.connector_path}")

            # Run exe in background
            self.process = subprocess.Popen(
                [self.connector_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

            logger.info(f"Tally connector process started (PID: {self.process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start Tally connector: {e}")
            return False

    def verify_connectivity(self) -> bool:
        """
        Verify Tally API is responding on port 9000.

        Returns:
            True if Tally API is accessible, False otherwise
        """
        try:
            import requests

            logger.info(f"Verifying Tally API connectivity at {self.TALLY_API_URL}...")

            start_time = time.time()
            elapsed = 0

            while elapsed < self.HEALTH_CHECK_TIMEOUT:
                try:
                    response = requests.get(
                        f"{self.TALLY_API_URL}/",
                        timeout=5,
                    )
                    if response.status_code in (200, 404, 500):  # Any response = server is up
                        logger.info(f"✓ Tally API is responding (HTTP {response.status_code})")
                        return True
                except requests.ConnectionError:
                    elapsed = time.time() - start_time
                    if elapsed < self.HEALTH_CHECK_TIMEOUT:
                        logger.debug(f"Tally API not ready yet... ({elapsed:.1f}s)")
                        time.sleep(self.HEALTH_CHECK_INTERVAL)
                    continue

            logger.warning(f"Tally API not responding after {self.HEALTH_CHECK_TIMEOUT}s")
            return False

        except ImportError:
            logger.warning("requests library not available for health check")
            # Fall back to simple wait
            logger.info("Waiting 5 seconds for Tally API to initialize...")
            time.sleep(5)
            return True

    def ensure_running(self) -> bool:
        """
        Ensure Tally API Connector is running.

        Attempts to start via PowerShell script first, then falls back to direct exe.
        Verifies connectivity before returning.

        Returns:
            True if connector is running, False otherwise
        """
        logger.info("=" * 60)
        logger.info("TALLY API SETUP")
        logger.info("=" * 60)

        # Try PowerShell script first (cleaner process management)
        if self._check_script_exists():
            if self.start_via_powershell():
                if self.verify_connectivity():
                    logger.info("✓ Tally API is ready for extraction")
                    return True
                logger.warning("PowerShell script started but API not responding")
                return False

        # Fall back to direct exe start
        logger.info("Falling back to direct exe execution...")
        if self._check_connector_exists():
            if self.start_direct():
                if self.verify_connectivity():
                    logger.info("✓ Tally API is ready for extraction")
                    return True
                logger.warning("Connector started but API not responding")
                return False

        logger.error("Failed to start Tally API Connector")
        logger.error(f"  Checked paths:")
        logger.error(f"    - Script: {self.setup_script}")
        logger.error(f"    - Exe: {self.connector_path}")
        return False

    def stop(self) -> None:
        """Stop the Tally setup process."""
        if self.process:
            try:
                logger.info("Stopping Tally setup process...")
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Tally setup process stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Tally setup process did not terminate gracefully, killing...")
                self.process.kill()
            except Exception as e:
                logger.error(f"Error stopping Tally setup: {e}")


# Global instance (used by agent startup)
_tally_setup: Optional[TallySetup] = None


def get_tally_setup() -> TallySetup:
    """Get or create global Tally setup instance."""
    global _tally_setup
    if _tally_setup is None:
        _tally_setup = TallySetup()
    return _tally_setup


def ensure_tally_ready() -> bool:
    """
    Ensure Tally API is ready before extraction.

    This is the main entry point called from agent startup.

    Returns:
        True if Tally API is ready, False if setup failed
    """
    setup = get_tally_setup()
    return setup.ensure_running()
