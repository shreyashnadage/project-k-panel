# -*- coding: utf-8 -*-
"""
Offline queue + retry test suite.

Tests:
  1. QueueManager basic ops (enqueue, get_pending, mark_sent, mark_failed)
  2. Queue stats and cleanup
  3. Max retries -> permanent failure
  4. Poller queues on cloud down (simulated)
  5. Poller flushes queue when cloud comes back
  6. Queue survives restart (persistence)
  7. Full e2e: fetch from Tally -> cloud down -> queued -> cloud up -> flushed -> DB verified
  8. Idempotency: flushed duplicates are handled gracefully
  9. Queue + sync_full integration

Prerequisites:
  - TallyPrime + TallyAPIConnectorV2.0.exe running
  - Cloud platform running on port 8000
  - Database seeded (python tests/seed_e2e.py)

Run: python tests/test_offline_queue.py
"""

import os
import sys
import json
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger("offline_queue")

CLOUD   = "http://localhost:8000"
API_KEY = "test-api-key-e2e-local-dev"
DEVICE  = "device-e2e-001"
TENANT  = "tenant-e2e-001"
COMPANY = "Bhrama Enterprises"
HDR     = {"X-API-Key": API_KEY}

from agent.queue.manager import QueueManager, MAX_RETRIES
from agent.engine import CommandEngine
from agent.poller import CommandPoller

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


