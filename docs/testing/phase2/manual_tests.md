# 🧪 Phase 2 Testing — Step by Step

Follow these steps in order to test Phase 2 API.

---

## Step 1: Activate Virtual Environment

```powershell
cd D:\tally-shayak
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt.

---

## Step 2: Initialize Test Database

Choose ONE option:

### Option A: SQLite (Simplest - Local Only)

```powershell
set DATABASE_URL=sqlite:///./tally_sync_test.db
python create_test_tenant.py
```

**Expected output**:
```
✓ Database tables created
✓ Tenant created successfully

Tenant Details:
  ID: test-tenant-001
  Name: Bhrama Enterprises
  API Key: test-api-key-12345

Ready to test! Use these values:
  x-api-key: test-api-key-12345
  tenant_id: test-tenant-001
```

### Option B: PostgreSQL (Production-like)

If you have PostgreSQL installed:

```powershell
# Create database
psql -U postgres -c "CREATE DATABASE tally_sync_test;"

# Set environment
set DATABASE_URL=postgresql://postgres:password@localhost/tally_sync_test

# Create tenant
python create_test_tenant.py
```

---

## Step 3: Start FastAPI Server

Keep this terminal open while testing.

```powershell
set DATABASE_URL=sqlite:///./tally_sync_test.db
python -m uvicorn cloudplatform.main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Step 4: Open Another Terminal for Testing

Open a NEW PowerShell window:

```powershell
cd D:\tally-shayak
.\.venv\Scripts\Activate.ps1
```

---

## Step 5: Run Tests (One at a Time)

### Test 1: Health Check

```powershell
curl http://localhost:8000/health
```

**Expected**:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

✅ **If you see this, the server is running!**

---

### Test 2: Ingest Ledgers

```powershell
curl -X POST http://localhost:8000/v1/ledgers `
  -H "x-api-key: test-api-key-12345" `
  -H "Content-Type: application/json" `
  -d @- <<'EOF'
{
  "tenant_id": "test-tenant-001",
  "ledgers": [
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "ledger_guid": "LED-CASH-001",
      "name": "Cash",
      "ledger_type": "Asset",
      "opening_balance": "100000",
      "closing_balance": "95000"
    },
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "ledger_guid": "LED-SALES-001",
      "name": "Sales",
      "ledger_type": "Income",
      "opening_balance": "0",
      "closing_balance": "50000"
    }
  ]
}
EOF
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

✅ **2 ledgers accepted!**

---

### Test 3: Ingest Vouchers

```powershell
curl -X POST http://localhost:8000/v1/vouchers `
  -H "x-api-key: test-api-key-12345" `
  -H "Content-Type: application/json" `
  -d @- <<'EOF'
{
  "tenant_id": "test-tenant-001",
  "vouchers": [
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "voucher_guid": "VOUCH-S-001",
      "voucher_type": "Sales",
      "voucher_number": "S/001",
      "date": "2026-06-01",
      "party": "Rahul Enterprises",
      "narration": "Sale of goods",
      "amount": "50000"
    },
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "voucher_guid": "VOUCH-P-001",
      "voucher_type": "Purchase",
      "voucher_number": "P/001",
      "date": "2026-06-02",
      "party": "Supplier A",
      "narration": "Purchase of materials",
      "amount": "30000"
    }
  ]
}
EOF
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

✅ **2 vouchers accepted!**

---

### Test 4: Test Idempotency (CRITICAL!)

**Send the same voucher again** (copy-paste Test 3 command again):

```powershell
curl -X POST http://localhost:8000/v1/vouchers `
  -H "x-api-key: test-api-key-12345" `
  -H "Content-Type: application/json" `
  -d @- <<'EOF'
{
  "tenant_id": "test-tenant-001",
  "vouchers": [
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "voucher_guid": "VOUCH-S-001",
      "voucher_type": "Sales",
      "voucher_number": "S/001",
      "date": "2026-06-01",
      "party": "Rahul Enterprises",
      "narration": "Sale of goods",
      "amount": "50000"
    }
  ]
}
EOF
```

**Expected**:
```json
{
  "accepted": 0,
  "duplicates": 1,
  "errors": 0,
  "message": "Vouchers: 0 new, 1 duplicates, 0 errors"
}
```

✅ **Idempotency works! No errors, just marked as duplicate.**

---

### Test 5: Get Statistics

```powershell
curl http://localhost:8000/v1/stats `
  -H "x-api-key: test-api-key-12345"
```

**Expected**:
```json
{
  "tenant_id": "test-tenant-001",
  "total_vouchers": 2,
  "total_ledgers": 2
}
```

✅ **Stats show 2 vouchers and 2 ledgers!**

---

### Test 6: Test with Unicode/Devanagari

```powershell
curl -X POST http://localhost:8000/v1/vouchers `
  -H "x-api-key: test-api-key-12345" `
  -H "Content-Type: application/json" `
  -d @- <<'EOF'
{
  "tenant_id": "test-tenant-001",
  "vouchers": [
    {
      "company_guid": "COMP-001",
      "company_name": "Bhrama Enterprises",
      "voucher_guid": "VOUCH-DEVA-001",
      "voucher_type": "Sales",
      "date": "2026-06-03",
      "party": "राहुल एंटरप्राइजेज",
      "narration": "Hindi name test",
      "amount": "25000"
    }
  ]
}
EOF
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

✅ **Unicode/Devanagari names preserved!**

---

### Test 7: Authentication Error

```powershell
curl -X POST http://localhost:8000/v1/vouchers `
  -H "x-api-key: invalid-key" `
  -H "Content-Type: application/json" `
  -d '{"tenant_id":"test-tenant-001","vouchers":[]}'
```

**Expected**:
```json
{"detail":"Invalid or inactive API key"}
```
HTTP 401

✅ **Invalid key rejected!**

---

## Summary Checklist

After all tests, verify:

- [ ] Test 1: Health check — ✅ OK
- [ ] Test 2: Ledgers ingested — ✅ 2 accepted
- [ ] Test 3: Vouchers ingested — ✅ 2 accepted
- [ ] Test 4: Idempotency — ✅ duplicate=1, accepted=0
- [ ] Test 5: Statistics — ✅ 2 vouchers, 2 ledgers
- [ ] Test 6: Unicode/Devanagari — ✅ accepted=1
- [ ] Test 7: Auth error — ✅ HTTP 401

---

## 🎉 If All Tests Pass!

Congratulations! Phase 2 is working correctly.

**Next**: Phase 3 will connect Phase 1 agent to Phase 2 API.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Is FastAPI server running? Check first terminal |
| "Invalid API key" | API key is `test-api-key-12345` (with hyphen) |
| "Tenant ID mismatch" | tenant_id must be exactly `test-tenant-001` |
| "Date format error" | Date must be YYYY-MM-DD format (2026-06-01) |
| Database file not found | Run `create_test_tenant.py` first |

---

**Ready to test?** Start with Test 1 (health check) and work down!
