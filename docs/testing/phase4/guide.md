# 🧪 Phase 4: Windows Service & Installer Testing

**Goal**: Validate service installation, scheduling, and long-running stability

---

## Setup (5 minutes)

### Prerequisites
- Windows 10 (1909+) or Windows 11 clean VM
- Admin access
- NSSM installed: https://nssm.cc/download
- Python 3.12 installed

### Step 1: Download & Install

```bash
# Download installer
TallySyncAgent-0.4.0-setup.exe

# Run installer (double-click or)
TallySyncAgent-0.4.0-setup.exe

# Follow wizard:
#  - Accept license
#  - Choose install directory (default OK)
#  - Optional: Desktop icon, Auto-start
#  - Click Install

# Wait for installation to complete (~30s)
```

### Step 2: Configure Service

```bash
# Edit configuration
cd "C:\Program Files\Tally Sync Agent"
notepad .env.local

# Set your values:
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-guid
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://your-api.com
CLOUD_API_KEY=your-key
CLOUD_TENANT_ID=tenant-001

# Save and close
```

---

## Test Scenarios

### Test 1: Service Installation

```powershell
# Verify service exists
nssm status TallySyncAgent

# Expected: SERVICE_INSTALLED (or similar status message)
```

✅ **Pass**: Service shows as installed  
❌ **Fail**: Service not found (re-run installer)

---

### Test 2: Service Start/Stop

```powershell
# Start service
nssm start TallySyncAgent
Start-Sleep -Seconds 5

# Check status
nssm status TallySyncAgent

# Expected: SERVICE_RUNNING
```

✅ **Pass**: Service starts and runs  
❌ **Fail**: Check logs for errors

```powershell
# Stop service
nssm stop TallySyncAgent
Start-Sleep -Seconds 2

# Check status
nssm status TallySyncAgent

# Expected: SERVICE_STOPPED
```

✅ **Pass**: Service stops cleanly  
❌ **Fail**: Service may need force-stop

---

### Test 3: Logging

```powershell
# View logs
$logFile = "C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log"
Get-Content $logFile -Tail 50

# Expected output:
#   SERVICE STARTED
#   SYNC CYCLE STARTING
#   Connected to Tally
#   Extracted X records
#   SYNC CYCLE COMPLETE
```

✅ **Pass**: Logs show successful sync  
❌ **Fail**: Check error messages in logs

---

### Test 4: Scheduled Sync (6-hour interval)

```powershell
# Option A: Run immediately for testing
# Edit .env.local:
TALLY_SYNC_INTERVAL_HOURS=0.1    # 6 minutes instead of 6 hours

# Restart service
nssm restart TallySyncAgent

# Wait for next sync (~6 minutes)
# Monitor logs
Get-Content $logFile -Wait -Tail 20

# After sync completes, restore interval:
TALLY_SYNC_INTERVAL_HOURS=6
nssm restart TallySyncAgent
```

✅ **Pass**: Sync runs on schedule, logs show completion  
❌ **Fail**: Check Tally connectivity, API key

---

### Test 5: Data Transmission

```powershell
# After a sync completes, check cloud API
# Option A: Via API
curl http://your-api.com/v1/stats \
  -H "x-api-key: your-key"

# Expected:
# {
#   "total_vouchers": 50,
#   "total_ledgers": 10
# }

# Option B: Query database directly
psql your-db -c "SELECT COUNT(*) FROM vouchers;"

# Expected: Number > 0
```

✅ **Pass**: Data arrived in cloud DB  
❌ **Fail**: Check cloud API connectivity, API key

---

### Test 6: Crash Recovery

```powershell
# Simulate process crash
# Find service process
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Kill process
Stop-Process -Name "pythonw" -Force

# Wait 10 seconds
Start-Sleep -Seconds 10

# Check service status
nssm status TallySyncAgent

# Expected: SERVICE_RUNNING (auto-restarted)
```

✅ **Pass**: Service auto-restarts after crash  
❌ **Fail**: NSSM restart policy may need adjustment

---

### Test 7: Uninstallation

```powershell
# Uninstall service
nssm remove TallySyncAgent confirm

# Verify removal
nssm status TallySyncAgent
# Expected: Service not found

# Uninstall via Control Panel or
TallySyncAgent-0.4.0-setup.exe /UNINSTALL

# Verify directory cleaned
```

✅ **Pass**: Service removed cleanly, files cleaned  
❌ **Fail**: Manually remove via Services.msc

---

## Phase 4 Gate Checklist

- [ ] Test 1: Service Installation ✅
- [ ] Test 2: Service Start/Stop ✅
- [ ] Test 3: Logging ✅
- [ ] Test 4: Scheduled Sync ✅
- [ ] Test 5: Data Transmission ✅
- [ ] Test 6: Crash Recovery ✅
- [ ] Test 7: Uninstallation ✅

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "NSSM not found" | Install NSSM and add to PATH |
| Service won't start | Check logs, verify Python path, check .env.local |
| No sync happening | Check interval in .env.local, verify Tally is running |
| Data not in cloud DB | Check API key, verify network connectivity |
| Service crashes | Check logs for specific errors, increase sync interval |
| Can't uninstall | Use Services.msc to stop, then uninstall |

---

## Monitoring in Production

### Daily Checks
```powershell
# Service status
nssm status TallySyncAgent

# Last sync result
Get-Content $logFile -Tail 50 | Where-Object {$_ -match "SYNC CYCLE"}

# Record count
psql your-db -c "SELECT COUNT(*) as total FROM vouchers WHERE created_at > NOW() - INTERVAL '1 day';"
```

### Weekly Maintenance
```powershell
# Archive logs
Move-Item $logFile "$logFile.backup"

# Check for errors in backups
Get-Content "$logFile.backup" | Where-Object {$_ -match "ERROR"}

# Restart service (clean)
nssm restart TallySyncAgent
```

---

## Performance Baselines

Expected metrics:
- **Service startup**: <5 seconds
- **Sync cycle**: 5-15 minutes (depends on data volume)
- **Memory usage**: 50-150 MB
- **CPU usage**: <10% during sync, <1% idle
- **Log file growth**: ~5-10 MB per week

---

## Success Criteria

✅ **Phase 4 is successful when**:
1. Service installs without errors
2. Service starts/stops cleanly
3. Syncs run on schedule (every 6 hours)
4. Data reaches cloud database
5. Logs show clean completion
6. Service survives crash and restarts
7. Uninstallation cleans up properly

---

**Ready to test?** Start with Test 1 and work through each scenario!