def fresh_queue():
    """Create a queue with a temp DB file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="queue_test_")
    os.close(fd)
    return QueueManager(db_path=path), path


def make_poller(engine, cloud_url=CLOUD, queue_db=None):
    """Create a poller with optional queue DB path."""
    if queue_db is None:
        fd, queue_db = tempfile.mkstemp(suffix=".db", prefix="poller_queue_")
        os.close(fd)
    return CommandPoller(
        cloud_base_url=cloud_url,
        device_id=DEVICE,
        api_key=API_KEY,
        tenant_id=TENANT,
        engine=engine,
        poll_interval=5,
        queue_db_path=queue_db,
    ), queue_db


def get_stats():
    r = requests.get(f"{CLOUD}/v1/stats", headers=HDR)
    return r.json() if r.status_code == 200 else {}


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

def test_queue_basic_ops():
    banner("TEST 1: QueueManager basic operations")
    q, path = fresh_queue()

    # Enqueue
    id1 = q.enqueue("/v1/ledgers", {"tenant_id": "t1", "ledgers": [{"name": "A"}]}, "ledger", 1)
    id2 = q.enqueue("/v1/vouchers", {"tenant_id": "t1", "vouchers": [{"date": "2026-01-01"}]}, "voucher", 1)
    check("Enqueue returns row IDs", id1 >= 1 and id2 >= 1, f"id1={id1}, id2={id2}")

    # Get pending
    pending = q.get_pending()
    check("2 pending items", len(pending) == 2)
    check("First item is ledger", pending[0]["label"] == "ledger")
    check("Payload preserved", pending[0]["payload"]["tenant_id"] == "t1")

    # Mark sent
    q.mark_sent(id1)
    pending = q.get_pending()
    check("1 pending after mark_sent", len(pending) == 1)

    # Mark failed
    q.mark_failed(id2, "connection refused")
    pending = q.get_pending()
    check("Still pending after 1 failure", len(pending) == 1, "retry_count < MAX_RETRIES")

    # Stats
    stats = q.get_stats()
    check("Stats correct", stats["sent"] == 1 and stats["pending"] == 1 and stats["failed"] == 0,
          f"sent={stats['sent']}, pending={stats['pending']}, failed={stats['failed']}")

    os.unlink(path)


def test_queue_max_retries():
    banner("TEST 2: Max retries -> permanent failure")
    q, path = fresh_queue()

    qid = q.enqueue("/v1/test", {"data": "x"}, "test", 1)
    for i in range(MAX_RETRIES):
        q.mark_failed(qid, f"attempt {i+1}")

    stats = q.get_stats()
    check(f"Failed after {MAX_RETRIES} retries", stats["failed"] == 1)
    check("Not in pending anymore", stats["pending"] == 0)

    os.unlink(path)


def test_queue_cleanup():
    banner("TEST 3: Queue cleanup")
    q, path = fresh_queue()

    id1 = q.enqueue("/v1/a", {}, "a", 1)
    id2 = q.enqueue("/v1/b", {}, "b", 1)
    q.mark_sent(id1)

    cleared = q.clear_sent()
    check("clear_sent removes sent items", cleared == 1)

    pending = q.get_pending()
    check("Pending items remain after clear_sent", len(pending) == 1)

    q.clear_all()
    check("clear_all empties queue", q.pending_count() == 0)

    os.unlink(path)


def test_poller_queues_on_cloud_down(engine):
    banner("TEST 4: Poller queues when cloud is unreachable")
    # Point poller at a port that isn't listening
    poller, qpath = make_poller(engine, cloud_url="http://localhost:19999")

    # Fetch data from Tally
    result = engine.execute({
        "resource": "ledger", "action": "pull_all",
        "company_name": COMPANY, "company_id": "test", "params": {},
    })
    check("Tally fetch succeeds", result.success, f"{result.record_count} ledgers")

    # Try to upload — should fail and queue
    poller._upload_data(result, COMPANY)

    stats = poller.queue.get_stats()
    check("Data queued on cloud failure", stats["pending"] >= 1,
          f"pending={stats['pending']}")

    pending = poller.queue.get_pending()
    check("Queued payload has correct endpoint", pending[0]["endpoint"] == "/v1/ledgers")
    check("Queued payload has records", pending[0]["record_count"] > 0,
          f"{pending[0]['record_count']} records")

    os.unlink(qpath)
    return True


def test_poller_flushes_queue(engine):
    banner("TEST 5: Poller flushes queue when cloud is back")
    # Create poller pointing at dead server, queue some data
    fd, qpath = tempfile.mkstemp(suffix=".db", prefix="flush_test_")
    os.close(fd)

    dead_poller, _ = make_poller(engine, cloud_url="http://localhost:19999", queue_db=qpath)
    result = engine.execute({
        "resource": "group", "action": "pull_all",
        "company_name": COMPANY, "company_id": "test", "params": {},
    })
    dead_poller._upload_data(result, COMPANY)

    queued_before = dead_poller.queue.pending_count()
    check("Data queued", queued_before >= 1, f"{queued_before} item(s)")

    # Now create a poller pointing at the REAL cloud, same queue DB
    live_poller, _ = make_poller(engine, cloud_url=CLOUD, queue_db=qpath)
    live_poller._flush_queue()

    queued_after = live_poller.queue.pending_count()
    sent = live_poller.queue.get_stats()["sent"]
    check("Queue flushed successfully", queued_after == 0 and sent >= 1,
          f"pending={queued_after}, sent={sent}")

    os.unlink(qpath)


def test_queue_persistence():
    banner("TEST 6: Queue survives restart (persistence)")
    fd, qpath = tempfile.mkstemp(suffix=".db", prefix="persist_test_")
    os.close(fd)

    # Create queue, add items, close
    q1 = QueueManager(db_path=qpath)
    q1.enqueue("/v1/ledgers", {"test": True}, "persistence_test", 5)
    del q1

    # Re-open same DB
    q2 = QueueManager(db_path=qpath)
    pending = q2.get_pending()
    check("Data persists across restart", len(pending) == 1)
    check("Payload intact", pending[0]["payload"]["test"] == True)
    check("Label intact", pending[0]["label"] == "persistence_test")

    os.unlink(qpath)


def test_e2e_queue_flush(engine):
    banner("TEST 7: E2E — Tally fetch -> queue -> flush -> DB verified")
    fd, qpath = tempfile.mkstemp(suffix=".db", prefix="e2e_queue_")
    os.close(fd)

    stats_before = get_stats()
    ledgers_before = stats_before.get("total_ledgers", 0)

    # Step 1: Fetch from Tally
    result = engine.execute({
        "resource": "stock_item", "action": "pull_all",
        "company_name": COMPANY, "company_id": "test-queue", "params": {},
    })
    check("Tally fetch OK", result.success, f"{result.record_count} stock items")

    # Step 2: Upload to dead server -> queued
    dead_poller, _ = make_poller(engine, cloud_url="http://localhost:19999", queue_db=qpath)
    dead_poller._upload_data(result, COMPANY)
    check("Items queued", dead_poller.queue.pending_count() >= 1)

    # Step 3: Flush to real cloud
    live_poller, _ = make_poller(engine, cloud_url=CLOUD, queue_db=qpath)
    live_poller._flush_queue()
    check("Queue empty after flush", live_poller.queue.pending_count() == 0)

    # Step 4: Verify in cloud DB
    stats_after = get_stats()
    check("Stock items in DB after flush",
          stats_after.get("total_stock_items", 0) >= result.record_count,
          f"{stats_after.get('total_stock_items', 0)} stock items")

    os.unlink(qpath)


def test_flush_idempotency(engine):
    banner("TEST 8: Flushed duplicates handled gracefully")
    fd, qpath = tempfile.mkstemp(suffix=".db", prefix="idem_queue_")
    os.close(fd)

    result = engine.execute({
        "resource": "ledger", "action": "pull_all",
        "company_name": COMPANY, "company_id": "test-idem", "params": {},
    })

    # Queue the same data twice
    q = QueueManager(db_path=qpath)
    payload = {"tenant_id": TENANT, "ledgers": [
        {
            "company_guid": "test-idem", "company_name": COMPANY,
            "ledger_guid": r.get("guid", r.get("name", "")),
            "name": r.get("name", ""), "parent": r.get("parent"),
            "ledger_type": r.get("ledger_type"),
            "opening_balance": r.get("opening_balance"),
            "closing_balance": r.get("closing_balance"),
        } for r in result.data
    ]}
    q.enqueue("/v1/ledgers", payload, "ledger", len(result.data))
    q.enqueue("/v1/ledgers", payload, "ledger_dup", len(result.data))

    # Flush both
    live_poller, _ = make_poller(engine, cloud_url=CLOUD, queue_db=qpath)
    live_poller._flush_queue()

    stats = q.get_stats()
    check("Both items sent (not failed)", stats["sent"] == 2 and stats["failed"] == 0,
          f"sent={stats['sent']}, failed={stats['failed']}")
    check("Queue fully drained", stats["pending"] == 0)

    os.unlink(qpath)


def test_sync_full_with_queue(engine):
    banner("TEST 9: sync_full queues correctly when cloud is down")
    fd, qpath = tempfile.mkstemp(suffix=".db", prefix="syncfull_queue_")
    os.close(fd)

    # Create poller pointing at dead server
    dead_poller, _ = make_poller(engine, cloud_url="http://localhost:19999", queue_db=qpath)
    dead_poller._handle_sync_full("fake-cmd-id", {
        "company_name": COMPANY, "company_id": "test-syncfull",
    })

    queued = dead_poller.queue.pending_count()
    check("sync_full queued uploads on failure", queued >= 3,
          f"{queued} items queued (ledgers, groups, vouchers, stock...)")

    # Flush to real cloud
    live_poller, _ = make_poller(engine, cloud_url=CLOUD, queue_db=qpath)
    live_poller._flush_queue()
    check("All queued items flushed", live_poller.queue.pending_count() == 0)

    stats = live_poller.queue.get_stats()
    check("All items sent successfully", stats["failed"] == 0,
          f"sent={stats['sent']}, failed={stats['failed']}")

    os.unlink(qpath)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    banner("OFFLINE QUEUE + RETRY TEST SUITE")

    preflight()
    engine = CommandEngine()

    # Unit tests (no Tally needed)
    test_queue_basic_ops()
    test_queue_max_retries()
    test_queue_cleanup()

    # Integration tests (need Tally)
    test_poller_queues_on_cloud_down(engine)
    test_poller_flushes_queue(engine)
    test_queue_persistence()

    # E2E tests (need Tally + cloud)
    test_e2e_queue_flush(engine)
    test_flush_idempotency(engine)
    test_sync_full_with_queue(engine)

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
