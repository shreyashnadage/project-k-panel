"""
Unit tests for Tally XML parser

Tests use pre-recorded Tally XML fixtures (no live Tally connection needed).
All tests should pass in CI/CD pipeline.
"""

import pytest
from agent.extractor.parser import (
    parse_vouchers,
    parse_ledgers,
    _parse_tally_date,
    _parse_int,
)


# Sample Tally XML responses (pre-recorded from actual Tally)
SAMPLE_VOUCHER_XML = """<?xml version="1.0" encoding="utf-16"?>
<ENVELOPE>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <VOUCHER>
          <GUID>VOUCH-001-GUID</GUID>
          <ALTERID>101</ALTERID>
          <DATE>20260601</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <VOUCHERNUMBER>S/001</VOUCHERNUMBER>
          <PARTYLEDGERNAME>Rahul Enterprises</PARTYLEDGERNAME>
          <NARRATION>Sale of goods</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Rahul Enterprises</LEDGERNAME>
            <AMOUNT>-50000</AMOUNT>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Sales Account</LEDGERNAME>
            <AMOUNT>50000</AMOUNT>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""

DEVANAGARI_VOUCHER_XML = """<?xml version="1.0" encoding="utf-16"?>
<ENVELOPE>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <VOUCHER>
          <GUID>DEVA-0001-GUID</GUID>
          <ALTERID>1</ALTERID>
          <DATE>20260601</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <VOUCHERNUMBER>1</VOUCHERNUMBER>
          <PARTYLEDGERNAME>रमेश ट्रेडर्स</PARTYLEDGERNAME>
          <NARRATION></NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>रमेश ट्रेडर्स</LEDGERNAME>
            <AMOUNT>-100000</AMOUNT>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Sales</LEDGERNAME>
            <AMOUNT>100000</AMOUNT>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""

MULTIPLE_VOUCHERS_XML = """<?xml version="1.0" encoding="utf-16"?>
<ENVELOPE>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <VOUCHER>
          <GUID>V001</GUID>
          <ALTERID>1</ALTERID>
          <DATE>20260601</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <VOUCHERNUMBER>S/001</VOUCHERNUMBER>
          <PARTYLEDGERNAME>Party A</PARTYLEDGERNAME>
          <NARRATION>Sale 1</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Party A</LEDGERNAME>
            <AMOUNT>-10000</AMOUNT>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
        <VOUCHER>
          <GUID>V002</GUID>
          <ALTERID>2</ALTERID>
          <DATE>20260602</DATE>
          <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
          <VOUCHERNUMBER>P/001</VOUCHERNUMBER>
          <PARTYLEDGERNAME>Supplier B</PARTYLEDGERNAME>
          <NARRATION>Purchase 1</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Supplier B</LEDGERNAME>
            <AMOUNT>5000</AMOUNT>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""

VOUCHER_NO_GUID_XML = """<?xml version="1.0" encoding="utf-16"?>
<ENVELOPE>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <VOUCHER>
          <ALTERID>999</ALTERID>
          <DATE>20260601</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <VOUCHERNUMBER>S/999</VOUCHERNUMBER>
        </VOUCHER>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""

