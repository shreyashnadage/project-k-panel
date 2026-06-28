# -*- coding: utf-8 -*-
"""
Seed script for local e2e testing.

Creates:
  - SQLite database (tally_sync_dev.db)
  - Test tenant with known API key
  - Test client (MSME)
  - Test device registration
  - One pending sync_ledgers command

Run: python tests/seed_e2e.py
"""

import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta

# Force SQLite for local dev
os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from cloudplatform.db.database import engine, SessionLocal
from cloudplatform.db.models import (
    Base, Tenant, Client, DeviceRegistration, SyncCommand,
)

# ── Constants ─────────────────────────────────────────────────────────────────

TEST_API_KEY     = "test-api-key-e2e-local-dev"
TEST_TENANT_ID   = "tenant-e2e-001"
TEST_CLIENT_ID   = "client-e2e-001"
TEST_DEVICE_ID   = "device-e2e-001"
TEST_COMPANY     = "Bhrama Enterprises"


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Tenant ────────────────────────────────────────────────────────────
        existing = db.query(Tenant).filter(Tenant.id == TEST_TENANT_ID).first()
        if existing:
            print(f"Tenant '{TEST_TENANT_ID}' already exists — skipping seed")
            _create_command(db)
            return

        tenant = Tenant(
            id=TEST_TENANT_ID,
            name="E2E Test Tenant",
            api_key_hash=hashlib.sha256(TEST_API_KEY.encode()).hexdigest(),
            is_active=True,
        )
        db.add(tenant)

        # ── Client ────────────────────────────────────────────────────────────
        client = Client(
            client_id=TEST_CLIENT_ID,
            company_name=TEST_COMPANY,
            email="test@e2e.local",
            status="active",
        )
        db.add(client)

        # ── Device ────────────────────────────────────────────────────────────
        device = DeviceRegistration(
            device_id=TEST_DEVICE_ID,
            client_id=TEST_CLIENT_ID,
            device_name="E2E-Dev-Machine",
            os_version="Windows 11",
            agent_version="0.1.0",
            registration_token="reg-token-e2e",
            api_key=TEST_API_KEY,
            status="active",
        )
        db.add(device)

        db.commit()
        print(f"[OK] Tenant:  {TEST_TENANT_ID}")
        print(f"[OK] Client:  {TEST_CLIENT_ID} ({TEST_COMPANY})")
        print(f"[OK] Device:  {TEST_DEVICE_ID}")
        print(f"[OK] API Key: {TEST_API_KEY}")

        _create_command(db)

    finally:
        db.close()


def _create_command(db):
    """Create a pending sync_ledgers command for the test device."""
    now = datetime.now(timezone.utc)
    cmd = SyncCommand(
        tenant_id=TEST_TENANT_ID,
        device_id=TEST_DEVICE_ID,
        command_type="sync_ledgers",
        params='{"company_name": "Bhrama Enterprises", "company_id": "client-e2e-001"}',
        status="pending",
        created_by="seed_script",
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    print(f"\n[OK] Pending command created: {cmd.id}")
    print(f"  type:   sync_ledgers")
    print(f"  device: {TEST_DEVICE_ID}")
    print(f"  status: pending")


if __name__ == "__main__":
    seed()
    print("\n" + "=" * 50)
    print("Seed complete! Now run:")
    print("  1. Start cloud:  python -m uvicorn cloudplatform.main:app --port 8000")
    print("  2. Start agent:  python -m agent.main")
    print("=" * 50)
