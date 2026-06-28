# Tally Sync Agent - Client Onboarding & Setup Journey

**Date**: 28 June 2026  
**Backend**: AWS (15.206.90.21:8000)  
**Frontend**: Local Dev (localhost:5173)  
**Status**: Ready for manual testing

---

## 📋 COMPLETE ONBOARDING FLOW

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENT ONBOARDING JOURNEY                                   │
└─────────────────────────────────────────────────────────────┘

STEP 1: PORTAL REGISTRATION (Web UI)
       ↓
STEP 2: AGENT DOWNLOAD
       ↓
STEP 3: AGENT INSTALLATION
       ↓
STEP 4: INITIAL SETUP & REGISTRATION
       ↓
STEP 5: FIRST DATA SYNC
       ↓
STEP 6: VERIFY IN DASHBOARD
```

---

## 🎯 STEP 1: PORTAL REGISTRATION (Web UI)

### What Happens

1. User visits registration portal
2. Fills in company details
3. System generates installation key
4. Key sent via email (simulated in test)
5. User downloads agent

### How to Test

#### **1.1 Open Registration Portal**

```
URL: http://localhost:5173/register
```

**In your browser:**
1. Open: http://localhost:5173/register
2. You should see the registration form

#### **1.2 Fill Registration Form**

Fill in the following test data:

| Field | Value |
|-------|-------|
| Company Name | Sharma Traders Pvt Ltd |
| Email | shreya@sharma.com |
| Phone | +91 9876543210 |
| GST ID | 18AABCU1234567Z5 |

**Screenshot of form** (should show):
- [ ] Company Name field (required)
- [ ] Email field (required, with validation)
- [ ] Phone field (optional)
- [ ] GST ID field (optional, 15-char validation)
- [ ] "Create Account" button
- [ ] Info box: "Why Register?"

#### **1.3 Submit Registration**

Click **"Create Account"** button

**Expected Response** (success screen shows):
- ✅ "Registration Successful!" message
- 📋 Your company details
- 🔑 **Installation Key** (format: `TSA-2026-XXXXX`)
- ⏰ "Expires in 30 days"
- 📥 "Next Steps" with action items
- 🔗 "Download Agent" button

**Example Success Screen:**
```
Registration Successful!

Your Details:
  Company: Sharma Traders Pvt Ltd
  Client ID: cli_abc123def456...

Installation Key (Save this!):
  ┌──────────────────────────────────┐
  │ TSA-2026-ABC123DEF456            │  ← Click to copy
  └──────────────────────────────────┘
  
  Expires in: 30 days

Next Steps:
  1. Download TallySyncAgent.exe
  2. Run installer on your office PC
  3. Paste installation key when prompted
  4. Agent will start syncing automatically

[Download Agent Button] [Register Another Button]
```

### Test Scenarios

**Scenario 1: Happy Path** ✅
- Fill all fields correctly
- See success screen
- Copy installation key

**Scenario 2: Validation Errors** ❌
- Try: Empty company name → Should show error
- Try: Invalid email (no @) → Should show error
- Try: Invalid GST (only 14 chars) → Should show error
- Try: Invalid phone format → Should show error

**Scenario 3: Duplicate Email** ⚠️
- Register twice with same email
- Should return error: "Email already registered"
- Try different email

---

## 🔑 STEP 2: GET INSTALLATION KEY

### What You'll Get

After registration, you receive:

```json
{
  "client_id": "cli_abc123def456...",
  "company_name": "Sharma Traders Pvt Ltd",
  "installation_key": "TSA-2026-ABC123DEF456",
  "expires_in_days": 30,
  "message": "Registration successful!"
}
```

### Store This Information

You'll need these later:
- ✅ **client_id**: Used to track your data
- ✅ **installation_key**: One-time setup key (expires in 30 days)

---

## 💻 STEP 3: AGENT INSTALLATION

### Current Status

⚠️ **NOTE**: Agent exe not yet built. For testing, we'll simulate installation.

### Installation Process (When Exe Built)

**On Windows (Office PC):**

```
1. Download TallySyncAgent.exe
2. Run installer (TallySyncAgent-Setup.exe)
3. Windows SmartScreen may appear → Click "More Info" → "Run Anyway"
4. Installer wizard launches
5. Enter installation key: TSA-2026-ABC123DEF456
6. Installer validates key with platform
7. If valid:
   ├─ Agent registered
   ├─ Device ID generated
   ├─ Credentials stored in Windows Credential Manager
   └─ Windows Service installed (NSSM)
