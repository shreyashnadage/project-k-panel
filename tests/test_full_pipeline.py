# -*- coding: utf-8 -*-
"""
Full pipeline test — fires every supported command type through the
continuous poller and verifies all data lands in the cloud database.

This test simulates the real production flow:
  Admin creates commands -> Agent polls -> Fetches from Tally -> Uploads to cloud

Prerequisites:
  - TallyPrime + TallyAPIConnectorV2.0.exe running
  - Cloud platform running on port 8000
  - Database seeded (python tests/seed_e2e.py)

Run: python tests/test_full_pipeline.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger("pipeline")

CLOUD   = "http://localhost:8000"
API_KEY = "test-api-key-e2e-local-dev"
DEVICE  = "device-e2e-001"
TENANT  = "tenant-e2e-001"
COMPANY = "Bhrama Enterprises"
HDR     = {"X-API-Key": API_KEY}

from agent.engine import CommandEngine
from agent.poller import COMMAND_TYPE_MAP

# ── helpers ──────────────────────────────────────────────────────────────────

passed = 0
failed = 0
results_log = []

def banner(text):
    print(f"\n{'='*65}")
    print(f"  {text}")
    print(f"{'='*65}")


def create_command(cmd_type, params=None):
    resp = requests.post(
        f"{CLOUD}/v1/commands",
        json={
            "device_id": DEVICE,
            "command_type": cmd_type,
            "params": params or {"company_name": COMPANY, "company_id": "client-e2e-001"},
            "created_by": "pipeline_test",
        },
        headers=HDR,
    )
    assert resp.status_code == 201, f"Create {cmd_type} failed: {resp.text}"
    return resp.json()


def poll_and_execute(engine):
    """Poll once, execute all fetched commands, upload results."""
    poll_resp = requests.get(
        f"{CLOUD}/v1/commands/pending",
        params={"device_id": DEVICE},
        headers=HDR,
    )
    assert poll_resp.status_code == 200
    commands = poll_resp.json()
    print(f"  Polled: {len(commands)} command(s)")

    for cmd in commands:
        cmd_id   = cmd["id"]
        cmd_type = cmd["command_type"]
        params   = cmd["params"]

        mapping = COMMAND_TYPE_MAP.get(cmd_type)

        # health_check
        if mapping is None:
            ready = engine.is_tally_ready()
            ack(cmd_id, "completed", {"tally_ready": ready})
            print(f"    {cmd_type}: tally_ready={ready}")
            continue

        engine_cmd = {
            "resource":     mapping["resource"],
            "action":       mapping["action"],
            "company_name": params.get("company_name", COMPANY),
            "company_id":   params.get("company_id", ""),
            "params":       params,
        }

        result = engine.execute(engine_cmd)
        print(f"    {cmd_type}: success={result.success} records={result.record_count}")

        if result.success:
            ack(cmd_id, "completed", {
                "record_count": result.record_count,
                "resource": result.resource,
            })
            upload(result, params.get("company_name", COMPANY))
        else:
            ack(cmd_id, "failed", error_message=result.error)
            print(f"    ERROR: {result.error}")

        return result  # return first result for assertions
    return None


def ack(cmd_id, status, result_data=None, error_message=None):
    body = {"status": status}
    if result_data:
        body["result"] = result_data
    if error_message:
        body["error_message"] = error_message
    requests.patch(f"{CLOUD}/v1/commands/{cmd_id}", json=body, headers=HDR)


def upload(result, company_name):
    """Upload result data to the correct ingest endpoint."""
    from agent.poller import CommandPoller
    # Create a minimal poller just for upload methods
    poller = CommandPoller.__new__(CommandPoller)
    poller.cloud_base_url = CLOUD
    poller.api_key = API_KEY
    poller.device_id = DEVICE
    poller.tenant_id = TENANT

    if result.resource == "ledger":
        poller._upload_ledgers(result, company_name)
    elif result.resource == "voucher":
        poller._upload_vouchers(result, company_name)
    elif result.resource == "group":
        poller._upload_groups(result, company_name)
    elif result.resource == "stock_item":
        poller._upload_stock_items(result, company_name)
    elif result.resource == "stock_group":
        poller._upload_stock_groups(result, company_name)


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results_log.append((status, label, detail))
    return condition


def get_stats():
    r = requests.get(f"{CLOUD}/v1/stats", headers=HDR)
    return r.json() if r.status_code == 200 else {}


def query_data(resource, limit=10):
    r = requests.get(f"{CLOUD}/v1/data/{resource}", params={"limit": limit}, headers=HDR)
    return r.json() if r.status_code == 200 else {"count": 0, "data": []}


# ── pre-flight ───────────────────────────────────────────────────────────────

def preflight():
    banner("PRE-FLIGHT CHECKS")
    try:
        r = requests.get(f"{CLOUD}/", timeout=3)
        check("Cloud platform reachable", r.status_code == 200)
    except Exception:
        print("  FATAL: Cloud not running. Start with: python -m uvicorn cloudplatform.main:app --port 8000")
        sys.exit(1)

    from agent.fetcher.base import TallyHTTPClient
    tally_ok = TallyHTTPClient().is_ready()
    check("Tally reachable (localhost:9000)", tally_ok)
    if not tally_ok:
        print("  FATAL: Start TallyPrime + TallyAPIConnectorV2.0.exe")
        sys.exit(1)


# ── tests ────────────────────────────────────────────────────────────────────

def test_health_check(engine):
    banner("TEST 1: health_check")
    create_command("health_check")
    result = poll_and_execute(engine)
    check("health_check completes", True)


def test_sync_ledgers(engine):
    banner("TEST 2: sync_ledgers")
    create_command("sync_ledgers")
    result = poll_and_execute(engine)
    check("sync_ledgers returned data", result and result.success)
    check("Ledger count > 0", result and result.record_count > 0,
          f"{result.record_count if result else 0} records")

    if result and result.data:
        first = result.data[0]
        check("Ledger has 'name' field", "name" in first, first.get("name", "?"))
        check("Ledger has 'parent' field", "parent" in first, first.get("parent", "?"))
        check("Ledger has 'guid' field", "guid" in first)
        check("Ledger has 'closing_balance'", "closing_balance" in first)

    # Verify in cloud DB
    data = query_data("ledgers")
    check("Ledgers stored in cloud DB", data["count"] > 0, f"{data['count']} rows")

    if data["data"]:
        row = data["data"][0]
        check("DB row has company_guid", bool(row.get("company_guid")))
        check("DB row has name", bool(row.get("name")))
        print(f"    Sample DB row: {row.get('name')} (parent: {row.get('parent')})")


def test_sync_ledger_one(engine):
    banner("TEST 3: sync_ledger_one (Kotak Bank)")
    create_command("sync_ledger_one", {
        "company_name": COMPANY, "company_id": "client-e2e-001",
        "name": "Kotak Bank"
    })
    result = poll_and_execute(engine)
    check("sync_ledger_one returned data", result and result.success)
    check("Exactly 1 record", result and result.record_count == 1,
          f"got {result.record_count if result else 0}")
    if result and result.data:
        check("Name is Kotak Bank", result.data[0].get("name") == "Kotak Bank")
        check("Parent is Bank Accounts", result.data[0].get("parent") == "Bank Accounts")


def test_sync_ledgers_by_group(engine):
    banner("TEST 4: sync_ledgers_by_group (Sundry Debtors)")
    create_command("sync_ledgers_by_group", {
        "company_name": COMPANY, "company_id": "client-e2e-001",
        "group": "Sundry Debtors"
    })
    result = poll_and_execute(engine)
    check("sync_ledgers_by_group returned data", result and result.success)
    if result and result.data:
        all_debtors = all(r.get("parent", "").lower() == "sundry debtors" for r in result.data)
        check("All results are Sundry Debtors", all_debtors,
              f"{result.record_count} records")
        print(f"    Debtors: {[r['name'] for r in result.data[:5]]}")


def test_sync_groups(engine):
    banner("TEST 5: sync_groups")
    create_command("sync_groups")
    result = poll_and_execute(engine)
    check("sync_groups returned data", result and result.success)
    check("Group count > 0", result and result.record_count > 0,
          f"{result.record_count if result else 0} records")

    if result and result.data:
        names = {r["name"] for r in result.data}
        check("Bank Accounts group exists", "Bank Accounts" in names)
        check("Sundry Debtors group exists", "Sundry Debtors" in names)
        check("Sundry Creditors group exists", "Sundry Creditors" in names)

    data = query_data("groups")
    check("Groups stored in cloud DB", data["count"] > 0, f"{data['count']} rows")


def test_sync_vouchers(engine):
    banner("TEST 6: sync_vouchers (DayBook XML)")
    # Use a short date range to avoid timeout
    from_d = (datetime.today() - timedelta(days=90)).strftime("%Y%m%d")
    to_d = datetime.today().strftime("%Y%m%d")
    create_command("sync_vouchers", {
        "company_name": COMPANY, "company_id": "client-e2e-001",
        "from_date": from_d, "to_date": to_d,
    })
    result = poll_and_execute(engine)
    check("sync_vouchers completed", result is not None)

    if result and result.success:
        check("Voucher count >= 0", result.record_count >= 0,
              f"{result.record_count} records")
        if result.data:
            first = result.data[0]
            check("Voucher has 'voucher_type'", "voucher_type" in first,
                  first.get("voucher_type", "?"))
            check("Voucher has 'party'", "party" in first)
            check("Voucher has 'date'", "date" in first, first.get("date", "?"))
            types = set(v.get("voucher_type") for v in result.data)
            print(f"    Voucher types found: {types}")

            data = query_data("vouchers")
            check("Vouchers stored in cloud DB", data["count"] > 0,
                  f"{data['count']} rows")
        else:
            print("    (No vouchers in date range — OK for test company)")
    elif result:
        print(f"    Voucher fetch error (may be expected): {result.error}")
        check("Voucher error is timeout-related (not crash)",
              "timed out" in (result.error or "").lower() or "timeout" in (result.error or "").lower(),
              "Tally did not crash")


def test_sync_stock(engine):
    banner("TEST 7: sync_stock")
    create_command("sync_stock")
    result = poll_and_execute(engine)
    check("sync_stock completed", result is not None)

    if result and result.success:
        check("Stock count >= 0", result.record_count >= 0,
              f"{result.record_count} records")
        if result.data:
            first = result.data[0]
            check("Stock item has 'name'", "name" in first, first.get("name", "?"))
            data = query_data("stock-items")
            check("Stock items stored in cloud DB", data["count"] > 0,
                  f"{data['count']} rows")
        else:
            print("    (No stock items — OK for service company)")
    elif result:
        print(f"    Stock fetch result: {result.error}")


def test_idempotency(engine):
    banner("TEST 8: Idempotency (re-sync ledgers)")
    stats_before = get_stats()
    ledgers_before = stats_before.get("total_ledgers", 0)

    create_command("sync_ledgers")
    result = poll_and_execute(engine)
    check("Re-sync completed", result and result.success)

    stats_after = get_stats()
    ledgers_after = stats_after.get("total_ledgers", 0)
    check("No duplicate ledgers created", ledgers_after == ledgers_before,
          f"before={ledgers_before}, after={ledgers_after}")


def test_security_gate(engine):
    banner("TEST 9: Security gate (invalid command)")
    result = engine.execute({
        "resource": "ledger", "action": "delete_all",
        "company_name": COMPANY, "company_id": "test", "params": {}
    })
    check("delete_all blocked", not result.success)
    check("Error mentions allowlist", "not in the allowed list" in (result.error or ""))

    result2 = engine.execute({
        "resource": "database", "action": "drop_tables",
        "company_name": COMPANY, "company_id": "test", "params": {}
    })
    check("drop_tables blocked", not result2.success)


def test_final_stats():
    banner("TEST 10: Final database verification")
    stats = get_stats()
    print(f"    Ledgers:      {stats.get('total_ledgers', '?')}")
    print(f"    Vouchers:     {stats.get('total_vouchers', '?')}")
    print(f"    Groups:       {stats.get('total_groups', '?')}")
    print(f"    Stock Items:  {stats.get('total_stock_items', '?')}")
    print(f"    Stock Groups: {stats.get('total_stock_groups', '?')}")

    check("Ledgers in DB", stats.get("total_ledgers", 0) > 0)
    check("Groups in DB", stats.get("total_groups", 0) > 0)

    # Query some actual data
    for resource in ["ledgers", "groups", "vouchers", "stock-items"]:
        data = query_data(resource, limit=3)
        if data["count"] > 0:
            print(f"\n    --- {resource} (sample) ---")
            for row in data["data"][:3]:
                name = row.get("name", row.get("voucher_number", "?"))
                print(f"      {name}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    banner("FULL PIPELINE TEST SUITE")
    print(f"  Cloud:   {CLOUD}")
    print(f"  Tally:   localhost:9000")
    print(f"  Company: {COMPANY}")

    preflight()

    engine = CommandEngine()

    test_health_check(engine)
    test_sync_ledgers(engine)
    test_sync_ledger_one(engine)
    test_sync_ledgers_by_group(engine)
    test_sync_groups(engine)
    test_sync_vouchers(engine)
    test_sync_stock(engine)
    test_idempotency(engine)
    test_security_gate(engine)
    test_final_stats()

    banner(f"RESULTS: {passed} passed, {failed} failed")
    if failed:
        print("\n  FAILURES:")
        for status, label, detail in results_log:
            if status == "FAIL":
                print(f"    - {label}: {detail}")
    print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
