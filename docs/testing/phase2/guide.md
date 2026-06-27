# Phase 2 Testing Guide

## Quick Start (5 minutes)

### Option 1: SQLite (Local Testing Only)

**1. Create test database file**
```bash
python -c "
import os
os.environ['DATABASE_URL'] = 'sqlite:///./tally_sync_test.db'
from cloudplatform.db.database import init_db
init_db()
print('✓ Database initialized')
"
```

**2. Start the server**
```bash
set DATABASE_URL=sqlite:///./tally_sync_test.db
python -m uvicorn cloudplatform.main:app --reload --port 8000
```

**3. Test in another terminal**
```bash
# Health check
curl http://localhost:8000/health

# Create a test tenant and ingest data
# (see Test Scenarios below)
```

---

### Option 2: PostgreSQL (Recommended for Real Testing)

**Prerequisites**: PostgreSQL installed and running

**1. Create database**
```bash
createdb tally_sync_test
```

**2. Start server**
```bash
set DATABASE_URL=postgresql://postgres:password@localhost/tally_sync_test
python -m uvicorn cloudplatform.main:app --reload --port 8000
```

**3. Test**
```bash
# Same curl commands as Option 1
```

---

## Test Scenarios

### Scenario 1: Health Check
```bash
curl http://localhost:8000/health
```

**Expected**:
```json
{"status": "ok", "service": "tally-sync-ingest"}
```

---

### Scenario 2: Create Test Tenant

First, we need to create a tenant in the database with an API key.

**Run this Python script**:
```python
import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cloudplatform.db.models import Base, Tenant

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tally_sync_test.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create test tenant
api_key = "test-api-key-12345"
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

tenant = Tenant(
    id="test-tenant-001",
    name="Test Company",
    api_key_hash=api_key_hash,
    is_active=True
)
session.add(tenant)
session.commit()
print(f"✓ Tenant created: test-tenant-001")
print(f"✓ API Key: {api_key}")
session.close()
```

Save this as `create_test_tenant.py` and run:
```bash
python create_test_tenant.py
```

---

### Scenario 3: Ingest Ledgers

```bash
curl -X POST http://localhost:8000/v1/ledgers \
  -H "x-api-key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "ledgers": [
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "ledger_guid": "LED-CASH-001",
        "name": "Cash",
        "parent": null,
        "ledger_type": "Asset",
        "opening_balance": "100000",
        "closing_balance": "95000"
      },
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "ledger_guid": "LED-SALES-001",
        "name": "Sales",
        "parent": null,
        "ledger_type": "Income",
        "opening_balance": "0",
        "closing_balance": "50000"
      }
    ]
  }'
```

**Expected**:
```json
{
  "accepted": 2,
  "duplicates": 0,
  "errors": 0,
  "message": "Ledgers: 2 new, 0 duplicates, 0 errors"
}
```

---

### Scenario 4: Ingest Vouchers

```bash
curl -X POST http://localhost:8000/v1/vouchers \
  -H "x-api-key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "vouchers": [
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "voucher_guid": "VOUCH-S-001",
        "voucher_type": "Sales",
        "voucher_number": "S/001",
        "date": "2026-06-01",
        "party": "Rahul Enterprises",
        "narration": "Sale of goods",
        "amount": "50000",
        "agent_version": "0.1.0"
      },
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "voucher_guid": "VOUCH-P-001",
        "voucher_type": "Purchase",
        "voucher_number": "P/001",
        "date": "2026-06-02",
        "party": "Supplier A",
        "narration": "Purchase of materials",
        "amount": "30000"
      }
    ]
  }'
```

**Expected**:
```json
{
  "accepted": 2,
  "duplicates": 0,
  "errors": 0,
  "message": "Vouchers: 2 new, 0 duplicates, 0 errors"
}
```

---

### Scenario 5: Test Idempotency (Critical!)

**Send the same voucher batch again**:
```bash
curl -X POST http://localhost:8000/v1/vouchers \
  -H "x-api-key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "vouchers": [
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "voucher_guid": "VOUCH-S-001",
        "voucher_type": "Sales",
        "voucher_number": "S/001",
        "date": "2026-06-01",
        "party": "Rahul Enterprises",
        "narration": "Sale of goods",
        "amount": "50000"
      }
    ]
  }'
```

