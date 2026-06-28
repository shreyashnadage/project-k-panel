# ⚡ Quick Installation Test Plan

## 🎯 Key Point: Completely Headless

**NO UI. NO Dialogs. NO Wizard.**

Configuration via `.env.local` file only.

---

## 🚀 Fastest Test (15 minutes)

### Step 1: Create Configuration
```powershell
# Create .env.local in project root
@"
TALLY_COMPANY_GUID=test-guid-12345
CLOUD_API_KEY=test-key-67890
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://15.206.90.21:8000
"@ | Set-Content "D:\tally-shayak\.env.local"
```

### Step 2: Run Exe
```bash
cd D:\tally-shayak\dist
TallySyncAgent.exe
```

### Step 3: Watch Output
```
[INFO] TALLY SYNC AGENT STARTUP
[INFO] TALLY API SETUP
[INFO] Starting Tally API Connector...
[INFO] ✓ Tally API is responding
[INFO] SYNC CYCLE START
[INFO] Extracting ledgers...
[INFO] SYNC COMPLETE - Status: success
```

### Step 4: Verify
✅ No errors  
✅ Tally API started  
✅ Sync completed  

**Done!** Agent works end-to-end.

---

## 📝 What to Expect

### No UI Means:
```
❌ No installer wizard
❌ No configuration dialogs
❌ No setup screens
❌ No prompts

✅ Logs to console/file
✅ All feedback text-based
✅ Configuration via files
✅ Automated everything
```

### Behavior:
```
exe starts
  ↓
reads .env.local
  ↓
validates required fields
  ↓
starts Tally setup
  ↓
checks Tally connectivity
  ↓
extracts data
  ↓
transmits to cloud
  ↓
exits (or waits for next cycle)
```

---

## ✅ Test Cases

### Test 1: Happy Path (Most Important)
```powershell
# Setup: Everything running
# Config: Valid .env.local

# Run
TallySyncAgent.exe

# Expect: Success message
# ✓ SYNC COMPLETE - Status: success
```

### Test 2: Missing Config
```powershell
# Setup: No .env.local file

# Run
TallySyncAgent.exe

# Expect: Error message
# [ERROR] Missing required environment variables
# [ERROR] Set: TALLY_COMPANY_GUID, CLOUD_API_KEY
```

### Test 3: Tally Down
```powershell
# Setup: Close TallyPrime first

# Run
TallySyncAgent.exe

# Expect: Warning, but continues
# [WARNING] Tally API setup failed, proceeding anyway...
# [ERROR] Tally unreachable
# [INFO] SYNC CYCLE COMPLETE - Status: tally_unreachable
```

### Test 4: Cloud Down
```powershell
# Setup: Stop AWS backend

# Run
TallySyncAgent.exe

# Expect: Retry logic
# [ERROR] Transmission failed
# [INFO] Retrying... (exponential backoff)
```

---

## 📊 Configuration Reference

```
REQUIRED:
├─ TALLY_COMPANY_GUID        (no default, exit if missing)
└─ CLOUD_API_KEY             (no default, exit if missing)

OPTIONAL (with defaults):
├─ TALLY_URL                 → http://localhost:9000
├─ TALLY_COMPANY_NAME        → Bhrama Enterprises
├─ CLOUD_API_URL             → http://localhost:8000
└─ CLOUD_TENANT_ID           → test-tenant-001
```

---

## 🧪 Simple Test Flow

```
1. Create .env.local (2 min)
   TALLY_COMPANY_GUID=your-guid
   CLOUD_API_KEY=your-key

2. Run exe (3 min)
   TallySyncAgent.exe

3. Check logs (5 min)
   Get-Content logs\tally_sync_service.log

4. Verify output (5 min)
   ✓ No errors
   ✓ Tally connected
   ✓ Data synced
```

**Total: ~15 minutes**

---

## 🔍 Verification

### Success Indicators
```
✅ No error messages
✅ "SYNC COMPLETE - Status: success"
✅ Log file created
✅ Data queued locally
✅ Cloud received records
```

### Failure Indicators
```
❌ "Missing required environment variables"
❌ "Tally unreachable" (if Tally isn't running)
❌ Unhandled exceptions
❌ Memory leaks
```

---

## 📋 Checklist

### Before Running
- [ ] .env.local created with required values
- [ ] TallyPrime running (for happy path test)
- [ ] AWS backend running
- [ ] Port 9000 accessible (Tally API)
- [ ] Port 8000 accessible (Cloud API)

### During Running
- [ ] Watch console output
- [ ] No UI dialogs appear (headless!)
- [ ] No hanging/frozen processes
- [ ] Reasonable memory usage (<500MB)

### After Running
- [ ] Log file created
- [ ] Check last 20 lines of log
- [ ] Verify sync completed
- [ ] Data in database

---

## 🛠️ Debugging

### Run in Debug Mode
```bash
cd D:\tally-shayak

# Run directly (shows console output)
python agent/main.py

# Watch logs real-time
Get-Content logs\tally_sync_service.log -Wait
```

### Check Configuration
```bash
# View loaded config
Get-Content .env.local

# Test connectivity
curl http://localhost:9000/        # Tally
curl http://15.206.90.21:8000/     # Cloud
```

### View Tally Setup
```bash
# Check if Tally connector is running
Get-Process | grep TallyAPIConnector

# Check port 9000
netstat -ano | findstr "9000"
```

---

## ✨ Key Points

✅ **Headless = No UI needed**
✅ **Completely automated**
✅ **Configuration-driven**
✅ **Full logging**
✅ **Error handling**
✅ **Production-ready**

---

**Ready to test? Start with Test 1 (Happy Path)!**

See full guide: [INSTALLATION_TESTING_GUIDE.md](INSTALLATION_TESTING_GUIDE.md)