8. Restart Windows (or Service starts automatically)
9. Agent starts syncing every 6 hours
```

### What Gets Installed

| Component | Location | Purpose |
|-----------|----------|---------|
| Agent exe | C:\Program Files\TallySyncAgent\ | Main application |
| Config | C:\ProgramData\TallySyncAgent\ | Settings, logs |
| Service | Windows Services | Runs continuously |
| Logs | C:\logs\tally_sync_service.log | Debug info |
| DB | C:\ProgramData\TallySyncAgent\local.db | Local queue |

---

## 🔌 STEP 4: MANUAL AGENT REGISTRATION (For Testing)

### Simulate Agent Registration

Since we're testing without the installer, we'll manually register:

#### **4.1 Call Device Registration API**

```bash
curl -X POST http://15.206.90.21:8000/v1/register-device \
  -H "Content-Type: application/json" \
  -d '{
    "installation_key": "TSA-2026-ABC123DEF456",
    "device_name": "OFFICE-PC-01",
    "os_version": "Windows 11 Build 26200",
    "agent_version": "0.4.0"
  }'
```

**Expected Response:**
```json
{
  "client_id": "cli_abc123def456...",
  "device_id": "dev_xyz789...",
  "api_key": "secret_api_token_here",
  "registration_token": "secret_registration_token",
  "message": "Device registered successfully!"
}
```

#### **4.2 Store Credentials (Simulated)**

In real agent, this goes to Windows Credential Manager. For testing:

```
Credentials Stored:
  client_id: cli_abc123def456...
  device_id: dev_xyz789...
  api_key: secret_api_token_here
  api_base_url: http://15.206.90.21:8000
```

---

## 📤 STEP 5: FIRST DATA SYNC

### What Happens

```
Agent Startup:
  1. Load credentials from secure storage
  2. Initialize Tally client (connect to localhost:9000)
  3. Initialize cloud transmitter (with client_id)
  4. Initialize local queue
  5. Initialize watermark tracker

First Sync Cycle (6 hours after startup):
  1. EXTRACT from Tally
     ├─ Query: SELECT * FROM Ledgers WHERE modified_date >= watermark
     ├─ Query: SELECT * FROM Vouchers WHERE modified_date >= watermark
     ├─ Result: e.g., 150 ledgers + 500 vouchers
     └─ Encode: UTF-16 → UTF-8
  
  2. QUEUE Locally
     ├─ Store in SQLite: pending_ledgers, pending_vouchers
     ├─ Purpose: Survive network failures
     └─ Queue depth: 650 records
  
  3. TRANSMIT to Cloud
     ├─ Endpoint: POST /v1/sync-with-client
     ├─ Headers:
     │  ├─ x-api-key: secret_api_token_here
     │  ├─ x-client-id: cli_abc123def456
     │  └─ x-device-id: dev_xyz789...
     ├─ Payload:
     │  ├─ client_id: cli_abc123def456
     │  ├─ device_id: dev_xyz789...
     │  ├─ extracted_ledgers: 150
     │  ├─ extracted_vouchers: 500
     │  └─ raw_data: {...JSON...}
     └─ Status: 200 OK
  
  4. MARK SENT
     ├─ Update queue: status = "sent"
     └─ Log audit trail
  
  5. ADVANCE WATERMARK
     └─ Remember: Latest sync time (for next cycle)
  
  6. REPORT HEARTBEAT
     └─ Send: device status, version, queue_depth
```

### Simulate First Sync

#### **5.1 Call Sync Endpoint**

```bash
curl -X POST http://15.206.90.21:8000/v1/sync-with-client \
  -H "Content-Type: application/json" \
  -H "x-api-key: secret_api_token_here" \
  -H "x-client-id: cli_abc123def456" \
  -H "x-device-id: dev_xyz789..." \
  -d '{
    "client_id": "cli_abc123def456",
    "device_id": "dev_xyz789...",
    "extracted_ledgers": 150,
    "extracted_vouchers": 500,
    "raw_data": {
      "ledgers": [...],
      "vouchers": [...]
    }
  }'
```

**Expected Response:**
```json
{
  "sync_id": "sync_abc123...",
  "records_received": 650,
  "status": "success",
  "message": "Data synced successfully"
}
```

#### **5.2 What Gets Stored**

**In Platform Database** (AWS PostgreSQL):
```sql
-- sync_records table
INSERT INTO sync_records (
  sync_id, client_id, device_id, tenant_id,
  records_count, extracted_ledgers, extracted_vouchers,
  sync_status, sync_timestamp, created_at
) VALUES (...)

