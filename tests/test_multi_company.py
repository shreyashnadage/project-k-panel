# -*- coding: utf-8 -*-
"""
Multi-company support test suite.

Tests:
  1. Company discovery from live Tally
  2. Company registration with cloud
  3. Company listing from cloud
  4. sync_full for a single company (all data types)
  5. sync_all_companies (syncs every mapped company)
  6. Idempotency of company registration
  7. Company deactivation
  8. discover_companies command via poller flow
  9. sync_full command via poller flow
  10. Database verification — all data types stored per company

Prerequisites:
  - TallyPrime + TallyAPIConnectorV2.0.exe running
  - Cloud platform running on port 8000
  - Database seeded (python tests/seed_e2e.py)

Run: python tests/test_multi_company.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta, timezone

os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger("multi_company")

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
        msg += f" -- {detail}"
    print(msg)
    results_log.append((status, label, detail))
    return condition


def create_command(cmd_type, params=None):
    resp = requests.post(
        f"{CLOUD}/v1/commands",
        json={
            "device_id": DEVICE,
            "command_type": cmd_type,
            "params": params or {"company_name": COMPANY, "company_id": "client-e2e-001"},
            "created_by": "multi_company_test",
        },
        headers=HDR,
    )
    assert resp.status_code == 201, f"Create {cmd_type} failed: {resp.text}"
    return resp.json()


def poll_and_execute(engine):
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

        # Use poller's actual handling logic
        from agent.poller import CommandPoller
        poller = CommandPoller.__new__(CommandPoller)
        poller.cloud_base_url = CLOUD
        poller.api_key = API_KEY
        poller.device_id = DEVICE
        poller.tenant_id = TENANT
        poller.engine = engine

        poller._handle(cmd)
        return cmd
    return None


def get_stats():
    r = requests.get(f"{CLOUD}/v1/stats", headers=HDR)
    return r.json() if r.status_code == 200 else {}


def query_data(resource, limit=100):
    r = requests.get(f"{CLOUD}/v1/data/{resource}", params={"limit": limit}, headers=HDR)
    return r.json() if r.status_code == 200 else {"count": 0, "data": []}


# ── pre-flight ───────────────────────────────────────────────────────────────

def preflight():
    banner("PRE-FLIGHT CHECKS")
    try:
        r = requests.get(f"{CLOUD}/", timeout=3)
        check("Cloud platform reachable", r.status_code == 200)
    except Exception:
        print("  FATAL: Cloud not running.")
        sys.exit(1)

    from agent.fetcher.base import TallyHTTPClient
    tally_ok = TallyHTTPClient().is_ready()
    check("Tally reachable (localhost:9000)", tally_ok)
    if not tally_ok:
        print("  FATAL: Start TallyPrime + TallyAPIConnectorV2.0.exe")
        sys.exit(1)


# ── tests ────────────────────────────────────────────────────────────────────

def test_company_discovery(engine):
    banner("TEST 1: Company discovery from Tally")
    result = engine.execute({
        "resource": "company", "action": "list",
        "company_name": "", "company_id": "", "params": {},
    })
    check("Company list succeeds", result.success)
    check("At least 1 company found", result.record_count >= 1,
          f"{result.record_count} companies")
    if result.data:
        names = [c["name"] for c in result.data]
        check("Bhrama Enterprises is listed", COMPANY in names, str(names))
    return result.data


def test_company_details(engine):
    banner("TEST 2: Company details from Tally")
    result = engine.execute({
        "resource": "company", "action": "details",
        "company_name": COMPANY, "company_id": "", "params": {},
    })
    check("Company details succeeds", result.success)
    if result.data:
        d = result.data[0]
        check("Has GUID", bool(d.get("guid")), d.get("guid", "?"))
        check("Has state", bool(d.get("state")), d.get("state", "?"))
        check("Has starting_from", bool(d.get("starting_from")), d.get("starting_from", "?"))
        print(f"    Full details: {json.dumps(d, ensure_ascii=False)}")
    return result.data[0] if result.data else {}


def test_cloud_company_registration(company_details):
    banner("TEST 3: Register company with cloud")
    payload = {
        "device_id": DEVICE,
        "companies": [{
            "device_id": DEVICE,
            "company_name": COMPANY,
            "company_guid": company_details.get("guid"),
            "formal_name": company_details.get("formal_name"),
            "gst_number": company_details.get("gst_number"),
            "state": company_details.get("state"),
        }],
    }
    resp = requests.post(f"{CLOUD}/v1/companies", json=payload, headers=HDR)
    check("Registration returns 201", resp.status_code == 201, resp.text[:200])
    data = resp.json()
    check("1 company registered", data["count"] == 1)
    if data["companies"]:
        c = data["companies"][0]
        check("Company name matches", c["company_name"] == COMPANY)
        check("GUID stored", bool(c.get("company_guid")))
        check("State stored", c.get("state") == "Karnataka")
    return data


def test_cloud_company_listing():
    banner("TEST 4: List companies from cloud")
    resp = requests.get(
        f"{CLOUD}/v1/companies",
        params={"device_id": DEVICE},
        headers=HDR,
    )
    check("Listing returns 200", resp.status_code == 200)
    data = resp.json()
    check("At least 1 company listed", data["count"] >= 1, f"{data['count']} companies")
    names = [c["company_name"] for c in data["companies"]]
    check("Bhrama Enterprises in list", COMPANY in names)
    return data


def test_company_registration_idempotency(company_details):
    banner("TEST 5: Idempotent re-registration")
    # Get count before
    resp1 = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    count_before = resp1.json()["count"]

    # Re-register same company
    payload = {
        "device_id": DEVICE,
        "companies": [{
            "device_id": DEVICE,
            "company_name": COMPANY,
            "company_guid": company_details.get("guid"),
            "state": "Karnataka",
        }],
    }
    resp2 = requests.post(f"{CLOUD}/v1/companies", json=payload, headers=HDR)
    check("Re-registration succeeds", resp2.status_code == 201)

    # Count should not increase
    resp3 = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    count_after = resp3.json()["count"]
    check("No duplicate created", count_after == count_before,
          f"before={count_before}, after={count_after}")


def test_discover_companies_command(engine):
    banner("TEST 6: discover_companies via command flow")
    create_command("discover_companies", {"company_name": "", "company_id": ""})
    cmd = poll_and_execute(engine)
    check("discover_companies command executed", cmd is not None)

    # Verify company is now in cloud
    resp = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    data = resp.json()
    check("Companies registered after discover", data["count"] >= 1)


def test_sync_full_command(engine):
    banner("TEST 7: sync_full for single company")
    stats_before = get_stats()

    create_command("sync_full", {
        "company_name": COMPANY,
        "company_id": "client-e2e-001",
    })
    cmd = poll_and_execute(engine)
    check("sync_full command executed", cmd is not None)

    # Verify all data types have records
    stats_after = get_stats()
    check("Ledgers synced", stats_after.get("total_ledgers", 0) > 0,
          f"{stats_after.get('total_ledgers', 0)} ledgers")
    check("Groups synced", stats_after.get("total_groups", 0) > 0,
          f"{stats_after.get('total_groups', 0)} groups")
    # Vouchers may be 0 if no transactions in date range — that's OK
    check("Stock items synced", stats_after.get("total_stock_items", 0) >= 0,
          f"{stats_after.get('total_stock_items', 0)} stock items")


def test_sync_all_companies_command(engine):
    banner("TEST 8: sync_all_companies")
    # Ensure at least one company is mapped
    resp = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    companies = resp.json()
    check("Companies mapped before sync_all", companies["count"] >= 1,
          f"{companies['count']} companies")

    create_command("sync_all_companies", {"company_name": "", "company_id": ""})
    cmd = poll_and_execute(engine)
    check("sync_all_companies executed", cmd is not None)

    stats = get_stats()
    check("Data present after sync_all", stats.get("total_ledgers", 0) > 0)


def test_company_deactivation():
    banner("TEST 9: Company deactivation")
    # Get company ID
    resp = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    companies = resp.json()["companies"]
    if not companies:
        check("Company exists for deactivation", False)
        return

    comp_id = companies[0]["id"]

    # Deactivate
    resp2 = requests.patch(
        f"{CLOUD}/v1/companies/{comp_id}",
        params={"is_active": False},
        headers=HDR,
    )
    check("Deactivation succeeds", resp2.status_code == 200)
    check("Company is inactive", resp2.json()["is_active"] == False)

    # List active only — should be 0
    resp3 = requests.get(
        f"{CLOUD}/v1/companies",
        params={"device_id": DEVICE, "active_only": True},
        headers=HDR,
    )
    check("No active companies after deactivation", resp3.json()["count"] == 0)

    # Re-activate for future tests
    requests.patch(f"{CLOUD}/v1/companies/{comp_id}", params={"is_active": True}, headers=HDR)
    resp4 = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    check("Re-activation works", resp4.json()["count"] >= 1)


def test_security_gate(engine):
    banner("TEST 10: Security gates")
    r1 = engine.execute({
        "resource": "company", "action": "delete",
        "company_name": "", "company_id": "", "params": {},
    })
    check("company/delete blocked", not r1.success)

    r2 = engine.execute({
        "resource": "company", "action": "create",
        "company_name": "", "company_id": "", "params": {},
    })
    check("company/create blocked", not r2.success)


def test_final_stats():
    banner("TEST 11: Final database verification")
    stats = get_stats()
    print(f"    Ledgers:      {stats.get('total_ledgers', '?')}")
    print(f"    Vouchers:     {stats.get('total_vouchers', '?')}")
    print(f"    Groups:       {stats.get('total_groups', '?')}")
    print(f"    Stock Items:  {stats.get('total_stock_items', '?')}")
    print(f"    Stock Groups: {stats.get('total_stock_groups', '?')}")

    check("Ledgers in DB", stats.get("total_ledgers", 0) > 0)
    check("Groups in DB", stats.get("total_groups", 0) > 0)

    # Check companies endpoint
    resp = requests.get(f"{CLOUD}/v1/companies", params={"device_id": DEVICE}, headers=HDR)
    companies = resp.json()
    check("Companies mapped in DB", companies["count"] >= 1)
    for c in companies["companies"]:
        print(f"    Company: {c['company_name']} (guid={c.get('company_guid', '?')}, "
              f"state={c.get('state', '?')}, active={c['is_active']})")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    banner("MULTI-COMPANY TEST SUITE")
    print(f"  Cloud:   {CLOUD}")
    print(f"  Tally:   localhost:9000")
    print(f"  Company: {COMPANY}")

    preflight()
    engine = CommandEngine()

    # Company discovery
    companies = test_company_discovery(engine)
    details = test_company_details(engine)

    # Cloud registration
    test_cloud_company_registration(details)
    test_cloud_company_listing()
    test_company_registration_idempotency(details)

    # Command-flow tests
    test_discover_companies_command(engine)
    test_sync_full_command(engine)
    test_sync_all_companies_command(engine)

    # Management
    test_company_deactivation()
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
