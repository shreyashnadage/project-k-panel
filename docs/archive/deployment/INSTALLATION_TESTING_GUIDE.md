# 🧪 Installation Testing Guide — TallySyncAgent.exe

## 📋 Overview

The TallySyncAgent is **completely headless** (no UI) and can be tested in multiple scenarios:

1. **Standalone Exe** — Single file, run and forget
2. **Windows Service** — Scheduled extraction
3. **Docker Container** — Cloud deployment (future)

---

## ✅ Installation Type: Headless (No UI)

### What This Means

**No Setup Wizard** ❌
- No graphical installer wizard
- No configuration dialogs
- No interactive prompts

**Configuration via Files** ✅
- `.env.local` file for settings
- Read from environment variables
- Command-line arguments (optional)

**Console/Logs Only** ✅
- All feedback via logs
- Service logs in `logs/tally_sync_service.log`
- Console output if run directly

---

## 🔧 Configuration Required

### Before Running Agent

The agent requires a `.env.local` file with these settings:

```
# Tally connection (required)
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Your Company Name
TALLY_COMPANY_GUID=your-company-guid-here

# Cloud API (required)
CLOUD_API_URL=http://15.206.90.21:8000
CLOUD_API_KEY=your-api-key-here
CLOUD_TENANT_ID=test-tenant-001
```

### Required vs Optional

| Variable | Required | Default | Impact |
|----------|----------|---------|--------|
| `TALLY_COMPANY_GUID` | **YES** | None | Agent exits if missing |
| `CLOUD_API_KEY` | **YES** | None | Agent exits if missing |
| `TALLY_URL` | No | http://localhost:9000 | Tally connection endpoint |
| `TALLY_COMPANY_NAME` | No | Bhrama Enterprises | Display name for company |
| `CLOUD_API_URL` | No | http://localhost:8000 | Cloud backend endpoint |
| `CLOUD_TENANT_ID` | No | test-tenant-001 | Cloud tenant identifier |

---

## 🧪 Testing Scenarios

### Scenario 1: Standalone Exe (Simplest)

#### Setup
```
Location: D:\tally-shayak\dist\TallySyncAgent.exe
Size: 13 MB
Type: Standalone (no dependencies)
```

#### Configuration
1. Create file: `D:\tally-shayak\.env.local`
2. Add required settings:
```
TALLY_COMPANY_GUID=test-company-guid-12345
CLOUD_API_KEY=test-api-key-67890
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://15.206.90.21:8000
```

#### Test Execution
```powershell
# Run exe
D:\tally-shayak\dist\TallySyncAgent.exe

# Expected output:
# [INFO] TALLY SYNC AGENT STARTUP
# [INFO] TALLY API SETUP
# [INFO] Starting Tally API Connector...
# [INFO] ✓ Tally API is responding
# [INFO] SYNC CYCLE START
# [INFO] Extracting ledgers...
# [INFO] SYNC COMPLETE
```

#### Verification
- ✅ No errors in console
- ✅ Tally API started
- ✅ Data extracted
- ✅ Check log: `D:\tally-shayak\logs\tally_sync_service.log`

---

### Scenario 2: Windows Service Installation

#### Prerequisites
- NSSM installed (`D:\tally-shayak\build\installer\install_service.bat`)
- Configuration file ready (`.env.local`)
- Admin privileges required

#### Installation Steps

```powershell
# Step 1: Create configuration
# File: C:\Program Files\Tally Sync Agent\.env.local
$config = @"
TALLY_COMPANY_GUID=test-company-guid-12345
CLOUD_API_KEY=test-api-key-67890
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://15.206.90.21:8000
"@
Set-Content "C:\Program Files\Tally Sync Agent\.env.local" $config

# Step 2: Install service
nssm install TallySyncAgent "D:\tally-shayak\dist\TallySyncAgent.exe"

# Step 3: Start service
nssm start TallySyncAgent

# Step 4: Check status
nssm status TallySyncAgent

# Step 5: View logs
Get-Content "C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log" -Wait
```

#### Service Behavior
- Runs every 6 hours (configurable)
- Auto-starts on Windows reboot
- Automatic Tally setup before each sync
- Logs to `logs/tally_sync_service.log`

#### Verification
```powershell
# Check if service is running
Get-Service TallySyncAgent | Select-Object Status

# Expected: Running

# Check for errors
Get-Content logs\tally_sync_service.log | Select-String "ERROR" | Head -10

# Should be empty or minimal errors
```

---

### Scenario 3: Installer Package (End-User Testing)

#### Build Installer
```powershell
# Requires Inno Setup 6 installed
# Download: https://jrsoftware.org/isdl.php

cd D:\tally-shayak\build\installer

# Build (requires Inno Setup)
iscc.exe TallySyncAgent.iss

# Output: TallySyncAgent-0.4.0-setup.exe
```