-- registration_audit_log table
INSERT INTO registration_audit_log (
  audit_id, client_id, action, details,
  source_device, ip_address, created_at
) VALUES (
  'audit_xyz...', 'cli_abc123...', 'sync_received',
  '{"records": 650, "ledgers": 150, "vouchers": 500}',
  'OFFICE-PC-01', '192.168.1.100', NOW()
)
```

---

## 📊 STEP 6: VERIFY IN DASHBOARD

### Check Client Statistics

#### **6.1 Query Client Stats Endpoint**

```bash
curl -X GET "http://15.206.90.21:8000/v1/clients/cli_abc123def456/stats" \
  -H "Authorization: Bearer your_api_key"
```

**Expected Response:**
```json
{
  "client_id": "cli_abc123def456",
  "company_name": "Sharma Traders Pvt Ltd",
  "email": "shreya@sharma.com",
  "status": "active",
  "plan": "trial",
  "total_syncs": 1,
  "total_records": 650,
  "total_ledgers": 150,
  "total_vouchers": 500,
  "last_sync": "2026-06-28T10:30:00Z",
  "devices": [
    {
      "device_id": "dev_xyz789...",
      "device_name": "OFFICE-PC-01",
      "os_version": "Windows 11",
      "agent_version": "0.4.0",
      "registered_at": "2026-06-28T10:00:00Z",
      "last_sync_at": "2026-06-28T10:30:00Z",
      "last_ip_address": "192.168.1.100",
      "status": "active"
    }
  ]
}
```

#### **6.2 Verify Data**

Check that:
- ✅ client_id matches registration
- ✅ company_name is correct
- ✅ total_syncs = 1
- ✅ total_records = 650
- ✅ devices list shows your PC
- ✅ last_sync is recent

---

## 🧪 COMPLETE TEST FLOW (Copy & Paste Commands)

### Test 1: Portal Registration

```bash
# Create client
curl -X POST http://15.206.90.21:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Sharma Traders Pvt Ltd",
    "email": "shreya@sharma.com",
    "phone": "+91 9876543210",
    "gst_id": "18AABCU1234567Z5"
  }' | python -m json.tool
```

**Output** (save these values):
```json
{
  "client_id": "cli_...",
  "installation_key": "TSA-2026-...",
  "expires_in_days": 30
}
```

### Test 2: Device Registration

```bash
# Register device (paste installation_key from above)
curl -X POST http://15.206.90.21:8000/v1/register-device \
  -H "Content-Type: application/json" \
  -d '{
    "installation_key": "TSA-2026-...",
    "device_name": "OFFICE-PC-01",
    "os_version": "Windows 11 Build 26200",
    "agent_version": "0.4.0"
  }' | python -m json.tool
```

**Output** (save these values):
```json
{
  "client_id": "cli_...",
  "device_id": "dev_...",
  "api_key": "secret_...",
  "registration_token": "secret_..."
}
```

### Test 3: First Sync

```bash
# Send data sync (use client_id, device_id, api_key from above)
curl -X POST http://15.206.90.21:8000/v1/sync-with-client \
  -H "Content-Type: application/json" \
  -H "x-api-key: secret_..." \
  -H "x-client-id: cli_..." \
  -H "x-device-id: dev_..." \
  -d '{
    "client_id": "cli_...",
    "device_id": "dev_...",
    "extracted_ledgers": 150,
    "extracted_vouchers": 500,
    "raw_data": {}
  }' | python -m json.tool
```

**Output:**
```json
{
  "sync_id": "sync_...",
  "records_received": 650,
  "status": "success"
}
```

### Test 4: Verify Statistics

```bash
# Check client stats (use client_id from Test 1)
curl -X GET "http://15.206.90.21:8000/v1/clients/cli_.../stats" | python -m json.tool
```

**Output** (should show):
```json
{
  "total_syncs": 1,
  "total_records": 650,
  "total_ledgers": 150,
  "total_vouchers": 500,
  "last_sync": "2026-06-28T..."
}
```

---

## 📝 STEP-BY-STEP MANUAL TESTING INSTRUCTIONS

### For Testing (Do This Now)

#### **Option A: Web UI Testing** (Easiest)

1. **Open browser**: http://localhost:5173/register
2. **Fill form**:
   - Company: "Test Company XYZ"
   - Email: "test@yourcompany.com"
   - Phone: "+91 9876543210"
   - GST: "18AABCU1234567Z5"
3. **Click "Create Account"**
4. **Verify success screen**:
   - See "Registration Successful!"
   - See installation key
   - Click to copy key

#### **Option B: Command Line Testing** (Most Thorough)

Create a test script: `test_onboarding.sh`

```bash
#!/bin/bash

API="http://15.206.90.21:8000"
TIMESTAMP=$(date +%s)
EMAIL="test-$TIMESTAMP@company.com"

