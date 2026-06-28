# -*- coding: utf-8 -*-
"""
LedgerFetcher — pull ledger (chart of accounts) data from Tally.

Tally response field shape: {"type": "String", "value": "Bank Accounts"}
All fields are extracted as strings; callers normalise types as needed.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import TallyHTTPClient

logger = logging.getLogger(__name__)

_FETCH_FIELDS = [
    "Name", "Parent", "Opening Balance", "Closing Balance",
    "GUID", "LedgType", "MasterId",
]


def _val(obj: Any, default: str = "") -> str:
    if isinstance(obj, dict):
        return str(obj.get("value", default) or default).strip()
    return str(obj).strip() if obj is not None else default


def _normalise(raw: Dict) -> Dict[str, Any]:
    meta = raw.get("metadata", {})
    return {
        "name":            meta.get("name", "").strip(),
        "guid":            _val(raw.get("guid")) or meta.get("name", ""),
        "master_id":       _val(raw.get("masterid")),
        "parent":          _val(raw.get("parent")),
        "ledger_type":     _val(raw.get("ledgtype")),
        "opening_balance": _val(raw.get("ledopeningbalance") or raw.get("tbalopening")),
        "closing_balance": _val(raw.get("closingbalance")),
    }


class LedgerFetcher:
    def __init__(self, client: TallyHTTPClient):
        self._c = client

    def pull_all(self, company: str) -> List[Dict[str, Any]]:
        """Return all ledgers for a company."""
        raw = self._c.export_collection("Ledger", _FETCH_FIELDS, company=company)
        result = [_normalise(r) for r in raw if r.get("metadata", {}).get("name")]
        logger.info(f"[LedgerFetcher] {len(result)} ledgers for '{company}'")
        return result

    def pull_one(self, company: str, name: str) -> Optional[Dict[str, Any]]:
        """Return details of a single ledger by name."""
        raw = self._c.export_object("Ledger", name, _FETCH_FIELDS, company=company)
        if not raw:
            return None
        return _normalise(raw)

    def pull_by_group(self, company: str, group: str) -> List[Dict[str, Any]]:
        """Return all ledgers under a specific parent group (client-side filter)."""
        all_ledgers = self.pull_all(company)
        result = [l for l in all_ledgers if l["parent"].lower() == group.lower()]
        logger.info(f"[LedgerFetcher] {len(result)} ledgers in group '{group}'")
        return result