#### Test Installation
```powershell
# Step 1: Run installer (as Administrator)
& "D:\tally-shayak\build\installer\Output\TallySyncAgent-0.4.0-setup.exe"

# Step 2: Follow installer steps
# - Accept license (auto-accepted)
# - Choose installation directory (default: C:\Program Files\Tally Sync Agent)
# - Select "Start service automatically on Windows startup"
# - Click Install

# Step 3: Installer runs these automatically:
# - Copies files to C:\Program Files\Tally Sync Agent\
# - Creates logs directory
# - Runs install_dependencies.bat
# - Runs install_service.bat
# - Installs Windows Service

# Step 4: Configure (after installation)
$configPath = "C:\Program Files\Tally Sync Agent\.env.local"
Set-Content $configPath @"
TALLY_COMPANY_GUID=test-company-guid-12345
CLOUD_API_KEY=test-api-key-67890
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://15.206.90.21:8000
"@

# Step 5: Restart service for config to take effect
Restart-Service TallySyncAgent -Force
```

#### Verification
- ✅ Service installed: `Get-Service TallySyncAgent`
- ✅ Files in: `C:\Program Files\Tally Sync Agent\`
- ✅ Logs created: `C:\Program Files\Tally Sync Agent\logs\`
- ✅ Service running: `Get-Service TallySyncAgent | Select Status`
- ✅ No errors in log file

---

## 🚦 Test Cases

### Test 1: Missing Configuration

**Setup**: No `.env.local` file

**Expected Behavior**:
```
[ERROR] Missing required environment variables
[ERROR] Set: TALLY_COMPANY_GUID, CLOUD_API_KEY
```

**Verification**: ✅ Exits with clear error message

---

### Test 2: Tally Not Reachable

**Setup**: Valid config, but Tally not running

**Expected Behavior**:
```
[INFO] Starting Tally API Connector...
[INFO] Tally API setup process started
[WARNING] Tally API not responding after 30s
[WARNING] Tally API setup failed, proceeding anyway...
[ERROR] Tally unreachable
[INFO] SYNC CYCLE COMPLETE - Status: tally_unreachable
```

**Verification**: ✅ Handles gracefully, doesn't crash

---

### Test 3: Cloud API Unreachable

**Setup**: Valid Tally config, but cloud API down

**Expected Behavior**:
```
[INFO] ✓ Tally is reachable
[INFO] Extracting ledgers...
[INFO] ✓ Extracted 150 ledgers
[ERROR] Failed to transmit: Connection refused
[ERROR] Transmission failed, retrying...
[INFO] SYNC CYCLE COMPLETE - Status: transmission_failed
```

**Verification**: ✅ Retries with exponential backoff

---

### Test 4: Successful Sync

**Setup**: All systems running, valid config

**Expected Behavior**:
```
============================================================
TALLY API SETUP
============================================================
✓ Tally API is responding
✓ Tally API is ready for extraction
============================================================

============================================================
SYNC CYCLE START
============================================================
✓ Tally is reachable
Extracting ledgers...
✓ Extracted 150 ledgers
Extracting vouchers...
✓ Extracted 500 vouchers
Transmitting 650 records...
✓ Transmitted 650 records
============================================================
SYNC CYCLE COMPLETE - Status: success
============================================================
```

**Verification**: ✅ Complete success with all metrics

---

## 📊 Logs & Debugging

### Log Locations

| Context | Path |
|---------|------|
| Standalone | `D:\tally-shayak\logs\tally_sync_service.log` |
| Service | `C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log` |
| Source Debug | `D:\tally-shayak\python agent/main.py` (console) |

### Log Levels

```
[DEBUG] - Detailed tracing (disabled by default)
[INFO] - Normal operation messages
[WARNING] - Non-fatal issues (e.g., Tally setup failed)
[ERROR] - Failures that prevent sync
[CRITICAL] - System failures
```

### Viewing Logs

```powershell
# Real-time tail
Get-Content logs\tally_sync_service.log -Wait

# Last 50 lines
Get-Content logs\tally_sync_service.log -Tail 50

# Search for errors
Get-Content logs\tally_sync_service.log | Select-String "ERROR"

# Search for warnings
Get-Content logs\tally_sync_service.log | Select-String "WARNING"
```

---

## 🔍 Troubleshooting

### Issue: "Missing required environment variables"

**Cause**: `.env.local` file not found or incomplete

**Solution**:
```powershell
# Create .env.local
$content = @"
TALLY_COMPANY_GUID=your-guid-here
CLOUD_API_KEY=your-key-here
TALLY_URL=http://localhost:9000
CLOUD_API_URL=http://15.206.90.21:8000
"@

# Save in working directory
Set-Content ".env.local" $content

