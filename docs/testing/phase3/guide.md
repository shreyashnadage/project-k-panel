# 🧪 Phase 3: End-to-End Pipeline Testing

**Goal**: Validate data flowing from Tally → Queue → Cloud API → Database

---

## Setup (5 minutes)

### Terminal 1: Start Cloud API

```powershell
cd D:\tally-shayak
.\.venv\Scripts\Activate.ps1
set DATABASE_URL=sqlite:///./tally_sync_test.db
python create_test_tenant.py
python -m uvicorn cloudplatform.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Terminal 2: Create Configuration

Create `.env.local` with:

```
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-company-guid-here

CLOUD_API_URL=http://localhost:8000
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
```

---

## Test Scenarios

### Test 1: Queue Manager (Offline Resilience)

```powershell
cd D:\tally-shayak
.\.venv\Scripts\Activate.ps1

python -c "
from agent.queue.manager import QueueManager

# Create queue
q = QueueManager()

# Enqueue a voucher (as if Tally is offline)
voucher = {
    'company_guid': 'COMP-001',
    'voucher_guid': 'TEST-VOUCH-001',
    'voucher_type': 'Sales',
    'date': '2026-06-01',
    'party': 'Customer A',
    'amount': '50000',
}
result = q.enqueue_voucher(voucher)
print(f'Enqueued: {result}')

# Check queue
stats = q.get_stats()
print(f'Queue stats: {stats}')

# Get pending
pending = q.get_pending()
print(f'Pending records: {len(pending)}')
for r in pending:
    print(f'  - {r[\"type\"]}: {r[\"data\"].get(\"voucher_guid\")}')
"
```

**Expected output**:
```
Enqueued: True
Queue stats: {'pending': 1, 'sent': 0, 'failed': 0}
Pending records: 1
  - voucher: TEST-VOUCH-001
```

✅ **Queue is working! Records persist even if process crashes.**

---

### Test 2: Transmitter Client (Cloud API Integration)

```powershell
python -c "
from agent.transmitter.client import TransmitterClient

# Create client
client = TransmitterClient(
    base_url='http://localhost:8000',
    api_key='test-api-key-12345',
    tenant_id='test-tenant-001',
)

# Check health
is_healthy = client.is_healthy()
print(f'Cloud API healthy: {is_healthy}')

# Try to send a voucher
vouchers = [{
    'company_guid': 'COMP-001',
    'company_name': 'Test',
    'voucher_guid': 'TX-VOUCH-001',
    'voucher_type': 'Sales',
    'date': '2026-06-01',
    'party': 'Customer B',
    'amount': '75000',
}]

response = client.send_vouchers(vouchers)
print(f'Response: {response}')
"
```

**Expected output**:
```
Cloud API healthy: True
Response: {'accepted': 1, 'duplicates': 0, 'errors': 0, 'message': 'Vouchers: 1 new, 0 duplicates, 0 errors'}
```

✅ **Transmitter is working! Data reaching cloud API.**

---

### Test 3: End-to-End Pipeline (Manual)

**Prerequisites**: 
- Tally running with test vouchers (or can skip extraction)
- Cloud API running on port 8000

```powershell
python -c "
from agent.queue.manager import QueueManager
from agent.transmitter.client import TransmitterClient

print('=== PHASE 3: END-TO-END PIPELINE TEST ===')
print()

# Step 1: Queue some records (simulating extraction)
print('[STEP 1] Enqueueing records (simulating extraction)')
q = QueueManager()
q.clear()  # Fresh start

vouchers = [
    {
        'company_guid': 'COMP-001',
        'voucher_guid': 'E2E-VOUCH-001',
        'voucher_type': 'Sales',
        'date': '2026-06-01',
        'party': 'Customer A',
        'amount': '50000',
    },
    {
        'company_guid': 'COMP-001',
        'voucher_guid': 'E2E-VOUCH-002',
        'voucher_type': 'Purchase',
        'date': '2026-06-02',
        'party': 'Supplier B',
        'amount': '30000',
    },
]

for v in vouchers:
    q.enqueue_voucher(v)

stats = q.get_stats()
print(f'✓ Queued {stats[\"pending\"]} vouchers')
print()

# Step 2: Get pending records
print('[STEP 2] Getting pending records from queue')
pending = q.get_pending()
print(f'✓ Retrieved {len(pending)} pending records')
print()

# Step 3: Transmit to cloud
print('[STEP 3] Transmitting to cloud API')
client = TransmitterClient(
    base_url='http://localhost:8000',
    api_key='test-api-key-12345',
    tenant_id='test-tenant-001',
)

vouchers_to_send = [p['data'] for p in pending if p['type'] == 'voucher']
response = client.send_vouchers(vouchers_to_send)
print(f'✓ API response: {response[\"message\"]}')
print()

# Step 4: Mark as sent in queue
print('[STEP 4] Marking records as sent')
for record in pending:
    q.mark_sent(record['id'])

stats = q.get_stats()
print(f'✓ Queue stats after transmission:')
print(f'  - Pending: {stats[\"pending\"]}')
print(f'  - Sent: {stats[\"sent\"]}')
print(f'  - Failed: {stats[\"failed\"]}')
print()

print('✅ END-TO-END PIPELINE TEST PASSED')
"
```

**Expected output**:
```
=== PHASE 3: END-TO-END PIPELINE TEST ===

[STEP 1] Enqueueing records (simulating extraction)
✓ Queued 2 vouchers

