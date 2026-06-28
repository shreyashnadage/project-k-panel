"""
Service Manager - Control the Tally Sync Windows Service

Provides utilities to manage the service:
- Install/uninstall
- Start/stop/restart
- Check status
- View logs
- Configure

Usage:
    python -m agent.service.manager install
    python -m agent.service.manager start
    python -m agent.service.manager stop
    python -m agent.service.manager status
    python -m agent.service.manager logs
"""

import subprocess
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manage Tally Sync Windows Service via NSSM."""

    SERVICE_NAME = "TallySyncAgent"
    DISPLAY_NAME = "Tally Sync Agent"
    DESCRIPTION = "Automated Tally → Cloud data synchronization service"

    def __init__(self):
        """Initialize service manager."""
        self.nssm_path = self._find_nssm()

    @staticmethod
    def _find_nssm() -> str:
        """Find NSSM executable."""
        try:
            result = subprocess.run(
                ["where", "nssm"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")[0]
        except (subprocess.CalledProcessError, IndexError):
            raise FileNotFoundError(
                "NSSM not found. Install NSSM and add to PATH:\n"
                "  https://nssm.cc/download"
            )

    def install(self, python_exe: Optional[str] = None) -> bool:
        """
        Install the service.

        Args:
            python_exe: Path to python.exe (auto-detect if None)

        Returns:
            True if successful
        """
        if python_exe is None:
            python_exe = sys.executable

        print(f"Installing {self.DISPLAY_NAME}...")
        print(f"  Python: {python_exe}")
        print(f"  Service Name: {self.SERVICE_NAME}")

        try:
            # Install service
            subprocess.run(
                [
                    self.nssm_path, "install", self.SERVICE_NAME,
                    python_exe, "-m", "agent.service.windows_service"
                ],
                check=True,
                capture_output=True,
            )

            # Set service properties
            subprocess.run(
                [self.nssm_path, "set", self.SERVICE_NAME, "DisplayName", self.DISPLAY_NAME],
                check=True,
                capture_output=True,
            )

            subprocess.run(
                [self.nssm_path, "set", self.SERVICE_NAME, "Description", self.DESCRIPTION],
                check=True,
                capture_output=True,
            )

            # Set to auto-start
            subprocess.run(
                [self.nssm_path, "set", self.SERVICE_NAME, "Start", "SERVICE_AUTO_START"],
                check=True,
                capture_output=True,
            )

            print("✓ Service installed successfully")
            print(f"  Start service: nssm start {self.SERVICE_NAME}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Installation failed: {e.stderr.decode() if e.stderr else str(e)}")
            return False

    def uninstall(self) -> bool:
        """Uninstall the service."""
        print(f"Uninstalling {self.DISPLAY_NAME}...")

        try:
            # Stop service first
            self.stop()

            # Remove service
            subprocess.run(
                [self.nssm_path, "remove", self.SERVICE_NAME, "confirm"],
                check=True,
                capture_output=True,
            )

            print("✓ Service uninstalled successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Uninstallation failed: {e.stderr.decode() if e.stderr else str(e)}")
            return False

    def start(self) -> bool:
        """Start the service."""
        print(f"Starting {self.DISPLAY_NAME}...")

        try:
            subprocess.run(
                [self.nssm_path, "start", self.SERVICE_NAME],
                check=True,
                capture_output=True,
            )
            print("✓ Service started")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to start service: {e.stderr.decode() if e.stderr else str(e)}")
            return False

    def stop(self) -> bool:
        """Stop the service."""
        print(f"Stopping {self.DISPLAY_NAME}...")

        try:
            subprocess.run(
                [self.nssm_path, "stop", self.SERVICE_NAME],
                check=True,
                capture_output=True,
            )
            print("✓ Service stopped")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to stop service: {e.stderr.decode() if e.stderr else str(e)}")
            return False

    def restart(self) -> bool:
        """Restart the service."""
        print(f"Restarting {self.DISPLAY_NAME}...")
        self.stop()
        return self.start()

    def status(self) -> bool:
        """Check service status."""
        try:
            result = subprocess.run(
                [self.nssm_path, "status", self.SERVICE_NAME],
                capture_output=True,
                text=True,
            )

            status_output = result.stdout.strip()
            print(f"Service Status: {status_output}")

            if "SERVICE_RUNNING" in status_output:
                print("✓ Service is running")
                return True
            else:
                print("⚠ Service is not running")
                return False

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to check status: {e.stderr.decode() if e.stderr else str(e)}")
            return False

    def logs(self, follow: bool = False) -> bool:
        """View service logs."""
        log_file = Path("logs/tally_sync_service.log")

        if not log_file.exists():
            print("✗ Log file not found. Service may not have run yet.")
            return False

        print(f"Service Logs: {log_file.absolute()}")
        print("-" * 70)

        try:
            if follow:
                # Follow logs (tail -f equivalent)
                while True:
                    with open(log_file, "r") as f:
                        lines = f.readlines()
                        for line in lines[-20:]:
                            print(line.rstrip())
                    import time
                    time.sleep(1)
            else:
                # Show last 50 lines
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in lines[-50:]:
                        print(line.rstrip())

            return True

        except Exception as e:
            print(f"✗ Failed to read logs: {e}")
            return False


def main():
    """Command-line interface for service management."""
    if len(sys.argv) < 2:
        print("Usage: python -m agent.service.manager <command>")
        print()
        print("Commands:")
        print("  install    Install the service")
        print("  uninstall  Uninstall the service")
        print("  start      Start the service")
        print("  stop       Stop the service")
        print("  restart    Restart the service")
        print("  status     Check service status")
        print("  logs       View service logs")
        sys.exit(1)

    command = sys.argv[1].lower()
    manager = ServiceManager()

    if command == "install":
        success = manager.install()
    elif command == "uninstall":
        success = manager.uninstall()
    elif command == "start":
        success = manager.start()
    elif command == "stop":
        success = manager.stop()
    elif command == "restart":
        success = manager.restart()
    elif command == "status":
        success = manager.status()
    elif command == "logs":
        follow = "--follow" in sys.argv
        success = manager.logs(follow=follow)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
