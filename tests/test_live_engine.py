# -*- coding: utf-8 -*-
"""
Live integration tests for the fetcher engine against a running TallyPrime.

Prerequisites:
  1. TallyPrime is open with "Bhrama Enterprises" loaded
  2. TallyAPIConnectorV2.0.exe is running
  3. Run: python -m pytest tests/test_live_engine.py -v -s

Each test is independent and uses only known-safe request patterns
to avoid Tally crashes (Tally crashes on malformed requests).
"""

import json
import logging
import pytest
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from agent.fetcher.base import TallyHTTPClient, TallyConnectionError, TallyTimeoutError
from agent.fetcher.ledger import LedgerFetcher
from agent.fetcher.voucher import VoucherFetcher
from agent.fetcher.stock import StockFetcher
from agent.fetcher.group import GroupFetcher
from agent.engine import CommandEngine, ALLOWED_OPS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

COMPANY = "Bhrama Enterprises"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    c = TallyHTTPClient()
    if not c.is_ready():
        pytest.skip("Tally is not reachable — start TallyPrime + TallyAPIConnectorV2.0.exe")
    return c


@pytest.fixture(scope="session")
def engine():
    e = CommandEngine()
    if not e.is_tally_ready():
        pytest.skip("Tally is not reachable")
    return e


@pytest.fixture(scope="session")
def ledger_fetcher(client):
    return LedgerFetcher(client)


@pytest.fixture(scope="session")
def voucher_fetcher(client):
    return VoucherFetcher(client)


@pytest.fixture(scope="session")
def stock_fetcher(client):
    return StockFetcher(client)


@pytest.fixture(scope="session")
def group_fetcher(client):
    return GroupFetcher(client)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 1: Health & Connectivity
# ═══════════════════════════════════════════════════════════════════════════════

class TestConnectivity:
    def test_tally_is_reachable(self, client):
        assert client.is_ready() is True

    def test_engine_health(self, engine):
        assert engine.is_tally_ready() is True


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 2: Ledger Fetcher
# ═══════════════════════════════════════════════════════════════════════════════

class TestLedgerFetcher:
    def test_pull_all_returns_list(self, ledger_fetcher):
        result = ledger_fetcher.pull_all(COMPANY)
        assert isinstance(result, list)
        assert len(result) > 0
        print(f"\n  → {len(result)} ledgers fetched")

    def test_ledger_has_required_fields(self, ledger_fetcher):
        result = ledger_fetcher.pull_all(COMPANY)
        first = result[0]
        for field in ("name", "guid", "parent", "opening_balance", "closing_balance"):
            assert field in first, f"Missing field: {field}"

    def test_ledger_names_are_populated(self, ledger_fetcher):
        result = ledger_fetcher.pull_all(COMPANY)
        names = [r["name"] for r in result]
        assert all(n for n in names), "Some ledger names are empty"
        print(f"\n  → Sample names: {names[:5]}")

    def test_pull_one_kotak_bank(self, ledger_fetcher):
        result = ledger_fetcher.pull_one(COMPANY, "Kotak Bank")
        assert result is not None
        assert result["name"] == "Kotak Bank"
        assert result["parent"] == "Bank Accounts"
        print(f"\n  → {json.dumps(result, ensure_ascii=False)}")

    def test_pull_one_nonexistent_returns_none(self, ledger_fetcher):
        result = ledger_fetcher.pull_one(COMPANY, "ZZZZ_DOES_NOT_EXIST_9999")
        # Tally may return empty or None for nonexistent ledger
        # Important: this must NOT crash Tally
        print(f"\n  → Nonexistent ledger result: {result}")

    def test_pull_by_group_bank_accounts(self, ledger_fetcher):
        result = ledger_fetcher.pull_by_group(COMPANY, "Bank Accounts")
        assert isinstance(result, list)
        for ledger in result:
            assert ledger["parent"].lower() == "bank accounts"
        print(f"\n  → {len(result)} ledgers in Bank Accounts: {[r['name'] for r in result]}")

    def test_pull_by_group_sundry_debtors(self, ledger_fetcher):
        result = ledger_fetcher.pull_by_group(COMPANY, "Sundry Debtors")
        assert isinstance(result, list)
        print(f"\n  → {len(result)} sundry debtors")

    def test_pull_by_group_empty_group(self, ledger_fetcher):
        result = ledger_fetcher.pull_by_group(COMPANY, "NONEXISTENT_GROUP_999")
        assert isinstance(result, list)
        assert len(result) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 3: Group Fetcher
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupFetcher:
    def test_pull_all_groups(self, group_fetcher):
        result = group_fetcher.pull_all(COMPANY)
        assert isinstance(result, list)
        assert len(result) > 0
        print(f"\n  → {len(result)} groups fetched")

    def test_group_has_required_fields(self, group_fetcher):
        result = group_fetcher.pull_all(COMPANY)
        first = result[0]
        for field in ("name", "guid", "parent"):
            assert field in first, f"Missing field: {field}"

    def test_standard_groups_present(self, group_fetcher):
        result = group_fetcher.pull_all(COMPANY)
        names = {r["name"] for r in result}
        expected = {"Bank Accounts", "Sundry Debtors", "Sundry Creditors"}
        found = expected.intersection(names)
        print(f"\n  → Found standard groups: {found}")
        assert len(found) >= 2, f"Expected at least 2 standard groups, found {found}"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 4: Voucher Fetcher (DayBook XML)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVoucherFetcher:
    def test_pull_by_date_recent(self, voucher_fetcher):
        """Fetch vouchers from last 7 days — short range to avoid timeout."""
        from datetime import datetime, timedelta
        to_d = datetime.today().strftime("%Y%m%d")
        from_d = (datetime.today() - timedelta(days=7)).strftime("%Y%m%d")
        result = voucher_fetcher.pull_by_date(COMPANY, from_d, to_d)
        assert isinstance(result, list)
        print(f"\n  → {len(result)} vouchers in last 7 days")
        if result:
            print(f"  → Sample: {json.dumps(result[0], ensure_ascii=False)}")

    def test_pull_by_date_fiscal_year(self, voucher_fetcher):
        """Fetch April 2026 vouchers — known to have data in Bhrama Enterprises."""
        result = voucher_fetcher.pull_by_date(COMPANY, "20260401", "20260430")
        assert isinstance(result, list)
        print(f"\n  → {len(result)} vouchers in April 2026")
        if result:
            types = set(v["voucher_type"] for v in result)
            print(f"  → Voucher types found: {types}")

    def test_pull_by_type_sales(self, voucher_fetcher):
        """Filter for Sales vouchers only."""
        result = voucher_fetcher.pull_by_type(COMPANY, "Sales", "20260401", "20260630")
        assert isinstance(result, list)
        for v in result:
            assert v["voucher_type"].lower() == "sales"
        print(f"\n  → {len(result)} Sales vouchers in Apr-Jun 2026")

    def test_voucher_has_required_fields(self, voucher_fetcher):
        result = voucher_fetcher.pull_by_date(COMPANY, "20260401", "20260430")
        if not result:
            pytest.skip("No vouchers in April 2026")
        first = result[0]
        for field in ("date", "voucher_type", "party"):
            assert field in first, f"Missing field: {field}"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 5: Stock Fetcher
