# -*- coding: utf-8 -*-
"""
Windows Service wrapper for Tally Sync Agent.

Implements the Windows SCM protocol via pywin32 so the agent can be installed,
started, and stopped as a proper Windows service.

Install:   python -m agent.service install
Start:     python -m agent.service start
Stop:      python -m agent.service stop
Remove:    python -m agent.service remove
Debug:     python -m agent.service debug  (runs in foreground)
"""

from __future__ import annotations

import sys
import os
import logging
import time
from pathlib import Path

import win32serviceutil
import win32service
import win32event
import servicemanager

logger = logging.getLogger(__name__)

SERVICE_NAME = "TallySyncAgent"
SERVICE_DISPLAY = "Tally Sync Agent"
SERVICE_DESC = "Extracts accounting data from TallyPrime and syncs to cloud platform"


class TallySyncService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY
    _svc_description_ = SERVICE_DESC

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.poller = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.poller:
            self.poller.stop()
        logger.info("Service stop requested")

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self._run()

    def _run(self):
        # Set up logging to file (service has no console)
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
        log_dir = exe_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(log_dir / "agent.log", encoding="utf-8"),
            ],
        )

        logger.info("Tally Sync Agent service starting")

        try:
            from agent.config import Config
            Config.validate()
            logger.info(f"Config source: {Config.source_info()}")

            from agent.connector import ensure_tally_ready
            connector_exe = Path(Config.CONNECTOR_EXE_PATH)
            tally_ok = ensure_tally_ready(
                connector_exe=connector_exe,
                auto_launch_tally=Config.AUTO_LAUNCH_TALLY,
            )
            if tally_ok:
                logger.info("Tally HTTP API is ready")
            else:
                logger.warning("Tally HTTP API not ready — will retry on each command")

            from agent.engine import CommandEngine
            from agent.poller import CommandPoller

            engine = CommandEngine(tally_url=Config.TALLY_URL)
            self.poller = CommandPoller(
                cloud_base_url=Config.CLOUD_URL,
                device_id=Config.DEVICE_ID,
                api_key=Config.API_KEY,
                tenant_id=Config.TENANT_ID,
                engine=engine,
                poll_interval=Config.POLL_INTERVAL_SECONDS,
            )
            self.poller.start()
            logger.info(f"Poller started — polling every {Config.POLL_INTERVAL_SECONDS}s")

            # Wait for stop signal
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"TallySyncAgent error: {e}")

        logger.info("Service stopped")


def main():
    if len(sys.argv) == 1:
        # Started by SCM — run the service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TallySyncService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # CLI: install/start/stop/remove/debug
        win32serviceutil.HandleCommandLine(TallySyncService)


if __name__ == "__main__":
    main()
