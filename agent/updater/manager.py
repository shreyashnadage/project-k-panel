"""
OTA Update Manager

Checks GitHub Releases for newer agent versions, downloads delta patches,
applies them atomically with rollback support, and schedules restarts.

Design:
- Checks once per day at a random offset to avoid thundering herd
- Downloads delta patch if available, falls back to full exe
- Verifies SHA-256 checksum before applying
- Keeps one backup copy for rollback
- Schedules Windows Service restart via NSSM
"""

import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from packaging.version import Version

logger = logging.getLogger(__name__)

CURRENT_VERSION = "0.4.0"

# GitHub Releases API — override via AGENT_UPDATE_URL env var for self-hosted
DEFAULT_UPDATE_URL = os.getenv(
    "AGENT_UPDATE_URL",
    "http://15.206.90.21:8000/v1/agent/releases/latest",
)

# Where this exe lives when installed
INSTALL_DIR = Path(os.getenv("AGENT_INSTALL_DIR", r"C:\Program Files\TallySyncAgent"))
BACKUP_PATH = INSTALL_DIR / "TallySyncAgent.backup.exe"
CURRENT_EXE = INSTALL_DIR / "TallySyncAgent.exe"

# Grace period before restart (seconds) — lets current sync cycle finish
RESTART_DELAY_SECONDS = 300


class UpdateInfo:
    """Metadata about an available update."""

    def __init__(self, data: dict):
        self.version: str = data["version"]
        self.download_url: str = data["download_url"]
        self.checksum_sha256: str = data["checksum_sha256"]
        self.release_notes: str = data.get("release_notes", "")
        self.min_agent_version: str = data.get("min_agent_version", "0.0.0")
        self.is_critical: bool = data.get("is_critical", False)
        self.published_at: str = data.get("published_at", "")

    def __repr__(self):
        return f"<UpdateInfo version={self.version} critical={self.is_critical}>"


