# -*- coding: utf-8 -*-
"""
CommandPoller — long-polls the cloud for pending SyncCommands,
executes them via CommandEngine, uploads results.

Loop: GET /v1/commands/pending → execute → PATCH /v1/commands/{id}
Interval: 15s base, exponential backoff on errors (cap 5min)
"""

import json
import logging
import time
import threading
from typing import Any, Dict, Optional

import requests

from .engine import CommandEngine, CommandResult

logger = logging.getLogger(__name__)

# Map cloud command_type → engine (resource, action)
COMMAND_TYPE_MAP: Dict[str, Dict[str, str]] = {
    "sync_ledgers":         {"resource": "ledger",  "action": "pull_all"},
    "sync_ledgers_by_group":{"resource": "ledger",  "action": "pull_by_group"},
    "sync_ledger_one":      {"resource": "ledger",  "action": "pull_one"},
    "sync_groups":          {"resource": "group",   "action": "pull_all"},
    "sync_vouchers":        {"resource": "voucher", "action": "pull_by_date"},
    "sync_vouchers_by_type":{"resource": "voucher", "action": "pull_by_type"},
    "sync_stock":           {"resource": "stock_item", "action": "pull_all"},
    "sync_stock_by_group":  {"resource": "stock_item", "action": "pull_by_group"},
    "health_check":         None,   # handled separately
}

POLL_INTERVAL_BASE = 15    # seconds
POLL_INTERVAL_MAX  = 300   # 5 minutes on error


class CommandPoller:
    """
    Background thread that polls the cloud for commands and dispatches them.

    The engine's TallyHTTPClient holds an inter-request lock — this class
    does NOT send concurrent requests to Tally.
    """

    def __init__(
        self,
        cloud_base_url: str,
        device_id: str,
        api_key: str,
        engine: Optional[CommandEngine] = None,
        poll_interval: int = POLL_INTERVAL_BASE,
    ):
        self.cloud_base_url = cloud_base_url.rstrip("/")
        self.device_id      = device_id
        self.api_key        = api_key
        self.engine         = engine or CommandEngine()
        self.poll_interval  = poll_interval
        self._stop_event    = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="CommandPoller", daemon=True)
        self._thread.start()
        logger.info(f"[Poller] Started — polling every {self.poll_interval}s")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        backoff = self.poll_interval
        while not self._stop_event.is_set():
            try:
                commands = self._poll_pending()
                if commands:
                    for cmd in commands:
                        self._handle(cmd)
                    backoff = self.poll_interval  # reset on success
                else:
                    backoff = self.poll_interval  # no commands is fine
            except requests.exceptions.ConnectionError:
                logger.warning("[Poller] Cloud unreachable — will retry")
                backoff = min(backoff * 2, POLL_INTERVAL_MAX)
            except Exception as e:
                logger.error(f"[Poller] Unexpected error: {e}")
                backoff = min(backoff * 2, POLL_INTERVAL_MAX)

            self._stop_event.wait(backoff)

    # ── Cloud API calls ───────────────────────────────────────────────────────

    def _poll_pending(self) -> list:
        resp = requests.get(
            f"{self.cloud_base_url}/v1/commands/pending",
            params={"device_id": self.device_id},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            logger.info(f"[Poller] Received {len(data)} command(s)")
        return data

    def _ack_command(
        self,
        command_id: str,
        status: str,
        result: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ) -> None:
        body: Dict[str, Any] = {"status": status}
        if result:
            body["result"] = result
        if error_message:
            body["error_message"] = error_message

        try:
            resp = requests.patch(
                f"{self.cloud_base_url}/v1/commands/{command_id}",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
            resp.raise_for_status()
            logger.info(f"[Poller] Command {command_id} acknowledged: {status}")
        except Exception as e:
            logger.error(f"[Poller] Failed to ack command {command_id}: {e}")
            # Not fatal — cloud already marked it 'fetched'; will expire naturally

    # ── Command handling ──────────────────────────────────────────────────────

    def _handle(self, cmd: Dict[str, Any]) -> None:
        command_id   = cmd.get("id", "unknown")
        command_type = cmd.get("command_type", "")
        params       = cmd.get("params", {})

        logger.info(f"[Poller] Handling {command_type} (id={command_id})")

        # ── health check ──────────────────────────────────────────────────────
        if command_type == "health_check":
            ready = self.engine.is_tally_ready()
            self._ack_command(
                command_id, "completed",
                result={"tally_ready": ready, "device_id": self.device_id},
            )
            return

        # ── data fetch ────────────────────────────────────────────────────────
        mapping = COMMAND_TYPE_MAP.get(command_type)
        if not mapping:
            self._ack_command(
                command_id, "failed",
                error_message=f"Unknown command_type: {command_type}",
            )
            return

        engine_cmd = {
            "resource":     mapping["resource"],
            "action":       mapping["action"],
            "company_name": params.get("company_name", ""),
            "company_id":   params.get("company_id", ""),
            "params":       params,
        }

        result: CommandResult = self.engine.execute(engine_cmd)

        if result.success:
            self._ack_command(
                command_id, "completed",
                result={
                    "record_count": result.record_count,
                    "resource": result.resource,
                    "action": result.action,
                    "company_id": result.company_id,
                    # data NOT sent in ack — uploaded separately via ingest API
                },
            )
            # Upload the actual data records
            self._upload_data(result)
        else:
            self._ack_command(
                command_id, "failed",
                error_message=result.error,
            )

    def _upload_data(self, result: CommandResult) -> None:
        """POST data records to cloud ingest endpoint."""
        if not result.data:
            return

        endpoint_map = {
            "ledger":      "/v1/ingest/ledgers",
            "group":       "/v1/ingest/groups",
            "voucher":     "/v1/ingest/vouchers",
            "stock_item":  "/v1/ingest/stock",
            "stock_group": "/v1/ingest/stock-groups",
        }

        endpoint = endpoint_map.get(result.resource)
        if not endpoint:
            logger.warning(f"[Poller] No ingest endpoint for resource '{result.resource}'")
            return

        payload = {
            "company_id": result.company_id,
            "records":    result.data,
        }

        try:
            resp = requests.post(
                f"{self.cloud_base_url}{endpoint}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            resp.raise_for_status()
            logger.info(
                f"[Poller] Uploaded {result.record_count} {result.resource} records "
                f"for company {result.company_id}"
            )
        except Exception as e:
            logger.error(f"[Poller] Upload failed for {result.resource}: {e}")
            # TODO Phase 3: queue locally and retry
