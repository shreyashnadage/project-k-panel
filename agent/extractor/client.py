# -*- coding: utf-8 -*-
"""
Tally HTTP Client — TallyPrime 3.x JSON API

TallyPrime 3.x exposes a JSON REST API on port 9000.
Request metadata goes in HTTP headers; body is JSON.

Response shape (collection):
  {"status": "1", "data": {"collection": [{"metadata": {...}, "field": {"type": "...", "value": "..."}}]}}

Critical constraints:
- Tally is single-threaded: NEVER send concurrent requests
- TallyAPIConnectorV2.0.exe must be running FIRST — it activates Tally's HTTP server
- Enforce 500ms inter-request delay
"""

import time
import logging
from typing import Optional, Dict, List, Any

import requests

logger = logging.getLogger(__name__)

TALLY_URL = "http://localhost:9000"
DEFAULT_INTER_REQUEST_DELAY_MS = 500
REQUEST_TIMEOUT_SECONDS = 30


class TallyClient:
    """
    HTTP client for TallyPrime 3.x JSON API.

    Thread safety: single-threaded only.
    """

    def __init__(self, base_url: str = TALLY_URL, delay_ms: int = DEFAULT_INTER_REQUEST_DELAY_MS):
        self.base_url = base_url.rstrip("/")
        self.delay_ms = delay_ms
        self._last_request_at: float = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def get_ledgers(self, company_name: str) -> List[Dict[str, Any]]:
        """Return all ledgers for the given company."""
        resp = self._post_json(
            headers={
                "Content-Type": "application/json",
                "version": "1",
                "tallyrequest": "export",
                "type": "collection",
                "subtype": "Ledger",
                "id": "Ledger",        # must match subtype; unknown IDs hang Tally
            },
            body={
                "static_variables": [
                    {"name": "svExportFormat", "value": "jsonEx"},
                    {"name": "svCurrentCompany", "value": company_name},
                ],
                "fetch_list": ["Name", "Parent", "Opening Balance", "Closing Balance", "GUID", "LedgType"],
            },
        )
        return _parse_collection(resp, "ledger")

    def get_vouchers(
        self,
        company_name: str,
        from_date: str,  # YYYYMMDD
        to_date: str,    # YYYYMMDD
    ) -> List[Dict[str, Any]]:
        """Return vouchers for the company and date range via DayBook XML report."""
        resp = self._post_xml_report(
            company_name=company_name,
            report_id="DayBook",
            from_date=from_date,
            to_date=to_date,
        )
        return _parse_daybook(resp)

    def is_reachable(self) -> bool:
        """
        Check if Tally's HTTP API is responding.
        Uses a lightweight XML ping (Trial Balance header check).
        Returns False if TallyAPIConnectorV2.0.exe is not running.
        """
        xml = (
            "<ENVELOPE><HEADER><VERSION>1</VERSION>"
            "<TALLYREQUEST>Export</TALLYREQUEST>"
            "<TYPE>Data</TYPE><ID>Trial Balance</ID></HEADER>"
            "<BODY><DESC><STATICVARIABLES>"
            "<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
            "</STATICVARIABLES></DESC></BODY></ENVELOPE>"
        )
        try:
            resp = requests.post(
                self.base_url,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False

    # ── Low-level helpers ─────────────────────────────────────────────────────

    def _post_json(self, headers: Dict, body: Dict) -> Dict[str, Any]:
        """POST a JSON request to Tally, enforce inter-request delay."""
        self._enforce_delay()
        try:
            resp = requests.post(
                self.base_url,
                headers=headers,
                json=body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            self._last_request_at = time.monotonic()
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as exc:
            raise TallyConnectionError(
                f"Cannot reach Tally at {self.base_url}. "
                "Is TallyPrime open and TallyAPIConnectorV2.0.exe running?"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise TallyTimeoutError(
                f"Tally did not respond within {REQUEST_TIMEOUT_SECONDS}s. "
                "Is TallyAPIConnectorV2.0.exe running? Is another request in flight?"
            ) from exc
        except Exception as exc:
            raise TallyResponseError(f"Tally request failed: {exc}") from exc

    def _post_xml_report(
        self,
        company_name: str,
        report_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> str:
        """POST an XML report request to Tally; returns raw response text."""
        date_vars = ""
        if from_date:
            date_vars += f"<SVFROMDATE>{from_date}</SVFROMDATE>"
        if to_date:
            date_vars += f"<SVTODATE>{to_date}</SVTODATE>"

        xml = (
            f"<ENVELOPE><HEADER>"
            f"<VERSION>1</VERSION>"
            f"<TALLYREQUEST>Export</TALLYREQUEST>"
            f"<TYPE>Data</TYPE>"
            f"<ID>{report_id}</ID>"
            f"</HEADER><BODY><DESC><STATICVARIABLES>"
            f"<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
            f"<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>"
            f"{date_vars}"
            f"</STATICVARIABLES></DESC></BODY></ENVELOPE>"
        )
        self._enforce_delay()
        try:
            resp = requests.post(
                self.base_url,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            self._last_request_at = time.monotonic()
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.ConnectionError as exc:
            raise TallyConnectionError(
                f"Cannot reach Tally at {self.base_url}."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise TallyTimeoutError(
                f"Tally DayBook report timed out after {REQUEST_TIMEOUT_SECONDS}s."
            ) from exc
        except Exception as exc:
            raise TallyResponseError(f"Tally XML report failed: {exc}") from exc

    def _enforce_delay(self) -> None:
        elapsed_ms = (time.monotonic() - self._last_request_at) * 1000
        if elapsed_ms < self.delay_ms:
            time.sleep((self.delay_ms - elapsed_ms) / 1000)


# ── Response parsers ──────────────────────────────────────────────────────────

def _val(field_obj: Any, default: str = "") -> str:
    """Extract .value from a Tally JSON field object."""
    if isinstance(field_obj, dict):
        return str(field_obj.get("value", default) or default)
    return str(field_obj) if field_obj is not None else default


def _parse_collection(raw: Dict, label: str) -> List[Dict[str, Any]]:
    """
    Parse a Tally collection response.

    Shape: {"status": "1", "data": {"collection": [{metadata: {...}, field: {type, value}}]}}
    """
    if str(raw.get("status")) != "1":
        err = raw.get("error_list", raw.get("error", raw))
        logger.warning(f"Tally {label} collection error: {err}")
        return []

    items = raw.get("data", {}).get("collection", [])
    if not isinstance(items, list):
        logger.warning(f"Unexpected Tally {label} shape: {type(items)}")
        return []

    result = []
    for item in items:
        meta = item.get("metadata", {})
        entry: Dict[str, Any] = {
            "name": meta.get("name", "").strip(),
            "guid": _val(item.get("guid")) or meta.get("name", ""),
            "parent": _val(item.get("parent")),
            "ledger_type": _val(item.get("ledgtype")),
            "opening_balance": _val(item.get("ledopeningbalance") or item.get("tbalopening")),
            "closing_balance": _val(item.get("closingbalance")),
        }
        if entry["name"]:
            result.append(entry)

    logger.info(f"Parsed {len(result)} {label}(s) from Tally")
    return result


def _parse_daybook(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse Tally DayBook XML response.

    Tally returns XML for the DayBook report even when JSON is requested.
    We extract DAYBOOK/DSPVCHDATE + DSPVCHTYPE + DSPVCHREF + DSPVCHLEDNAME + DSPVCHAMT.
    Returns a list of flat dicts — one per voucher display row.
    """
    import xml.etree.ElementTree as ET

    if not raw_text or not raw_text.strip().startswith("<"):
        logger.warning(f"DayBook response is not XML: {raw_text[:200]}")
        return []

    try:
        root = ET.fromstring(raw_text)
    except ET.ParseError as exc:
        logger.error(f"Failed to parse DayBook XML: {exc}")
        return []

    vouchers = []
    seen_guids: set = set()

    # DayBook XML has DSPVCHDATE rows — collect unique voucher entries
    for row in root.iter("DSPDAY"):
        date = (row.findtext("DSPVCHDATE") or "").strip()
        for vch_row in row.iter("DSPVCHROWDET"):
            vch_type = (vch_row.findtext("DSPVCHTYPE") or "").strip()
            vch_ref  = (vch_row.findtext("DSPVCHREF") or "").strip()
            party    = (vch_row.findtext("DSPVCHLEDNAME") or "").strip()
            amt_dr   = (vch_row.findtext("DSPVCHDRAMT") or "").strip()
            amt_cr   = (vch_row.findtext("DSPVCHCRAMT") or "").strip()
            narration = (vch_row.findtext("DSPVCHNARRATION") or "").strip()

            key = (date, vch_type, vch_ref)
            if key in seen_guids:
                continue
            seen_guids.add(key)

            vouchers.append({
                "date": _tally_date_to_iso(date),
                "voucher_type": vch_type,
                "voucher_number": vch_ref,
                "party": party,
                "amount_dr": amt_dr,
                "amount_cr": amt_cr,
                "narration": narration,
            })

    if not vouchers:
        # Fallback: try flat DSPVCHROWDET without DSPDAY wrapper
        for vch_row in root.iter("DSPVCHROWDET"):
            date_el = vch_row.find("../DSPVCHDATE")
            date = (date_el.text if date_el is not None else "").strip()
            vouchers.append({
                "date": _tally_date_to_iso(date),
                "voucher_type": (vch_row.findtext("DSPVCHTYPE") or "").strip(),
                "voucher_number": (vch_row.findtext("DSPVCHREF") or "").strip(),
                "party": (vch_row.findtext("DSPVCHLEDNAME") or "").strip(),
                "amount_dr": (vch_row.findtext("DSPVCHDRAMT") or "").strip(),
                "amount_cr": (vch_row.findtext("DSPVCHCRAMT") or "").strip(),
                "narration": (vch_row.findtext("DSPVCHNARRATION") or "").strip(),
            })

    logger.info(f"Parsed {len(vouchers)} voucher row(s) from DayBook XML")
    return vouchers


def _tally_date_to_iso(date_str: str) -> Optional[str]:
    """Convert Tally YYYYMMDD → YYYY-MM-DD. Returns None if invalid."""
    if not date_str:
        return None
    s = date_str.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s or None


# ── Exceptions ────────────────────────────────────────────────────────────────

class TallyConnectionError(Exception):
    pass

class TallyTimeoutError(Exception):
    pass

class TallyResponseError(Exception):
    pass
