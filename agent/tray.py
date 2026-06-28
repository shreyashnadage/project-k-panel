# -*- coding: utf-8 -*-
"""
System tray icon for Tally Sync Agent.

Shows agent status in the Windows notification area with a context menu
for common operations. Runs the poller in a background thread and
updates the icon/tooltip based on connection state.
"""

from __future__ import annotations

import sys
import os
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

import pystray
from pystray import MenuItem, Menu

logger = logging.getLogger(__name__)

# Icon colours
COLOR_GREEN = (76, 175, 80)
COLOR_YELLOW = (255, 193, 7)
COLOR_RED = (244, 67, 54)
COLOR_GREY = (158, 158, 158)


def _create_icon_image(color: tuple, letter: str = "T") -> Image.Image:
    """Generate a 64x64 tray icon with a coloured circle and letter."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    try:
        font = ImageFont.truetype("segoeui.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((64 - tw) / 2, (64 - th) / 2 - 2), letter, fill="white", font=font)
    return img


class TrayStatus:
    STARTING = "starting"
    CONNECTED = "connected"
    TALLY_OFFLINE = "tally_offline"
    CLOUD_OFFLINE = "cloud_offline"
    NO_CREDENTIALS = "no_credentials"
    ERROR = "error"


_STATUS_CONFIG = {
    TrayStatus.STARTING:       (COLOR_GREY,   "Tally Sync Agent — Starting..."),
    TrayStatus.CONNECTED:      (COLOR_GREEN,  "Tally Sync Agent — Connected"),
    TrayStatus.TALLY_OFFLINE:  (COLOR_YELLOW, "Tally Sync Agent — Tally offline"),
    TrayStatus.CLOUD_OFFLINE:  (COLOR_YELLOW, "Tally Sync Agent — Cloud unreachable"),
    TrayStatus.NO_CREDENTIALS: (COLOR_RED,    "Tally Sync Agent — Not registered"),
    TrayStatus.ERROR:          (COLOR_RED,    "Tally Sync Agent — Error"),
}


class AgentTray:
    """System tray application that wraps the agent poller."""

    def __init__(self):
        self._status = TrayStatus.STARTING
        self._icon: Optional[pystray.Icon] = None
        self._poller = None
        self._poller_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._app_dir = self._get_app_dir()

    @staticmethod
    def _get_app_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent

    def _set_status(self, status: str):
        self._status = status
        color, tooltip = _STATUS_CONFIG.get(status, (COLOR_GREY, "Tally Sync Agent"))
        if self._icon:
            self._icon.icon = _create_icon_image(color)
            self._icon.title = tooltip

    # ── Menu actions ──────────────────────────────────────────────────────

    def _on_open_logs(self, icon, item):
        log_dir = self._app_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "agent.log"
        if log_file.exists():
            os.startfile(str(log_file))
        else:
            os.startfile(str(log_dir))

    def _on_open_config(self, icon, item):
        config_file = self._app_dir / "config" / "agent.env"
        if config_file.exists():
            os.startfile(str(config_file))

    def _on_register(self, icon, item):
        wizard = self._app_dir / "registration_wizard.exe"
        if wizard.exists():
            subprocess.Popen([str(wizard)], cwd=str(self._app_dir))
        else:
            # Dev mode — run the wizard script directly
            try:
                subprocess.Popen(
                    [sys.executable, "-m", "installer.wizard.registration_wizard"],
                    cwd=str(self._app_dir),
                )
            except Exception as e:
                logger.error(f"Failed to launch wizard: {e}")

    def _on_restart_sync(self, icon, item):
        """Stop and restart the poller."""
        if self._poller:
            self._poller.stop()
        self._start_poller()

    def _on_quit(self, icon, item):
        self._stop_event.set()
        if self._poller:
            self._poller.stop()
        if self._icon:
            self._icon.stop()

    def _status_text(self, item):
        _, tooltip = _STATUS_CONFIG.get(self._status, (None, "Unknown"))
        return tooltip

    # ── Agent lifecycle ───────────────────────────────────────────────────

    def _has_credentials(self) -> bool:
        try:
            from .registration import is_registered
            return is_registered()
        except Exception:
            pass
        # Fallback: check env vars
        return bool(os.environ.get("AGENT_API_KEY"))

    def _start_poller(self):
        """Start the poller in a background thread."""
        self._poller_thread = threading.Thread(
            target=self._run_agent, name="AgentPoller", daemon=True,
        )
        self._poller_thread.start()

    def _run_agent(self):
        from .telemetry import init as init_telemetry, set_user_context, capture_exception

        init_telemetry(component="tray")

        try:
            from .config import Config
            Config.validate()
            set_user_context(client_id=Config.TENANT_ID, device_id=Config.DEVICE_ID)
        except RuntimeError as e:
            logger.error(f"Config error: {e}")
            capture_exception(e, stage="tray_config")
            self._set_status(TrayStatus.NO_CREDENTIALS)
            return

        logger.info(f"Config source: {Config.source_info()}")

        # Try to connect to Tally
        from .connector import ensure_tally_ready

        connector_exe = Path(Config.CONNECTOR_EXE_PATH)
        tally_ok = ensure_tally_ready(
            connector_exe=connector_exe,
            auto_launch_tally=Config.AUTO_LAUNCH_TALLY,
        )

        if not tally_ok:
            self._set_status(TrayStatus.TALLY_OFFLINE)
            logger.warning("Tally offline — will retry on each command")
        else:
            self._set_status(TrayStatus.CONNECTED)

        # Start poller
        from .engine import CommandEngine
        from .poller import CommandPoller

        engine = CommandEngine(tally_url=Config.TALLY_URL)
        self._poller = CommandPoller(
            cloud_base_url=Config.CLOUD_URL,
            device_id=Config.DEVICE_ID,
            api_key=Config.API_KEY,
            tenant_id=Config.TENANT_ID,
            engine=engine,
            poll_interval=Config.POLL_INTERVAL_SECONDS,
        )
        self._poller.start()
        self._set_status(TrayStatus.CONNECTED)
        logger.info(f"Poller started — polling every {Config.POLL_INTERVAL_SECONDS}s")

        # Health check loop — update tray status periodically
        while not self._stop_event.is_set():
            self._stop_event.wait(30)
            if self._stop_event.is_set():
                break
            try:
                from .connector import _tally_http_ready
                if _tally_http_ready():
                    if self._status != TrayStatus.CONNECTED:
                        self._set_status(TrayStatus.CONNECTED)
                else:
                    self._set_status(TrayStatus.TALLY_OFFLINE)
            except Exception:
                pass

    # ── Entry point ───────────────────────────────────────────────────────

    def run(self):
        """Start the tray icon and agent."""
        # Set up logging
        log_dir = self._app_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(log_dir / "agent.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

        logger.info("Tally Sync Agent tray starting")

        # Check credentials — launch wizard if missing
        if not self._has_credentials():
            logger.info("No credentials found — launching registration wizard")
            self._on_register(None, None)
            self._set_status(TrayStatus.NO_CREDENTIALS)

            # Wait for wizard to complete (poll for credentials)
            for _ in range(120):  # 2 minutes max
                time.sleep(1)
                if self._has_credentials():
                    logger.info("Credentials detected after wizard — starting agent")
                    break
            else:
                logger.warning("Wizard closed without registering — tray will show as unregistered")

        # Build menu
        menu = Menu(
            MenuItem(self._status_text, lambda icon, item: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Restart Sync", self._on_restart_sync),
            MenuItem("Re-register Device", self._on_register),
            Menu.SEPARATOR,
            MenuItem("Open Logs", self._on_open_logs),
            MenuItem("Open Config", self._on_open_config),
            Menu.SEPARATOR,
            MenuItem("Quit", self._on_quit),
        )

        self._icon = pystray.Icon(
            name="TallySyncAgent",
            icon=_create_icon_image(COLOR_GREY),
            title="Tally Sync Agent — Starting...",
            menu=menu,
        )

        # Start the agent poller if credentials exist
        if self._has_credentials():
            self._start_poller()

        # This blocks until icon.stop() is called
        self._icon.run()


def main():
    tray = AgentTray()
    tray.run()