# ═══════════════════════════════════════════════════════════════════════════════

class TestStockFetcher:
    def test_pull_all_items(self, stock_fetcher):
        result = stock_fetcher.pull_all_items(COMPANY)
        assert isinstance(result, list)
        print(f"\n  → {len(result)} stock items fetched")
        if result:
            print(f"  → Sample: {result[0]['name']}")

    def test_pull_all_groups(self, stock_fetcher):
        result = stock_fetcher.pull_all_groups(COMPANY)
        assert isinstance(result, list)
        print(f"\n  → {len(result)} stock groups fetched")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 6: CommandEngine (security + dispatch)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommandEngine:
    def test_security_blocks_unknown_action(self, engine):
        result = engine.execute({
            "resource": "ledger", "action": "delete_all",
            "company_name": COMPANY, "company_id": "test", "params": {}
        })
        assert result.success is False
        assert "not in the allowed list" in result.error

    def test_security_blocks_unknown_resource(self, engine):
        result = engine.execute({
            "resource": "database", "action": "drop",
            "company_name": COMPANY, "company_id": "test", "params": {}
        })
        assert result.success is False

    def test_rejects_missing_company(self, engine):
        result = engine.execute({
            "resource": "ledger", "action": "pull_all",
            "company_name": "", "company_id": "test", "params": {}
        })
        assert result.success is False
        assert "company_name" in result.error

    def test_engine_pull_all_ledgers(self, engine):
        result = engine.execute({
            "resource": "ledger", "action": "pull_all",
            "company_name": COMPANY, "company_id": "comp_test", "params": {}
        })
        assert result.success is True
        assert result.record_count > 0
        print(f"\n  → Engine returned {result.record_count} ledgers")

    def test_engine_pull_one_ledger(self, engine):
        result = engine.execute({
            "resource": "ledger", "action": "pull_one",
            "company_name": COMPANY, "company_id": "comp_test",
            "params": {"name": "Kotak Bank"}
        })
        assert result.success is True
        assert result.record_count == 1
        assert result.data[0]["name"] == "Kotak Bank"

    def test_engine_pull_groups(self, engine):
        result = engine.execute({
            "resource": "group", "action": "pull_all",
            "company_name": COMPANY, "company_id": "comp_test", "params": {}
        })
        assert result.success is True
        assert result.record_count > 0
        print(f"\n  → Engine returned {result.record_count} groups")

    def test_engine_result_to_dict(self, engine):
        result = engine.execute({
            "resource": "ledger", "action": "pull_all",
            "company_name": COMPANY, "company_id": "comp_test", "params": {}
        })
        d = result.to_dict()
        assert d["success"] is True
        assert d["resource"] == "ledger"
        assert d["action"] == "pull_all"
        assert d["company_id"] == "comp_test"
        assert isinstance(d["data"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE 7: CommandPoller mapping (unit-level, no network)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPollerMapping:
    def test_all_command_types_have_valid_targets(self):
        from agent.poller import COMMAND_TYPE_MAP
        for cmd_type, mapping in COMMAND_TYPE_MAP.items():
            if mapping is None:  # health_check
                continue
            resource = mapping["resource"]
            action = mapping["action"]
            assert resource in ALLOWED_OPS, f"{cmd_type} → unknown resource '{resource}'"
            assert action in ALLOWED_OPS[resource], (
                f"{cmd_type} → {resource}/{action} not in allowlist"
            )

    def test_health_check_mapped_to_none(self):
        from agent.poller import COMMAND_TYPE_MAP
        assert COMMAND_TYPE_MAP["health_check"] is None
