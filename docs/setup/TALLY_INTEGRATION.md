# 🔗 Tally API Connector Integration

## Overview

The Tally Sync Agent now automatically ensures the Tally API Connector is running before each extraction cycle. This eliminates the need for manual setup and ensures the Tally HTTP API (port 9000) is always available.

---

## How It Works

### Startup Flow

```
TallySyncAgent.exe starts
    ↓
main.py runs
    ↓
ensure_tally_ready()  ← NEW: Starts TallyAPIConnector if needed
    ↓
orchestrator.main()
    ↓
Extract from Tally → Queue → Transmit to Cloud
```

### Service Flow (Windows Service)

```
NSSM Service starts TallySyncService
    ↓
Waits for sync interval (default 6 hours)
    ↓
_run_sync_cycle() runs
    ↓
ensure_tally_ready()  ← NEW: Starts TallyAPIConnector before sync
    ↓
SyncOrchestrator extracts from Tally
    ↓
Data transmitted to cloud
    ↓
Wait for next interval, repeat
```

---

## Configuration

### Default Paths

The agent looks for the Tally setup in these default locations:

```
TallyAPIConnector Exe:
  D:\Downloads\integration-setup\integration-setup\TallyAPIConnectorV1.0.exe

PowerShell Setup Script:
  D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1
```

### Customizing Paths

If your Tally setup is in a different location, you have two options:

#### Option 1: Create Symlinks (Recommended)
```powershell
# Run as Administrator

# Create directory if it doesn't exist
New-Item -ItemType Directory -Path "D:\Downloads\integration-setup\integration-setup" -Force

# Create symlinks to your actual Tally files
New-Item -ItemType SymbolicLink -Path "D:\Downloads\integration-setup\integration-setup\TallyAPIConnectorV1.0.exe" `
  -Target "C:\YourActualPath\TallyAPIConnectorV1.0.exe"

New-Item -ItemType SymbolicLink -Path "D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1" `
  -Target "C:\YourActualPath\RunWithoutBrowser.ps1"
```

#### Option 2: Modify Code (Advanced)
Edit `agent/setup/tally_setup.py` and change:

```python
DEFAULT_CONNECTOR_PATH = r"YOUR\ACTUAL\PATH\TallyAPIConnectorV1.0.exe"
DEFAULT_SETUP_SCRIPT = r"YOUR\ACTUAL\PATH\RunWithoutBrowser.ps1"
```

#### Option 3: Environment Variables (Planned)
Will be added in future version:
```bash
TALLY_CONNECTOR_PATH=C:\YourPath\TallyAPIConnectorV1.0.exe
TALLY_SETUP_SCRIPT=C:\YourPath\RunWithoutBrowser.ps1
```

---

## Startup Behavior

### When Running TallySyncAgent.exe

1. **Startup Check**
   - Verifies Tally setup files exist
   - Logs configuration paths

2. **PowerShell Script Execution** (Preferred)
   - Runs `RunWithoutBrowser.ps1`
   - Script monitors and kills any browser windows
   - Keeps TallyAPIConnector running in background

3. **Fallback: Direct Exe Execution**
   - If PowerShell script fails, runs exe directly
   - Less clean process management but still works

4. **Health Check**
   - Polls `http://localhost:9000/` for responsiveness
   - Waits up to 30 seconds for API to respond
   - Reports success/failure

5. **Sync Starts**
   - Once Tally API is verified, extraction begins
   - Queues data locally
   - Transmits to cloud

### Error Handling

If Tally setup fails:
- **Non-blocking**: Agent continues with sync attempt
- **Logging**: Detailed error messages in logs
- **Recovery**: Next sync cycle tries again

This allows graceful degradation — if Tally is already running, setup can be skipped.

---

## Troubleshooting

### Issue: "Tally setup script not found"

**Cause**: PowerShell script not at default location

**Solution**:
1. Check if script exists: `Test-Path "D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1"`
2. If missing, create symlink (Option 1 above) or modify paths (Option 2)
3. Re-run agent

### Issue: "Tally API Connector process started but API not responding"

**Cause**: Exe runs but API doesn't start properly

**Diagnosis**:
```powershell
# Check if exe is running
Get-Process | Where-Object { $_.Name -match "Tally" }

# Manually test the setup script
& "D:\Downloads\integration-setup\integration-setup\RunWithoutBrowser.ps1"

# Test API connectivity
curl.exe http://localhost:9000/
```

**Solution**:
1. Ensure TallyPrime is open and accessible
2. Check Windows Firewall allows localhost:9000
3. Verify exe file is not corrupted
4. Try running exe manually and checking for error dialogs

### Issue: "PowerShell execution policy denied"

**Cause**: PowerShell doesn't allow running scripts

**Solution**:
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser

# Or run agent as Administrator
```

### Issue: Health check times out after 30 seconds

**Cause**: Tally API is slow to start or unreachable

**Check**:
1. Is TallyPrime running? `tasklist | findstr "TallyPrime"`
2. Is port 9000 listening? `netstat -ano | findstr "9000"`
3. Windows Firewall blocking? Check Windows Defender Firewall
4. Antivirus quarantining exe? Check antivirus logs

**Increase timeout** (in `agent/setup/tally_setup.py`):
```python
HEALTH_CHECK_TIMEOUT = 60  # seconds (was 30)
```

---

## Architecture

### Module: `agent/setup/tally_setup.py`

**Main Class**: `TallySetup`

**Key Methods**:
- `start_via_powershell()` — Runs setup via PowerShell script
- `start_direct()` — Runs exe directly
- `verify_connectivity()` — Health checks API on port 9000
- `ensure_running()` — Main entry point (tries both methods)
- `stop()` — Cleanup when agent exits

**Global Function**: `ensure_tally_ready()`
- Called from `main.py` and Windows service
- Returns True if Tally is ready, False if failed

### Integration Points

1. **agent/main.py** (Standalone exe)
   ```python
   if not ensure_tally_ready():
       logger.warning("Tally API setup failed, proceeding anyway...")
   orchestrator_main()
   ```

2. **agent/service/windows_service.py** (Windows Service)
   ```python
   def _run_sync_cycle(self):
       if not ensure_tally_ready():
           logger.warning("Tally API setup failed, but proceeding...")
       # Run orchestrator
   ```

---

## Logs

### Where to Find Logs

**Standalone Exe**:
```
D:\tally-shayak\logs\tally_sync_service.log
```

**Windows Service**:
```
C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log
```

### What to Look For

**Successful Setup**:
```
[INFO] Tally API is responding (HTTP 200)
[INFO] ✓ Tally API is ready for extraction
```

**Failed Setup**:
```
[WARNING] Tally API not responding after 30s
[ERROR] Failed to start Tally API Connector
[ERROR]   Checked paths:
[ERROR]     - Script: D:\Downloads\...
[ERROR]     - Exe: D:\Downloads\...
```

---

## Testing

### Manual Test (Standalone)

```powershell
cd D:\tally-shayak

# Run agent (will start Tally setup automatically)
python agent/main.py

# Check logs
Get-Content logs/tally_sync_service.log -Tail 50
```

### Manual Test (Service)

```powershell
# Start service
nssm start TallySyncAgent

# Check status
nssm status TallySyncAgent

# View logs
Get-Content "C:\Program Files\Tally Sync Agent\logs\tally_sync_service.log" -Tail 50
```

### API Health Check

```powershell
# Test Tally API directly
curl.exe http://localhost:9000/

# Expected: Some response (shows Tally is listening)
```

---

## Security Notes

### Process Management
- **PowerShell script monitors browser processes** — kills any launched by exe
- **Separate process group** — Allows clean shutdown
- **Error handling** — Doesn't crash if setup fails

### File Permissions
- Agent runs as **SYSTEM** (Windows Service) or **Current User** (Standalone)
- PowerShell script requires **Execution Policy** (bypassed via parameters)
- No elevated privileges needed for normal operation

### Network
- Only communicates with **localhost:9000** (Tally API)
- No internet access needed for Tally setup
- Cloud transmission uses standard HTTPS

---

## Future Enhancements

### Planned
- [ ] Support for custom paths via environment variables
- [ ] Configurable health check timeout
- [ ] Automatic restart if Tally connection drops
- [ ] Metrics/monitoring for Tally availability
- [ ] Support for alternate Tally setup methods

### Possible
- [ ] WebSocket health monitoring (real-time status)
- [ ] Dashboard widget for Tally connectivity
- [ ] Alerting if Tally is unavailable

---

## FAQ

**Q: Does this slow down startup?**
A: No significant slowdown. Health check (30s max) only happens once at startup.

**Q: What if TallyPrime is already running?**
A: Setup runs anyway but Tally API is already available, so it connects immediately.

**Q: Can I disable Tally setup?**
A: Not currently, but could be added as config option. For now, setup is always attempted.

**Q: Does setup require admin privileges?**
A: No, but running as Administrator is recommended for Windows Service.

**Q: What if Tally goes offline during a sync?**
A: Agent continues with existing connection. Next sync cycle tries to restart Tally.

---

## Summary

✅ **Tally API Connector now starts automatically**
✅ **Before every sync cycle (standalone or service)**
✅ **Graceful error handling (non-blocking)**
✅ **Health checks verify connectivity**
✅ **Configurable paths (multiple options)**
✅ **Detailed logging for troubleshooting**

The agent is now fully autonomous and handles Tally setup without user intervention! 🎯

---

**Last Updated**: 28 June 2026
**Status**: Implementation Complete
**Version**: 0.4.0+