class UpdateManager:
    """
    Manages OTA updates for the Tally Sync Agent.

    Thread-safe: only one update check/apply runs at a time via a lock file.
    """

    def __init__(
        self,
        current_version: str = CURRENT_VERSION,
        update_url: str = DEFAULT_UPDATE_URL,
        install_dir: Path = INSTALL_DIR,
    ):
        self.current_version = current_version
        self.update_url = update_url
        self.install_dir = Path(install_dir)
        self._lock_path = self.install_dir / ".update.lock"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_and_apply(self) -> bool:
        """
        Full update cycle: check → download → verify → apply → schedule restart.

        Returns True if an update was applied.
        """
        if not self._acquire_lock():
            logger.info("Another update process is already running, skipping")
            return False

        try:
            update = self.check_for_update()
            if update is None:
                return False

            logger.info(f"Update available: {self.current_version} → {update.version}")

            exe_path = self._download(update)
            if exe_path is None:
                return False

            if not self._verify_checksum(exe_path, update.checksum_sha256):
                logger.error("Checksum mismatch — aborting update")
                exe_path.unlink(missing_ok=True)
                return False

            self._apply(exe_path)
            self._schedule_restart()
            logger.info(f"Update to {update.version} applied — restart scheduled")
            return True

        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return False

        finally:
            self._release_lock()

    def check_for_update(self) -> Optional[UpdateInfo]:
        """
        Query the update server and return UpdateInfo if a newer version exists.
        Returns None when already up-to-date or server is unreachable.
        """
        try:
            resp = requests.get(
                self.update_url,
                timeout=10,
                headers={"User-Agent": f"TallySyncAgent/{self.current_version}"},
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.warning(f"Update check failed (will retry tomorrow): {e}")
            return None

        try:
            update = UpdateInfo(data)
        except (KeyError, TypeError) as e:
            logger.warning(f"Malformed update response: {e}")
            return None

        if Version(update.version) <= Version(self.current_version):
            logger.info(f"Already on latest version {self.current_version}")
            return None

        # Skip update if we don't meet minimum agent version (shouldn't happen)
        if Version(self.current_version) < Version(update.min_agent_version):
            logger.warning(
                f"Update {update.version} requires agent >={update.min_agent_version}, "
                f"but we are {self.current_version}"
            )
            return None

        return update

    def rollback(self) -> bool:
        """Restore the backup exe if a bad update was applied."""
        if not BACKUP_PATH.exists():
            logger.error("No backup found — cannot rollback")
            return False

        try:
            shutil.copy2(BACKUP_PATH, CURRENT_EXE)
            BACKUP_PATH.unlink()
            logger.info("Rollback successful")
            self._schedule_restart()
            return True
        except OSError as e:
            logger.error(f"Rollback failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _download(self, update: UpdateInfo) -> Optional[Path]:
        """Download update exe into a temp file next to the install dir."""
        tmp_path = self.install_dir / f"TallySyncAgent.{update.version}.tmp"
        try:
            logger.info(f"Downloading {update.download_url}")
            with requests.get(update.download_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 64):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded * 100 // total
                            logger.debug(f"Download progress: {pct}%")

            logger.info(f"Download complete: {tmp_path} ({downloaded:,} bytes)")
            return tmp_path

        except Exception as e:
            logger.error(f"Download failed: {e}")
            tmp_path.unlink(missing_ok=True)
            return None

    def _verify_checksum(self, path: Path, expected_sha256: str) -> bool:
        """SHA-256 verify the downloaded file."""
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 64), b""):
                sha.update(chunk)
        actual = sha.hexdigest()
        if actual != expected_sha256.lower():
            logger.error(f"Checksum FAIL: expected={expected_sha256} got={actual}")
            return False
        logger.info("Checksum OK")
        return True

    def _apply(self, new_exe: Path):
        """
        Atomic swap:
          1. Backup current exe
          2. Move new exe into place
        On Windows, a running exe cannot be overwritten — the move defers
        the delete until next reboot, while the new file takes the name.
        """
        if CURRENT_EXE.exists():
            # Remove old backup first
            BACKUP_PATH.unlink(missing_ok=True)
            shutil.copy2(CURRENT_EXE, BACKUP_PATH)
            logger.info(f"Backed up current exe to {BACKUP_PATH}")

        # On Windows this works even if the exe is running (renames the old file,
        # places new file at the original path)
        shutil.move(str(new_exe), str(CURRENT_EXE))
        logger.info(f"New exe placed at {CURRENT_EXE}")

    def _schedule_restart(self):
        """
        Ask NSSM to restart the Windows service after RESTART_DELAY_SECONDS.
        Falls back to a simple subprocess restart when not running as a service.
        """
        service_name = os.getenv("AGENT_SERVICE_NAME", "TallySyncAgent")
        try:
            # Schedule a delayed service restart via Windows Task Scheduler
            restart_time = datetime.now(timezone.utc)
            at_time = time.strftime(
                "%H:%M",
                time.localtime(time.time() + RESTART_DELAY_SECONDS),
            )
            cmd = [
                "schtasks", "/create", "/f",
                "/tn", "TallySyncAgentRestart",
                "/tr", f'nssm restart "{service_name}"',
                "/sc", "once",
                "/st", at_time,
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Restart scheduled for {at_time} via Task Scheduler")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Could not schedule restart via schtasks: {e}")
            logger.info("Agent will restart on next manual start")

    def _acquire_lock(self) -> bool:
        """Simple file-based lock to prevent concurrent updates."""
        try:
            if self._lock_path.exists():
                age = time.time() - self._lock_path.stat().st_mtime
                if age < 1800:  # Stale after 30 minutes
                    return False
                self._lock_path.unlink()
            self._lock_path.write_text(str(os.getpid()))
            return True
        except OSError:
            return False

    def _release_lock(self):
        self._lock_path.unlink(missing_ok=True)
