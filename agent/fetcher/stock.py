# -*- coding: utf-8 -*-
"""StockFetcher — pull inventory master data from Tally."""

import logging
from typing import Any, Dict, List, Optional

from .base import TallyHTTPClient

logger = logging.getLogger(__name__)

_ITEM_FIELDS = [
    "Name", "Parent", "GUID", "MasterId",
    "BaseUnits", "Opening Balance", "Closing Balance",
    "HSNCode", "GSTRate",
]

_GROUP_FIELDS = ["Name", "Parent", "GUID", "MasterId"]


def _val(obj: Any, default: str = "") -> str:
    if isinstance(obj, dict):
        return str(obj.get("value", default) or default).strip()
    return str(obj).strip() if obj is not None else default


def _normalise_item(raw: Dict) -> Dict[str, Any]:
    meta = raw.get("metadata", {})
    return {
        "name":             meta.get("name", "").strip(),
        "guid":             _val(raw.get("guid")) or meta.get("name", ""),
        "master_id":        _val(raw.get("masterid")),
        "parent":           _val(raw.get("parent")),
        "base_units":       _val(raw.get("baseunits")),
        "opening_balance":  _val(raw.get("openingbalance")),
        "closing_balance":  _val(raw.get("closingbalance")),
        "hsn_code":         _val(raw.get("hsncode")),
        "gst_rate":         _val(raw.get("gstrate")),
    }


class StockFetcher:
    def __init__(self, client: TallyHTTPClient):
        self._c = client

    def pull_all_items(self, company: str) -> List[Dict[str, Any]]:
        raw = self._c.export_collection("StockItem", _ITEM_FIELDS, company=company)
        result = [_normalise_item(r) for r in raw if r.get("metadata", {}).get("name")]
        logger.info(f"[StockFetcher] {len(result)} stock items for '{company}'")
        return result

    def pull_item(self, company: str, name: str) -> Optional[Dict[str, Any]]:
        raw = self._c.export_object("StockItem", name, _ITEM_FIELDS, company=company)
        return _normalise_item(raw) if raw else None

    def pull_by_group(self, company: str, group: str) -> List[Dict[str, Any]]:
        extra = [{"name": "svStockGroupName", "value": group}]
        raw = self._c.export_collection(
            "StockItem", _ITEM_FIELDS, company=company, extra_static_vars=extra
        )
        result = [_normalise_item(r) for r in raw if r.get("metadata", {}).get("name")]
        logger.info(f"[StockFetcher] {len(result)} items in group '{group}'")
        return result

    def pull_zero_balance(self, company: str) -> List[Dict[str, Any]]:
        all_items = self.pull_all_items(company)
        zero = [i for i in all_items if i["closing_balance"] in ("0", "0.00", "")]
        logger.info(f"[StockFetcher] {len(zero)} zero-balance items for '{company}'")
        return zero

    def pull_all_groups(self, company: str) -> List[Dict[str, Any]]:
        raw = self._c.export_collection("StockGroup", _GROUP_FIELDS, company=company)
        return [
            {
                "name":      r.get("metadata", {}).get("name", "").strip(),
                "guid":      _val(r.get("guid")),
                "master_id": _val(r.get("masterid")),
                "parent":    _val(r.get("parent")),
            }
            for r in raw if r.get("metadata", {}).get("name")
        ]
