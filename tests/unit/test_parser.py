"""
Unit tests for Tally JSON Parser

Tests use pre-recorded/mocked Tally JSON responses.
"""

import pytest
from agent.extractor.parser import (
    parse_vouchers,
    parse_ledgers,
    _parse_tally_date,
    _parse_int,
)


SAMPLE_VOUCHER_JSON = {
    "data": [
        {
            "id": "VOUCH-001-GUID",
            "date": "20260601",
            "vouchertype": "Sales",
            "vouchernumber": "S/001",
            "party": "Rahul Enterprises",
            "narration": "Sale of goods",
            "amount": "50000"
        }
    ]
}


SAMPLE_LEDGER_JSON = {
    "data": [
        {
            "name": "Cash",
            "parent": "Cash-in-hand",
            "opening_balance": "100000",
            "closing_balance": "80000"
        },
        {
            "name": "Sales",
            "parent": "Direct Incomes",
            "opening_balance": "0",
            "closing_balance": "150000"
        }
    ]
}


class TestVoucherParser:
    """Test voucher JSON parsing"""

    def test_parses_single_voucher(self):
        """Basic voucher parsing"""
        vouchers = parse_vouchers(SAMPLE_VOUCHER_JSON)
        assert len(vouchers) == 1
        assert vouchers[0]["id"] == "VOUCH-001-GUID"
        assert vouchers[0]["voucher_type"] == "Sales"
        assert vouchers[0]["voucher_number"] == "S/001"
        assert vouchers[0]["party"] == "Rahul Enterprises"
        assert vouchers[0]["amount"] == "50000"
        assert vouchers[0]["date"] == "2026-06-01"

    def test_devanagari_party_name_preserved(self):
        """Devanagari party names are preserved"""
        devanagari_json = {
            "data": [
                {
                    "id": "DEVA-01",
                    "date": "20260601",
                    "vouchertype": "Sales",
                    "party": "रमेश ट्रेडर्स",
                    "amount": "1000"
                }
            ]
        }
        vouchers = parse_vouchers(devanagari_json)
        assert len(vouchers) == 1
        assert vouchers[0]["party"] == "रमेश ट्रेडर्स"

    def test_malformed_json_returns_empty_list(self):
        """Bad format JSON returns empty list, not exception"""
        assert parse_vouchers({"data": "not a list"}) == []
        assert parse_vouchers({}) == []

    def test_date_parsing(self):
        """Date format conversion YYYYMMDD -> YYYY-MM-DD"""
        assert _parse_tally_date("20260615") == "2026-06-15"
        assert _parse_tally_date("20251201") == "2025-12-01"

    def test_invalid_date_returns_none(self):
        """Invalid dates return None"""
        assert _parse_tally_date("") is None
        assert _parse_tally_date("invalid") is None
        assert _parse_tally_date("20260132") is None


class TestLedgerParser:
    """Test ledger JSON parsing"""

    def test_parses_multiple_ledgers(self):
        """Parse ledger master data"""
        ledgers = parse_ledgers(SAMPLE_LEDGER_JSON)
        assert len(ledgers) == 2
        assert ledgers[0]["name"] == "Cash"
        assert ledgers[0]["parent"] == "Cash-in-hand"
        assert ledgers[0]["opening_balance"] == "100000"
        assert ledgers[1]["name"] == "Sales"
        assert ledgers[1]["parent"] == "Direct Incomes"

    def test_malformed_ledger_json_returns_empty(self):
        """Malformed ledger JSON returns empty list"""
        assert parse_ledgers({}) == []


class TestIntegerParsing:
    """Test integer parsing utility"""

    def test_parse_valid_integer(self):
        """Parse valid integer from string"""
        assert _parse_int("25") == 25
        assert _parse_int("-10") == -10

    def test_parse_missing_integer_returns_default(self):
        """Missing value returns default"""
        assert _parse_int(None) is None
        assert _parse_int(None, default=0) == 0

    def test_parse_invalid_integer_returns_default(self):
        """Non-integer value returns default"""
        assert _parse_int("abc") is None
        assert _parse_int("abc", default=-1) == -1
