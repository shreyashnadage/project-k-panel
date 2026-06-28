# -*- coding: utf-8 -*-
"""
VoucherFetcher — pull transaction data from Tally via DayBook XML report.

The collection API for Voucher hangs Tally (too many records, no reliable filter).
The DayBook XML report is the standard Tally way to get date-range transactions.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

TALLY_URL = "http://localhost:9000"
REQUEST_TIMEOUT = 60  # DayBook can be slow for large date ranges


def _tally_date(s: str) -> Optional[str]:
    s = (s or "").strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s or None


class VoucherFetcher:
    def __init__(self, client=None):
        # client param kept for API consistency; DayBook uses its own HTTP call
        self._base_url = getattr(client, "base_url", TALLY_URL) if client else TALLY_URL

    def pull_by_date(
        self,
        company: str,
        from_date: str,   # YYYYMMDD
        to_date: str,     # YYYYMMDD
    ) -> List[Dict[str, Any]]:
        """Return all vouchers in a date range via DayBook report."""
        xml_resp = self._daybook_xml(company, from_date, to_date)
        result = _parse_daybook(xml_resp)
        logger.info(
            f"[VoucherFetcher] {len(result)} vouchers for '{company}' "
            f"[{from_date}–{to_date}]"
        )
        return result

    def pull_by_type(
        self,
        company: str,
        voucher_type: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict[str, Any]]:
        """Return vouchers filtered by type (client-side after DayBook fetch)."""
        all_vouchers = self.pull_by_date(company, from_date, to_date)
        vtype = voucher_type.lower()
        result = [
            v for v in all_vouchers
            if v.get("voucher_type", "").lower() == vtype
        ]
        logger.info(
            f"[VoucherFetcher] {len(result)} {voucher_type} vouchers after filter"
        )
        return result

    # ── DayBook XML report ─────────────────────────────────────────────────────

    def _daybook_xml(self, company: str, from_date: str, to_date: str) -> str:
        xml_body = (
            f"<ENVELOPE><HEADER>"
            f"<VERSION>1</VERSION>"
            f"<TALLYREQUEST>Export</TALLYREQUEST>"
            f"<TYPE>Data</TYPE>"
            f"<ID>DayBook</ID>"
            f"</HEADER><BODY><DESC><STATICVARIABLES>"
            f"<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
            f"<SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>"
            f"<SVFROMDATE>{from_date}</SVFROMDATE>"
            f"<SVTODATE>{to_date}</SVTODATE>"
            f"</STATICVARIABLES></DESC></BODY></ENVELOPE>"
        )
        try:
            resp = requests.post(
                self._base_url,
                data=xml_body.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"DayBook report timed out after {REQUEST_TIMEOUT}s. "
                "Try a shorter date range."
            )
        except Exception as e:
            raise RuntimeError(f"DayBook request failed: {e}") from e


def _parse_daybook(xml_text: str) -> List[Dict[str, Any]]:
    """
    Parse Tally DayBook XML into flat voucher dicts.

    DayBook XML structure (typical):
      <ENVELOPE>
        <DSPDAY>
          <DSPVCHDATE>20260601</DSPVCHDATE>
          <DSPVCHROWDET>
            <DSPVCHTYPE>Sales</DSPVCHTYPE>
            <DSPVCHREF>SAL-001</DSPVCHREF>
            <DSPVCHLEDNAME>ABC Party</DSPVCHLEDNAME>
            <DSPVCHDRAMT>50000.00</DSPVCHDRAMT>
            <DSPVCHCRAMT></DSPVCHCRAMT>
            <DSPVCHNARRATION>Sale to party</DSPVCHNARRATION>
          </DSPVCHROWDET>
        </DSPDAY>
      </ENVELOPE>
    """
    if not xml_text or not xml_text.strip().startswith("<"):
        logger.warning(f"DayBook: non-XML response ({xml_text[:100]})")
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"DayBook XML parse error: {e}\nSnippet: {xml_text[:300]}")
        return []

    vouchers: List[Dict[str, Any]] = []
    seen: set = set()

    for day_el in root.iter("DSPDAY"):
        date_raw = (day_el.findtext("DSPVCHDATE") or "").strip()
        date_iso = _tally_date(date_raw)

        for row in day_el.iter("DSPVCHROWDET"):
            vtype  = (row.findtext("DSPVCHTYPE") or "").strip()
            ref    = (row.findtext("DSPVCHREF") or "").strip()
            party  = (row.findtext("DSPVCHLEDNAME") or "").strip()
            dr_amt = (row.findtext("DSPVCHDRAMT") or "").strip()
            cr_amt = (row.findtext("DSPVCHCRAMT") or "").strip()
            narr   = (row.findtext("DSPVCHNARRATION") or "").strip()

            key = (date_raw, vtype, ref, party)
            if key in seen:
                continue
            seen.add(key)

            vouchers.append({
                "date":           date_iso,
                "voucher_type":   vtype,
                "voucher_number": ref,
                "party":          party,
                "amount_dr":      dr_amt,
                "amount_cr":      cr_amt,
                "narration":      narr,
            })

    # Fallback: flat DSPVCHROWDET without DSPDAY wrapper
    if not vouchers:
        for row in root.iter("DSPVCHROWDET"):
            vtype  = (row.findtext("DSPVCHTYPE") or "").strip()
            ref    = (row.findtext("DSPVCHREF") or "").strip()
            party  = (row.findtext("DSPVCHLEDNAME") or "").strip()
            dr_amt = (row.findtext("DSPVCHDRAMT") or "").strip()
            cr_amt = (row.findtext("DSPVCHCRAMT") or "").strip()
            narr   = (row.findtext("DSPVCHNARRATION") or "").strip()
            vouchers.append({
                "date": None, "voucher_type": vtype, "voucher_number": ref,
                "party": party, "amount_dr": dr_amt, "amount_cr": cr_amt,
                "narration": narr,
            })

    logger.info(f"[VoucherFetcher] Parsed {len(vouchers)} rows from DayBook XML")
    return vouchers
