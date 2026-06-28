# -*- coding: utf-8 -*-
"""
VoucherFetcher — pull transaction data from Tally via DayBook XML report.

The collection API for Voucher hangs Tally (too many records, no reliable filter).
The DayBook XML report is the standard Tally way to get date-range transactions.
"""

import logging
import re
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


def _sanitize_xml(text: str) -> str:
    """Remove characters that are illegal in XML 1.0."""
    # Strip invalid XML character references
    text = re.sub(r"&#x[0-9a-fA-F]{1,2};", "", text)
    text = re.sub(r"&#[0-9]+;", lambda m: m.group() if int(m.group()[2:-1]) >= 32 else "", text)
    # Strip raw control characters (0x00-0x08, 0x0B-0x0C, 0x0E-0x1F) except tab/newline/CR
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text


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

    xml_text = _sanitize_xml(xml_text)

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

    # Fallback: Tally may return full <VOUCHER> elements instead of DSP format
    if not vouchers:
        for vch in root.iter("VOUCHER"):
            date_raw = (vch.findtext("DATE") or "").strip()
            vtype    = (vch.attrib.get("VCHTYPE") or vch.findtext("VOUCHERTYPENAME") or "").strip()
            ref      = (vch.findtext("VOUCHERNUMBER") or "").strip()
            guid     = (vch.attrib.get("REMOTEID") or vch.findtext("GUID") or "").strip()
            narr     = (vch.findtext("NARRATION") or "").strip()

            # Party: first PARTYLEDGERNAME, or first LEDGERNAME in ledger entries
            party = (vch.findtext("PARTYLEDGERNAME") or "").strip()
            if not party:
                ledger_el = vch.find(".//LEDGERENTRIES.LIST/LEDGERNAME")
                if ledger_el is not None:
                    party = (ledger_el.text or "").strip()

            # Amount: find the party's ledger entry (largest absolute value)
            amounts = []
            for entry_el in vch.findall(".//LEDGERENTRIES.LIST"):
                amt_el = entry_el.find("AMOUNT")
                if amt_el is not None and amt_el.text:
                    try:
                        amounts.append(float(amt_el.text.strip()))
                    except ValueError:
                        pass

            # The total invoice amount is the largest absolute value entry
            total = max(amounts, key=abs) if amounts else 0.0
            amount_str = f"{abs(total):.2f}"

            key = (date_raw, vtype, ref, guid or party)
            if key in seen:
                continue
            seen.add(key)

            vouchers.append({
                "date":           _tally_date(date_raw),
                "voucher_type":   vtype,
                "voucher_number": ref,
                "guid":           guid,
                "party":          party,
                "amount_dr":      amount_str if total > 0 else "",
                "amount_cr":      amount_str if total <= 0 else "",
                "narration":      narr,
            })

    logger.info(f"[VoucherFetcher] Parsed {len(vouchers)} rows from DayBook XML")
    return vouchers
