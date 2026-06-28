# -*- coding: utf-8 -*-
"""
CompanyFetcher — discover Tally companies available on this machine.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import TallyHTTPClient

logger = logging.getLogger(__name__)

COMPANY_FIELDS = [
    "Name", "GUID", "FormalName", "StartingFrom", "BooksFrom",
    "BasicCurrencyName", "StateName", "GSTNumber",
]


class CompanyFetcher:
    def __init__(self, client: Optional[TallyHTTPClient] = None):
        self._client = client or TallyHTTPClient()

    def list_companies(self) -> List[Dict[str, Any]]:
        """Return all companies currently open in TallyPrime."""
        raw = self._client.export_collection("Company", ["Name"])
        companies = []
        for item in raw:
            name = ""
            if isinstance(item.get("name"), dict):
                name = item["name"].get("value", "")
            elif isinstance(item.get("metadata"), dict):
                name = item["metadata"].get("name", "")
            if name:
                companies.append({"name": name})

        logger.info(f"[CompanyFetcher] Found {len(companies)} company(ies) in Tally")
        return companies

    def get_company_details(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed info for a single company."""
        raw = self._client.export_object("Company", company_name, COMPANY_FIELDS)
        if not raw:
            return None

        def _val(obj, key):
            v = obj.get(key)
            if isinstance(v, dict):
                return v.get("value", "")
            return v or ""

        return {
            "name": _val(raw, "name") or company_name,
            "guid": _val(raw, "guid"),
            "formal_name": _val(raw, "formalname"),
            "starting_from": _val(raw, "startingfrom"),
            "books_from": _val(raw, "booksfrom"),
            "currency": _val(raw, "basiccurrencyname"),
            "state": _val(raw, "statename"),
            "gst_number": _val(raw, "gstnumber"),
        }
