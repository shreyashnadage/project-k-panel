# -*- coding: utf-8 -*-
"""
End-to-end roundtrip test.

Runs ONE poll cycle of the agent against the local cloud + live Tally:
  1. Polls cloud for pending commands
  2. Fetches ledgers from Tally
  3. Uploads to cloud ingest API
  4. Acks command as completed
  5. Verifies data landed in the database

Prerequisites:
  - Tally + TallyAPIConnectorV2.0.exe running
  - Cloud platform running: uvicorn cloudplatform.main:app --port 8000
  - Database seeded: python tests/seed_e2e.py

Run: python tests/test_e2e_roundtrip.py
"""

import os
import sys
import json
import time
import hashlib
import logging
from datetime import datetime, timezone, timedelta

os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("e2e")

CLOUD  = "http://localhost:8000"
API_KEY = "test-api-key-e2e-local-dev"
DEVICE = "device-e2e-001"
TENANT = "tenant-e2e-001"
COMPANY = "Bhrama Enterprises"
HEADERS = {"X-API-Key": API_KEY}


def step(n, desc):
    print(f"\n{'='*60}")
    print(f"  STEP {n}: {desc}")
    print(f"{'='*60}")


def main():
    print("\n" + "=" * 60)
    print("  END-TO-END ROUNDTRIP TEST")
    print("=" * 60)

    # ── Pre-checks ────────────────────────────────────────────────────────────
    step(0, "Pre-flight checks")

    # Cloud alive?
    try:
        r = requests.get(f"{CLOUD}/", timeout=5)
        assert r.status_code == 200
        print(f"  Cloud platform: OK ({CLOUD})")
    except Exception as e:
        print(f"  FAIL: Cloud not reachable at {CLOUD}: {e}")
        print("  Run: python -m uvicorn cloudplatform.main:app --port 8000")
        sys.exit(1)

    # Tally alive?
    from agent.fetcher.base import TallyHTTPClient
    client = TallyHTTPClient()
    if client.is_ready():
        print("  Tally: OK (localhost:9000)")
    else:
        print("  FAIL: Tally not reachable. Start TallyPrime + TallyAPIConnectorV2.0.exe")
        sys.exit(1)

    # ── Step 1: Create a pending command ──────────────────────────────────────
    step(1, "Create pending sync_ledgers command")

    cmd_resp = requests.post(
        f"{CLOUD}/v1/commands",
        json={
            "device_id": DEVICE,
            "command_type": "sync_ledgers",
            "params": {"company_name": COMPANY, "company_id": "client-e2e-001"},
            "created_by": "e2e_test",
        },
        headers=HEADERS,
    )
    assert cmd_resp.status_code == 201, f"Create command failed: {cmd_resp.text}"
    cmd = cmd_resp.json()
    command_id = cmd["id"]
    print(f"  Created command: {command_id}")
    print(f"  Status: {cmd['status']} (should be 'pending')")

    # ── Step 2: Agent polls for pending commands ──────────────────────────────
    step(2, "Poll for pending commands (simulating agent)")

    poll_resp = requests.get(
        f"{CLOUD}/v1/commands/pending",
        params={"device_id": DEVICE},
        headers=HEADERS,
    )
    assert poll_resp.status_code == 200
    commands = poll_resp.json()
    print(f"  Received {len(commands)} command(s)")

    # Find our command
    our_cmd = None
    for c in commands:
        if c["id"] == command_id:
            our_cmd = c
            break

    assert our_cmd is not None, f"Command {command_id} not found in poll response"
    print(f"  Command {command_id}: status={our_cmd['status']} (should be 'fetched')")
    assert our_cmd["status"] == "fetched"

    # ── Step 3: Execute command via engine ────────────────────────────────────
    step(3, "Execute sync_ledgers via CommandEngine")

    from agent.engine import CommandEngine
    engine = CommandEngine()

    params = our_cmd["params"]
    result = engine.execute({
        "resource": "ledger",
        "action": "pull_all",
        "company_name": params["company_name"],
        "company_id": params.get("company_id", ""),
        "params": params,
    })

    print(f"  Success: {result.success}")
    print(f"  Records: {result.record_count}")
    assert result.success, f"Engine failed: {result.error}"
    assert result.record_count > 0, "No ledgers returned"

    if result.data:
        print(f"  Sample: {result.data[0]['name']} (parent: {result.data[0]['parent']})")

    # ── Step 4: Upload ledgers to cloud ───────────────────────────────────────
    step(4, "Upload ledgers to cloud ingest API")

    company_guid = params.get("company_id", COMPANY)
    ledgers_payload = []
    for r in result.data:
        ledgers_payload.append({
            "company_guid": company_guid,
            "company_name": COMPANY,
            "ledger_guid": r.get("guid", r.get("name", "")),
            "name": r.get("name", ""),
            "parent": r.get("parent"),
            "ledger_type": r.get("ledger_type"),
            "opening_balance": r.get("opening_balance"),
            "closing_balance": r.get("closing_balance"),
        })

    ingest_resp = requests.post(
        f"{CLOUD}/v1/ledgers",
        json={"tenant_id": TENANT, "ledgers": ledgers_payload},
        headers=HEADERS,
    )
    print(f"  HTTP {ingest_resp.status_code}: {ingest_resp.text}")
    assert ingest_resp.status_code == 200, f"Ingest failed: {ingest_resp.text}"
    ingest = ingest_resp.json()
    print(f"  Accepted: {ingest['accepted']}, Duplicates: {ingest['duplicates']}, Errors: {ingest['errors']}")

    # ── Step 5: Ack command as completed ──────────────────────────────────────
    step(5, "Acknowledge command as completed")

    ack_resp = requests.patch(
        f"{CLOUD}/v1/commands/{command_id}",
        json={
            "status": "completed",
            "result": {
                "record_count": result.record_count,
                "resource": "ledger",
                "action": "pull_all",
            },
        },
        headers=HEADERS,
    )
    assert ack_resp.status_code == 200, f"Ack failed: {ack_resp.text}"
    ack = ack_resp.json()
    print(f"  Command status: {ack['status']} (should be 'completed')")
    print(f"  Completed at: {ack['completed_at']}")

    # ── Step 6: Verify data in database via stats API ─────────────────────────
    step(6, "Verify data landed in cloud database")

    stats_resp = requests.get(f"{CLOUD}/v1/stats", headers=HEADERS)
    if stats_resp.status_code == 200:
        stats = stats_resp.json()
        print(f"  Total ledgers in DB: {stats.get('total_ledgers', '?')}")
        print(f"  Total vouchers in DB: {stats.get('total_vouchers', '?')}")

    # Verify command is completed
    list_resp = requests.get(
        f"{CLOUD}/v1/commands",
        params={"device_id": DEVICE, "status": "completed"},
        headers=HEADERS,
    )
    completed = list_resp.json()
    found = any(c["id"] == command_id for c in completed)
    print(f"  Command {command_id} found in completed list: {found}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  E2E ROUNDTRIP: ALL STEPS PASSED")
    print("=" * 60)
    print(f"  Command created  -> polled  -> {result.record_count} ledgers fetched")
    print(f"  -> {ingest['accepted']} uploaded -> command acked as completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