# For service, save in installation directory
# C:\Program Files\Tally Sync Agent\.env.local
```

### Issue: "Tally unreachable"

**Cause**: Tally API Connector not running

**Solution**:
```powershell
# 1. Check if Tally is running
Get-Process | Where-Object { $_.Name -match "Tally" }

# 2. Check if port 9000 is listening
netstat -ano | findstr "9000"

# 3. Manually start connector
& "D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1"

# 4. Test connectivity
curl.exe http://localhost:9000/
```

### Issue: Service won't start

**Cause**: Configuration error or permission issue

**Solution**:
```powershell
# 1. Check service status
nssm status TallySyncAgent

# 2. View service logs
nssm query TallySyncAgent

# 3. Stop service
nssm stop TallySyncAgent

# 4. Check configuration file
Get-Content "C:\Program Files\Tally Sync Agent\.env.local"

# 5. Fix configuration if needed
Set-Content "C:\Program Files\Tally Sync Agent\.env.local" @"
TALLY_COMPANY_GUID=your-guid
CLOUD_API_KEY=your-key
"@

# 6. Start service again
nssm start TallySyncAgent

# 7. Check logs
Get-Content "C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log" -Tail 20
```

---

## ✨ Test Checklist

### Pre-Installation
- [ ] System Requirements Met (Windows 10+, Python 3.12)
- [ ] Dependencies installed (NSSM, Inno Setup if building installer)
- [ ] Tally is running and accessible
- [ ] Cloud API is running and accessible
- [ ] Configuration values obtained (Company GUID, API Key)

### Installation Testing
- [ ] Exe runs without errors (standalone)
- [ ] Configuration loaded correctly
- [ ] Service installs successfully
- [ ] Service starts without errors
- [ ] Logs created in correct location

### Functional Testing
- [ ] Tally API setup runs automatically
- [ ] Extraction works (ledgers + vouchers)
- [ ] Queue persists data locally
- [ ] Transmission sends to cloud
- [ ] Error handling works (graceful failures)

### Edge Cases
- [ ] Missing `.env.local` handled
- [ ] Tally unreachable handled
- [ ] Cloud API unreachable handled
- [ ] Partial data extraction handled
- [ ] Service restarts automatically on crash

### Performance
- [ ] Startup time < 60 seconds
- [ ] Extraction time proportional to data size
- [ ] Memory usage < 500 MB
- [ ] CPU usage minimal when idle

---

## 🚀 Test Execution Plan

### Phase 1: Standalone Testing (1 hour)
```
1. Create .env.local with test values
2. Run exe: dist\TallySyncAgent.exe
3. Check logs for success/failure
4. Test error cases (missing config, Tally down)
```

### Phase 2: Service Testing (1 hour)
```
1. Install service via install_service.bat
2. Configure .env.local
3. Start service
4. Wait for scheduled run (or force run)
5. Check logs and verify data sync
6. Stop and remove service
```

### Phase 3: Installer Testing (1 hour)
```
1. Build installer: iscc.exe TallySyncAgent.iss
2. Run installer on clean test VM
3. Follow installation flow
4. Configure after installation
5. Verify service starts and runs
6. Uninstall and verify cleanup
```

### Phase 4: Edge Case Testing (30 minutes)
```
1. No configuration file
2. Tally not running
3. Cloud API down
4. Partial data extraction
5. Network interruptions
```

---

## 📝 Success Criteria

| Aspect | Criteria | Status |
|--------|----------|--------|
| **Installation** | No errors, files in correct location | ⬜ |
| **Configuration** | Reads from .env.local correctly | ⬜ |
| **Headless** | No UI dialogs appear | ⬜ |
| **Startup** | Tally setup runs automatically | ⬜ |
| **Execution** | Extracts and transmits data | ⬜ |
| **Error Handling** | Graceful failures, clear logs | ⬜ |
| **Service** | Installs, starts, runs on schedule | ⬜ |
| **Logging** | All activities logged clearly | ⬜ |
| **Uninstall** | Clean removal, no leftover files | ⬜ |
| **Performance** | Fast startup, reasonable memory | ⬜ |

---

## 📖 Related Documentation

- [Tally Setup Integration](TALLY_SETUP_INTEGRATION_SUMMARY.md)
- [Deployment Checklist](docs/deployment/DEPLOYMENT_CHECKLIST.md)
- [AWS Deployment Guide](docs/deployment/AWS_DEPLOYMENT_STEPS.md)
- [Phase 4 Testing](docs/testing/phase4/guide.md)

---

## Summary

✅ **Agent is completely headless (no UI)**
✅ **Configuration via .env.local file**
✅ **Fully automated, requires no user interaction**
✅ **Detailed logging for troubleshooting**
✅ **Ready for production deployment**

The agent is designed for **unattended operation** as a Windows Service!

---

**Last Updated**: 28 June 2026
**Status**: Testing Guide Complete
**Next**: Execute test plan on clean Windows VM