[STEP 2] Getting pending records from queue
✓ Retrieved 2 pending records

[STEP 3] Transmitting to cloud API
✓ API response: Vouchers: 2 new, 0 duplicates, 0 errors

[STEP 4] Marking records as sent
✓ Queue stats after transmission:
  - Pending: 0
  - Sent: 2
  - Failed: 0

✅ END-TO-END PIPELINE TEST PASSED
```

✅ **Complete pipeline working!**

---

### Test 4: Idempotency (Critical for Reliability)

```powershell
python -c "
from agent.transmitter.client import TransmitterClient

client = TransmitterClient(
    base_url='http://localhost:8000',
    api_key='test-api-key-12345',
    tenant_id='test-tenant-001',
)

# Same voucher twice
voucher = {
    'company_guid': 'COMP-001',
    'company_name': 'Test',
    'voucher_guid': 'IDEMPOTENT-TEST',
    'voucher_type': 'Sales',
    'date': '2026-06-03',
    'party': 'Customer C',
    'amount': '25000',
}

# First send
print('Sending voucher (first time)...')
r1 = client.send_vouchers([voucher])
print(f'Response 1: accepted={r1[\"accepted\"]}, duplicates={r1[\"duplicates\"]}')
print()

# Second send (same voucher)
print('Sending same voucher (second time)...')
r2 = client.send_vouchers([voucher])
print(f'Response 2: accepted={r2[\"accepted\"]}, duplicates={r2[\"duplicates\"]}')
print()

if r2['accepted'] == 0 and r2['duplicates'] == 1:
    print('✅ IDEMPOTENCY PASSED: No duplicate key error!')
else:
    print('❌ IDEMPOTENCY FAILED')
"
```

**Expected output**:
```
Sending voucher (first time)...
Response 1: accepted=1, duplicates=0

Sending same voucher (second time)...
Response 2: accepted=0, duplicates=1

✅ IDEMPOTENCY PASSED: No duplicate key error!
```

---

### Test 5: Offline Queue Resilience

Simulates network outage and recovery:

```powershell
python -c "
from agent.queue.manager import QueueManager
from agent.transmitter.client import TransmitterClient

print('=== OFFLINE RESILIENCE TEST ===')
print()

q = QueueManager('offline_test.db')
q.clear()

# Phase 1: Network is DOWN (agent continues extracting)
print('[PHASE 1] Network DOWN - Agent extracts to queue')
for i in range(5):
    q.enqueue_voucher({
        'company_guid': 'COMP-001',
        'voucher_guid': f'OFFLINE-{i:03d}',
        'voucher_type': 'Sales',
        'date': '2026-06-01',
    })

stats = q.get_stats()
print(f'Queue has {stats[\"pending\"]} pending records (waiting for network)')
print()

# Phase 2: Network comes back online
print('[PHASE 2] Network is UP - Transmitting queued records')
client = TransmitterClient(
    base_url='http://localhost:8000',
    api_key='test-api-key-12345',
    tenant_id='test-tenant-001',
)

pending = q.get_pending()
vouchers = [p['data'] for p in pending]
response = client.send_vouchers(vouchers)
print(f'Transmitted: {response[\"accepted\"]} new, {response[\"duplicates\"]} duplicates')

# Mark as sent
for p in pending:
    q.mark_sent(p['id'])

stats = q.get_stats()
print(f'Queue after transmission: {stats[\"pending\"]} pending, {stats[\"sent\"]} sent')
print()

print('✅ OFFLINE RESILIENCE PASSED')
"
```

---

## Unit Tests

Run automated tests:

```powershell
# All Phase 3 tests
python -m pytest tests/integration/test_e2e_pipeline.py -v

# Specific test
python -m pytest tests/integration/test_e2e_pipeline.py::TestQueueManager::test_queue_survives_restart -v

# Coverage
python -m pytest tests/integration/test_e2e_pipeline.py --cov=agent --cov-report=term-missing
```

---

## Full Orchestrator Test (With Real Tally)

Once Tally has test data:

```powershell
python agent/orchestrator.py
```

This will:
1. Connect to Tally
2. Extract ledgers + vouchers
3. Enqueue to local queue
4. Transmit to cloud API
5. Mark records as sent
6. Print statistics

---

## Phase 3 Gate Checklist

- [ ] Queue manager tests pass (Test 1)
- [ ] Transmitter client tests pass (Test 2)
- [ ] End-to-end pipeline works (Test 3)
- [ ] Idempotency verified (Test 4)
- [ ] Offline queue resilience works (Test 5)
- [ ] Unit tests pass (pytest)
- [ ] Orchestrator can run without errors

---

## Verification Summary

| Test | Status | Notes |
|------|--------|-------|
| Queue persistence | ⏳ Manual | Enqueue voucher, verify stats |
| Cloud transmission | ⏳ Manual | Send to API, verify response |
| End-to-end pipeline | ⏳ Manual | Queue → API → DB flow |
| Idempotency | ⏳ Manual | Send same record twice |
| Offline resilience | ⏳ Manual | Queue survives network outage |
| Unit tests | ⏳ pytest | Run test_e2e_pipeline.py |
| Orchestrator | ⏳ Manual | Run with real Tally |

---

## Next: Watermark Advancement

Once core pipeline works, we'll add watermark tracking for incremental sync (Phase 3 enhancement).

---

**Ready to test?** Start with Test 1 and work through each scenario!