SAMPLE_LEDGER_XML = """<?xml version="1.0" encoding="utf-16"?>
<ENVELOPE>
  <BODY>
    <DATA>
      <TALLYMESSAGE>
        <LEDGER>
          <GUID>LED-001</GUID>
          <NAME>Cash</NAME>
          <LEDGTYPE>Asset</LEDGTYPE>
          <OPENINGBALANCE>50000</OPENINGBALANCE>
        </LEDGER>
        <LEDGER>
          <GUID>LED-002</GUID>
          <NAME>Sales</NAME>
          <LEDGTYPE>Income</LEDGTYPE>
          <OPENINGBALANCE>0</OPENINGBALANCE>
        </LEDGER>
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""


class TestVoucherParser:
    """Test voucher XML parsing"""

    def test_parses_single_voucher(self):
        """Basic voucher parsing"""
        vouchers = parse_vouchers(SAMPLE_VOUCHER_XML)
        assert len(vouchers) == 1
        v = vouchers[0]
        assert v["guid"] == "VOUCH-001-GUID"
        assert v["alterid"] == 101
        assert v["date"] == "2026-06-01"
        assert v["voucher_type"] == "Sales"
        assert v["voucher_number"] == "S/001"
        assert v["party_ledger_name"] == "Rahul Enterprises"
        assert v["narration"] == "Sale of goods"
        assert len(v["line_items"]) == 2

    def test_line_items_parsed_correctly(self):
        """Line items have correct structure"""
        vouchers = parse_vouchers(SAMPLE_VOUCHER_XML)
        items = vouchers[0]["line_items"]
        assert items[0]["ledger_name"] == "Rahul Enterprises"
        assert items[0]["amount"] == "-50000"
        assert items[0]["is_debit"] is True
        assert items[1]["ledger_name"] == "Sales Account"
        assert items[1]["amount"] == "50000"
        assert items[1]["is_debit"] is False

    def test_devanagari_party_name_preserved(self):
        """Critical: Hindi/Marathi names must survive parsing"""
        vouchers = parse_vouchers(DEVANAGARI_VOUCHER_XML)
        assert len(vouchers) == 1
        assert vouchers[0]["party_ledger_name"] == "रमेश ट्रेडर्स"
        assert vouchers[0]["line_items"][0]["ledger_name"] == "रमेश ट्रेडर्स"

    def test_multiple_vouchers_parsed(self):
        """Parse multiple vouchers in one response"""
        vouchers = parse_vouchers(MULTIPLE_VOUCHERS_XML)
        assert len(vouchers) == 2
        assert vouchers[0]["guid"] == "V001"
        assert vouchers[0]["voucher_type"] == "Sales"
        assert vouchers[1]["guid"] == "V002"
        assert vouchers[1]["voucher_type"] == "Purchase"

    def test_voucher_without_guid_skipped(self):
        """Vouchers without GUID are skipped (malformed)"""
        vouchers = parse_vouchers(VOUCHER_NO_GUID_XML)
        assert len(vouchers) == 0

    def test_malformed_xml_returns_empty_list(self):
        """Bad XML returns empty list, not exception"""
        result = parse_vouchers("<broken xml")
        assert result == []

    def test_empty_xml_returns_empty_list(self):
        """Empty valid XML returns empty list"""
        xml = "<ENVELOPE></ENVELOPE>"
        result = parse_vouchers(xml)
        assert result == []

    def test_date_parsing(self):
        """Date format conversion YYYYMMDD -> YYYY-MM-DD"""
        assert _parse_tally_date("20260615") == "2026-06-15"
        assert _parse_tally_date("20251201") == "2025-12-01"
        assert _parse_tally_date("20260101") == "2026-01-01"

    def test_invalid_date_returns_none(self):
        """Invalid dates return None"""
        assert _parse_tally_date("") is None
        assert _parse_tally_date("invalid") is None
        assert _parse_tally_date("202601") is None
        assert _parse_tally_date("20260132") is None


class TestLedgerParser:
    """Test ledger XML parsing"""

    def test_parses_multiple_ledgers(self):
        """Parse ledger master data"""
        ledgers = parse_ledgers(SAMPLE_LEDGER_XML)
        assert len(ledgers) == 2
        assert ledgers[0]["guid"] == "LED-001"
        assert ledgers[0]["name"] == "Cash"
        assert ledgers[0]["ledger_type"] == "Asset"
        assert ledgers[1]["name"] == "Sales"
        assert ledgers[1]["ledger_type"] == "Income"

    def test_malformed_ledger_xml_returns_empty(self):
        """Malformed ledger XML returns empty list"""
        result = parse_ledgers("<broken>")
        assert result == []


class TestIntegerParsing:
    """Test integer parsing utility"""

    def test_parse_valid_integer(self):
        """Parse valid integer from element"""
        from xml.etree.ElementTree import fromstring
        elem = fromstring("<root><age>25</age></root>")
        assert _parse_int(elem, "age") == 25

    def test_parse_missing_integer_returns_default(self):
        """Missing element returns default"""
        from xml.etree.ElementTree import fromstring
        elem = fromstring("<root></root>")
        assert _parse_int(elem, "age") is None
        assert _parse_int(elem, "age", default=0) == 0

    def test_parse_invalid_integer_returns_default(self):
        """Non-integer value returns default"""
        from xml.etree.ElementTree import fromstring
        elem = fromstring("<root><age>abc</age></root>")
        assert _parse_int(elem, "age") is None
        assert _parse_int(elem, "age", default=-1) == -1
