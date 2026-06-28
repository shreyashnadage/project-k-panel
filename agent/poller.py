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
        tenant_id: str = "",
        engine: Optional[CommandEngine] = None,
        poll_interval: int = POLL_INTERVAL_BASE,
    ):
        self.cloud_base_url = cloud_base_url.rstrip("/")
        self.device_id      = device_id
        self.api_key        = api_key
        self.tenant_id      = tenant_id or device_id
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

    def _auth_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key}

    def _poll_pending(self) -> list:
        resp = requests.get(
            f"{self.cloud_base_url}/v1/commands/pending",
            params={"device_id": self.device_id},
            headers=self._auth_headers(),
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
                headers=self._auth_headers(),
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
                },
            )
            self._upload_data(result, company_name=engine_cmd["company_name"])
        else:
            self._ack_command(
                command_id, "failed",
                error_message=result.error,
            )

    def _upload_data(self, result: CommandResult, company_name: str = "") -> None:
        """POST data records to cloud ingest endpoint."""
        if not result.data:
            return

        upload_fn = {
            "ledger":      self._upload_ledgers,
            "voucher":     self._upload_vouchers,
            "group":       self._upload_groups,
            "stock_item":  self._upload_stock_items,
            "stock_group": self._upload_stock_groups,
        }.get(result.resource)

        if upload_fn:
            upload_fn(result, company_name)
        else:
            logger.info(
                f"[Poller] No ingest endpoint for '{result.resource}' yet — "
                f"{result.record_count} records fetched but not uploaded"
            )

    def _upload_ledgers(self, result: CommandResult, company_name: str) -> None:
        company_guid = result.company_id or company_name
        ledgers = []
        for r in result.data:
            ledgers.append({
                "company_guid": company_guid,
                "company_name": company_name,
                "ledger_guid": r.get("guid", r.get("name", "")),
                "name": r.get("name", ""),
                "parent": r.get("parent"),
                "ledger_type": r.get("ledger_type"),
                "opening_balance": r.get("opening_balance"),
                "closing_balance": r.get("closing_balance"),
            })

        payload = {"tenant_id": self.tenant_id, "ledgers": ledgers}
        self._post_ingest("/v1/ledgers", payload, "ledger", len(ledgers))

    def _upload_vouchers(self, result: CommandResult, company_name: str) -> None:
        company_guid = result.company_id or company_name
        vouchers = []
        for r in result.data:
            date_val = r.get("date") or "1900-01-01"
            vouchers.append({
                "company_guid": company_guid,
                "company_name": company_name,
                "voucher_guid": r.get("guid", r.get("voucher_number", "")),
                "voucher_type": r.get("voucher_type", "Journal"),
                "voucher_number": r.get("voucher_number"),
                "date": date_val,
                "party": r.get("party"),
                "narration": r.get("narration"),
                "amount": r.get("amount_dr") or r.get("amount_cr") or r.get("amount"),
            })

        payload = {"tenant_id": self.tenant_id, "vouchers": vouchers}
        self._post_ingest("/v1/vouchers", payload, "voucher", len(vouchers))

    def _upload_groups(self, result: CommandResult, company_name: str) -> None:
        company_guid = result.company_id or company_name
        groups = []
        for r in result.data:
            groups.append({
                "company_guid": company_guid,
                "company_name": company_name,
                "group_guid": r.get("guid", r.get("name", "")),
                "name": r.get("name", ""),
                "parent": r.get("parent"),
                "is_revenue": r.get("is_revenue"),
            })
        payload = {"tenant_id": self.tenant_id, "groups": groups}
        self._post_ingest("/v1/groups", payload, "group", len(groups))

    def _upload_stock_items(self, result: CommandResult, company_name: str) -> None:
        company_guid = result.company_id or company_name
        items = []
        for r in result.data:
            items.append({
                "company_guid": company_guid,
                "company_name": company_name,
                "item_guid": r.get("guid", r.get("name", "")),
                "name": r.get("name", ""),
                "parent": r.get("parent"),
                "base_units": r.get("base_units"),
                "opening_balance": r.get("opening_balance"),
                "closing_balance": r.get("closing_balance"),
                "hsn_code": r.get("hsn_code"),
                "gst_rate": r.get("gst_rate"),
            })
        payload = {"tenant_id": self.tenant_id, "stock_items": items}
        self._post_ingest("/v1/stock-items", payload, "stock_item", len(items))

    def _upload_stock_groups(self, result: CommandResult, company_name: str) -> None:
        company_guid = result.company_id or company_name
        groups = []
        for r in result.data:
            groups.append({
                "company_guid": company_guid,
                "company_name": company_name,
                "group_guid": r.get("guid", r.get("name", "")),
                "name": r.get("name", ""),
                "parent": r.get("parent"),
            })
        payload = {"tenant_id": self.tenant_id, "stock_groups": groups}
        self._post_ingest("/v1/stock-groups", payload, "stock_group", len(groups))

    def _post_ingest(self, endpoint: str, payload: dict, label: str, count: int) -> None:
        try:
            resp = requests.post(
                f"{self.cloud_base_url}{endpoint}",
                json=payload,
                headers=self._auth_headers(),
                timeout=60,
            )
            resp.raise_for_status()
            body = resp.json()
            logger.info(
                f"[Poller] Uploaded {count} {label}(s) — "
                f"accepted={body.get('accepted')}, duplicates={body.get('duplicates')}"
            )
        except Exception as e:
            logger.error(f"[Poller] Upload failed for {label}: {e}")