echo "=========================================="
echo "STEP 1: REGISTER CLIENT"
echo "=========================================="

REGISTER=$(curl -s -X POST "$API/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"company_name\": \"Test Company\",
    \"email\": \"$EMAIL\",
    \"phone\": \"+91 9876543210\",
    \"gst_id\": \"18AABCU1234567Z5\"
  }")

echo "$REGISTER" | python -m json.tool

CLIENT_ID=$(echo "$REGISTER" | python -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
INSTALL_KEY=$(echo "$REGISTER" | python -c "import sys, json; print(json.load(sys.stdin)['installation_key'])")

echo ""
echo "CLIENT_ID: $CLIENT_ID"
echo "INSTALL_KEY: $INSTALL_KEY"

echo ""
echo "=========================================="
echo "STEP 2: REGISTER DEVICE"
echo "=========================================="

DEVICE=$(curl -s -X POST "$API/v1/register-device" \
  -H "Content-Type: application/json" \
  -d "{
    \"installation_key\": \"$INSTALL_KEY\",
    \"device_name\": \"TEST-PC-01\",
    \"os_version\": \"Windows 11\",
    \"agent_version\": \"0.4.0\"
  }")

echo "$DEVICE" | python -m json.tool

DEVICE_ID=$(echo "$DEVICE" | python -c "import sys, json; print(json.load(sys.stdin)['device_id'])")
API_KEY=$(echo "$DEVICE" | python -c "import sys, json; print(json.load(sys.stdin)['api_key'])")

echo ""
echo "DEVICE_ID: $DEVICE_ID"
echo "API_KEY: $API_KEY"

echo ""
echo "=========================================="
echo "STEP 3: SEND FIRST SYNC"
echo "=========================================="

SYNC=$(curl -s -X POST "$API/v1/sync-with-client" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-client-id: $CLIENT_ID" \
  -H "x-device-id: $DEVICE_ID" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"device_id\": \"$DEVICE_ID\",
    \"extracted_ledgers\": 150,
    \"extracted_vouchers\": 500,
    \"raw_data\": {}
  }")

echo "$SYNC" | python -m json.tool

echo ""
echo "=========================================="
echo "STEP 4: VERIFY STATS"
echo "=========================================="

curl -s -X GET "$API/v1/clients/$CLIENT_ID/stats" | python -m json.tool

echo ""
echo "=========================================="
echo "✅ COMPLETE ONBOARDING TEST DONE!"
echo "=========================================="
```

**Run it:**
```bash
bash test_onboarding.sh
```

---

## ✅ VERIFICATION CHECKLIST

After running the complete onboarding:

- [ ] Registration form loaded (http://localhost:5173/register)
- [ ] Form validation working (email, GST)
- [ ] Registration successful
- [ ] Installation key displayed (format: TSA-2026-XXXXX)
- [ ] Client ID generated (format: cli_xxx...)
- [ ] Device registration successful
- [ ] Device ID generated (format: dev_xxx...)
- [ ] API key generated (secret token)
- [ ] First sync received (650 records)
- [ ] Stats endpoint shows total_syncs = 1
- [ ] Stats show total_records = 650
- [ ] Device listed in devices array
- [ ] All timestamps are recent
- [ ] Audit trail logged (registration_audit_log)

---

## 🐛 TROUBLESHOOTING

### Problem: "Backend not responding"
```
Solution: Check AWS backend is up
  curl http://15.206.90.21:8000/
  Should return: {"service": "tally-sync-platform", "status": "ok"}
```

### Problem: "Email already registered"
```
Solution: Use different email (add timestamp to email)
  test-2026062810300001@company.com
```

### Problem: "Installation key invalid"
```
Solution: Copy key exactly from registration response
  Should be format: TSA-2026-XXXXX
  Should not have spaces
```

### Problem: "CORS error in browser"
```
Solution: Backend allows cross-origin from localhost:5173
  If still failing, check CORS settings in cloudplatform/main.py
```

---

## 📞 NEXT STEPS

After successful manual testing:

1. **Build Agent Exe** (Phase 4B)
   - PyInstaller: Python → .exe
   - Code signing: EV certificate

2. **Create Installer** (Phase 4B)
   - Inno Setup wizard
   - Prompts for installation key
   - Registers device automatically

3. **Deploy Full System** (Phase 4C)
   - AWS RDS PostgreSQL
   - EC2 backend
   - S3 agent downloads

4. **OTA Updates** (Phase 5)
   - Squirrel.Windows integration
   - GitHub Actions pipeline
   - Delta update support

---

**Status**: Ready to test! Start with Step 1 (Portal Registration).

