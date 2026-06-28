# -*- coding: utf-8 -*-
"""
CommandEngine — routes a SyncCommand to the correct Tally fetcher.

Security: only operations in ALLOWED_OPS can be executed.
          Any other command is rejected before Tally is ever called.

SyncCommand params schema:
  {
    "company_name": "Bhrama Enterprises",   # required: Tally company name
    "company_id":   "comp_001",             # required: platform company id
    "resource":     "ledger",               # one of ALLOWED_OPS keys
    "action":       "pull_all",             # one of the allowed actions
    "params": {
      "name":         "Kotak Bank",         # for pull_one
      "group":        "Bank Accounts",      # for pull_by_group
      "from_date":    "20260601",           # for voucher date range
      "to_date":      "20260628",
      "voucher_type": "Sales",              # for pull_by_type
    }
  }
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .fetcher.base import TallyHTTPClient, TallyAPIError
from .fetcher.ledger import LedgerFetcher
from .fetcher.voucher import VoucherFetcher
from .fetcher.stock import StockFetcher
from .fetcher.group import GroupFetcher

logger = logging.getLogger(__name__)

# Allowlist: (resource, action) pairs permitted in MVP
ALLOWED_OPS: Dict[str, set] = {
    "ledger":      {"pull_all", "pull_one", "pull_by_group"},
    "group":       {"pull_all", "pull_one", "pull_subgroups"},
    "voucher":     {"pull_by_date", "pull_by_type"},
    "stock_item":  {"pull_all", "pull_by_group", "pull_zero_balance"},
    "stock_group": {"pull_all"},
}


class CommandResult:
    def __init__(
        self,
        success: bool,
        data: Optional[List[Dict]] = None,
        record_count: int = 0,
        error: Optional[str] = None,
        resource: str = "",
        action: str = "",
        company_id: str = "",
    ):
        self.success = success
        self.data = data or []
        self.record_count = record_count
        self.error = error
        self.resource = resource
        self.action = action
        self.company_id = company_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "resource": self.resource,
            "action": self.action,
            "company_id": self.company_id,
            "record_count": self.record_count,
            "error": self.error,
            "data": self.data,
        }


class CommandEngine:
    """
    Routes SyncCommand dicts to the correct fetcher and returns a CommandResult.

    One shared TallyHTTPClient is used across all fetchers — it holds the
    inter-request lock that prevents concurrent Tally calls.
    """

    def __init__(self, tally_url: str = "http://localhost:9000"):
        self._client = TallyHTTPClient(base_url=tally_url)
        self._ledger  = LedgerFetcher(self._client)
        self._voucher = VoucherFetcher(self._client)
        self._stock   = StockFetcher(self._client)
        self._group   = GroupFetcher(self._client)

    def execute(self, command: Dict[str, Any]) -> CommandResult:
        """
        Execute a SyncCommand dict.  Returns CommandResult (never raises).

        command should have: resource, action, company_name, company_id, params
        """
        resource   = (command.get("resource") or "").lower().strip()
        action     = (command.get("action") or "").lower().strip()
        company    = (command.get("company_name") or "").strip()
        company_id = (command.get("company_id") or "").strip()
        params     = command.get("params") or {}

        # --- security gate ---
        allowed = ALLOWED_OPS.get(resource, set())
        if action not in allowed:
            msg = f"Operation '{resource}/{action}' is not in the allowed list"
            logger.warning(f"[CommandEngine] REJECTED: {msg}")
            return CommandResult(
                success=False, error=msg,
                resource=resource, action=action, company_id=company_id
            )

        if not company:
            return CommandResult(
                success=False, error="company_name is required",
                resource=resource, action=action, company_id=company_id
            )

        logger.info(f"[CommandEngine] {resource}/{action} for '{company}' ({company_id})")

        try:
            data = self._dispatch(resource, action, company, params)
            return CommandResult(
                success=True, data=data, record_count=len(data),
                resource=resource, action=action, company_id=company_id
            )
        except TallyAPIError as e:
            logger.error(f"[CommandEngine] Tally error: {e}")
            return CommandResult(
                success=False, error=str(e),
                resource=resource, action=action, company_id=company_id
            )
        except Exception as e:
            logger.exception(f"[CommandEngine] Unexpected error")
            return CommandResult(
                success=False, error=f"Unexpected: {e}",
                resource=resource, action=action, company_id=company_id
            )

    def is_tally_ready(self) -> bool:
        return self._client.is_ready()

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def _dispatch(self, resource: str, action: str,
                  company: str, params: Dict) -> List[Dict]:
        if resource == "ledger":
            return self._dispatch_ledger(action, company, params)
        if resource == "group":
            return self._dispatch_group(action, company, params)
        if resource == "voucher":
            return self._dispatch_voucher(action, company, params)
        if resource == "stock_item":
            return self._dispatch_stock(action, company, params)
        if resource == "stock_group":
            return self._stock.pull_all_groups(company)
        raise ValueError(f"Unknown resource: {resource}")

    def _dispatch_ledger(self, action, company, params):
        if action == "pull_all":
            return self._ledger.pull_all(company)
        if action == "pull_one":
            r = self._ledger.pull_one(company, params["name"])
            return [r] if r else []
        if action == "pull_by_group":
            return self._ledger.pull_by_group(company, params["group"])

    def _dispatch_group(self, action, company, params):
        if action == "pull_all":
            return self._group.pull_all(company)
        if action == "pull_one":
            r = self._group.pull_one(company, params["name"])
            return [r] if r else []
        if action == "pull_subgroups":
            return self._group.pull_subgroups(company, params["parent"])

    def _dispatch_voucher(self, action, company, params):
        from_date = params.get("from_date", "")
        to_date   = params.get("to_date", "")
        if not from_date or not to_date:
            raise ValueError("from_date and to_date are required for voucher fetch")
        if action == "pull_by_date":
            return self._voucher.pull_by_date(company, from_date, to_date)
        if action == "pull_by_type":
            return self._voucher.pull_by_type(
                company, params.get("voucher_type", "Sales"), from_date, to_date
            )

    def _dispatch_stock(self, action, company, params):
        if action == "pull_all":
            return self._stock.pull_all_items(company)
        if action == "pull_by_group":
            return self._stock.pull_by_group(company, params["group"])
        if action == "pull_zero_balance":
            return self._stock.pull_zero_balance(company)