**Expected** (CRITICAL for reliability):
```json
{
  "accepted": 0,
  "duplicates": 1,
  "errors": 0,
  "message": "Vouchers: 0 new, 1 duplicates, 0 errors"
}
```

✅ **This proves idempotency works!** Same GUID = treated as duplicate, no error

---

### Scenario 6: Test with Unicode/Devanagari

```bash
curl -X POST http://localhost:8000/v1/vouchers \
  -H "x-api-key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "vouchers": [
      {
        "company_guid": "COMP-001",
        "company_name": "Test Company",
        "voucher_guid": "VOUCH-DEVA-001",
        "voucher_type": "Sales",
        "date": "2026-06-03",
        "party": "राहुल एंटरप्राइजेज",
        "narration": "Hindi name test",
        "amount": "25000"
      }
    ]
  }'
```

**Expected**:
```json
{
  "accepted": 1,
  "duplicates": 0,
  "errors": 0,
  "message": "Vouchers: 1 new, 0 duplicates, 0 errors"
}
```

---

### Scenario 7: Get Statistics

```bash
curl http://localhost:8000/v1/stats \
  -H "x-api-key: test-api-key-12345"
```

**Expected**:
```json
{
  "tenant_id": "test-tenant-001",
  "total_vouchers": 3,
  "total_ledgers": 2
}
```

---

### Scenario 8: Test Authentication

**Missing API key**:
```bash
curl -X POST http://localhost:8000/v1/vouchers \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test-tenant-001","vouchers":[]}'
```

**Expected**: HTTP 422 (Missing header)

**Invalid API key**:
```bash
curl -X POST http://localhost:8000/v1/vouchers \
  -H "x-api-key: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test-tenant-001","vouchers":[]}'
```

**Expected**: HTTP 401 (Invalid or inactive API key)

---

## Verification Checklist

After running all scenarios, verify:

- [ ] Health check responds with status "ok"
- [ ] Can create test tenant
- [ ] Can ingest ledgers (accepted=2)
- [ ] Can ingest vouchers (accepted=2)
- [ ] **Idempotency works** (duplicate=1 on second send)
- [ ] Unicode/Devanagari names preserved correctly
- [ ] Stats endpoint shows correct counts (3 vouchers, 2 ledgers)
- [ ] Authentication rejects invalid API keys
- [ ] Server handles errors gracefully (no 500 errors)

---

## Database Inspection

**Check what was ingested**:

### SQLite:
```bash
# List all vouchers
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cloudplatform.db.models import Voucher

engine = create_engine('sqlite:///./tally_sync_test.db')
Session = sessionmaker(bind=engine)
session = Session()

for v in session.query(Voucher).all():
    print(f'{v.voucher_number}: {v.party} ({v.amount})')
"
```

### PostgreSQL:
```bash
psql tally_sync_test -c "SELECT voucher_number, party, amount FROM vouchers LIMIT 10;"
psql tally_sync_test -c "SELECT COUNT(*) FROM vouchers;"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "no such table" | Run `create_test_tenant.py` first (creates tables) |
| "API key not found" | Check API key matches in create_test_tenant.py |
| "Tenant ID mismatch" | tenant_id must match "test-tenant-001" |
| Server won't start | Check port 8000 isn't in use: `netstat -ano \| findstr :8000` |
| Database connection error | Verify DATABASE_URL is set correctly |

---

## Next: Connect to Phase 1 Agent

Once Phase 2 testing passes, update Phase 1 extraction to POST to the Phase 2 API:
```python
# From run_extraction_json.py, after extracting ledgers:
ingest_client = IngestClient(
    base_url="http://localhost:8000",
    api_key="test-api-key-12345",
    tenant_id="test-tenant-001"
)
response = ingest_client.send_vouchers(extracted_vouchers)
```

---

**Ready to test?** Start with Scenario 1 (health check) and work through each scenario.
