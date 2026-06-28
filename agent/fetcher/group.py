# -*- coding: utf-8 -*-
"""GroupFetcher — pull account group hierarchy from Tally."""

import logging
from typing import Any, Dict, List, Optional

from .base import TallyHTTPClient

logger = logging.getLogger(__name__)

_FETCH_FIELDS = ["Name", "Parent", "GUID", "MasterId", "IsRevenueItem"]


def _val(obj: Any, default: str = "") -> str:
    if isinstance(obj, dict):
        return str(obj.get("value", default) or default).strip()
    return str(obj).strip() if obj is not None else default


def _normalise(raw: Dict) -> Dict[str, Any]:
    meta = raw.get("metadata", {})
    return {
        "name":       meta.get("name", "").strip(),
        "guid":       _val(raw.get("guid")) or meta.get("name", ""),
        "master_id":  _val(raw.get("masterid")),
        "parent":     _val(raw.get("parent")),
        "is_revenue": _val(raw.get("isrevenueitem")),
    }


class GroupFetcher:
    def __init__(self, client: TallyHTTPClient):
        self._c = client

    def pull_all(self, company: str) -> List[Dict[str, Any]]:
        raw = self._c.export_collection("Group", _FETCH_FIELDS, company=company)
        result = [_normalise(r) for r in raw if r.get("metadata", {}).get("name")]
        logger.info(f"[GroupFetcher] {len(result)} groups for '{company}'")
        return result

    def pull_one(self, company: str, name: str) -> Optional[Dict[str, Any]]:
        raw = self._c.export_object("Group", name, _FETCH_FIELDS, company=company)
        return _normalise(raw) if raw else None

    def pull_subgroups(self, company: str, parent: str) -> List[Dict[str, Any]]:
        extra = [{"name": "svGroupName", "value": parent}]
        raw = self._c.export_collection(
            "Group", _FETCH_FIELDS, company=company, extra_static_vars=extra
        )
        result = [_normalise(r) for r in raw if r.get("metadata", {}).get("name")]
        logger.info(f"[GroupFetcher] {len(result)} subgroups of '{parent}'")
        return result
