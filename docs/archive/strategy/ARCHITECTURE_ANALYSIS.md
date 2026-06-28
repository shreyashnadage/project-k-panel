# Tally Sync Agent - Architecture Analysis

**Date**: 28 June 2026  
**Focus**: Sync Mechanism & OTA Update Strategy

---

## 📡 QUESTION 1: HOW DOES THE CLIENT LISTEN & TRANSMIT DATA?

### Current Implementation

#### **Sync Flow (Push Model)**

```
┌──────────────────────────────────────────────────────────────┐
│ TALLY SYNC AGENT (Windows Service)                           │
└──────────────────────────────────────────────────────────────┘

TIME=0h
  ↓
WINDOWS SERVICE STARTS (NSSM)
  ├─ Service: TallySyncService
  ├─ Interval: 6 hours (configurable)
  ├─ Log: C:\logs\tally_sync_service.log
  └─ State: Running continuously
  
EVERY 6 HOURS:
  ↓
[1] EXTRACT FROM TALLY
  ├─ Connect: http://localhost:9000 (TDML API)
  ├─ Query: SELECT * FROM Ledgers WHERE modified_date >= watermark
  ├─ Query: SELECT * FROM Vouchers WHERE modified_date >= watermark
  ├─ Encoding: UTF-16 → UTF-8 conversion
  ├─ Result: {ledgers: 150, vouchers: 500}
  └─ Watermark: Advance to latest sync time
  
[2] ENQUEUE LOCALLY
  ├─ Store in SQLite: cloudplatform/db/local.db
  ├─ Table: pending_ledgers, pending_vouchers
  ├─ Queue depth tracked: 650 records
  └─ Purpose: Local retry buffer if cloud fails
  
[3] TRANSMIT TO CLOUD
  ├─ Endpoint: POST http://15.206.90.21:8000/v1/sync-with-client
  ├─ Headers:
  │  ├─ x-api-key: secret_token
  │  ├─ x-client-id: cli_abc123
  │  ├─ x-device-id: dev_xyz789
  │  └─ Content-Type: application/json
  ├─ Payload:
  │  ├─ client_id: cli_abc123
  │  ├─ device_id: dev_xyz789
  │  ├─ extracted_ledgers: 150
  │  ├─ extracted_vouchers: 500
  │  └─ raw_data: {...JSON...}
  └─ Retry Logic: Exponential backoff (1s, 2s, 4s, 8s, 16s)
  
[4] MARK SENT
  ├─ Update SQLite queue: status = "sent"
  ├─ Log: sync_audit_log
  └─ Track: transmission timestamp
  
[5] REPORT HEARTBEAT
  ├─ Send: POST /v1/heartbeat
  ├─ Data: {agent_version, last_sync, queue_depth, errors}
  └─ Interval: With each sync or separately every 1h
  
REPEAT: After 6 hours
```

### Key Architecture Details

#### **1. Service Management (Windows Service)**

**File**: `agent/service/windows_service.py`

```python
class TallySyncService:
    def __init__(self, sync_interval_hours: int = 6):
        self.sync_interval_seconds = sync_interval_hours * 3600
        self.shutdown_event = threading.Event()
        self.next_sync_time = None
    
    def run(self):
        """Main service loop - runs sync cycles on schedule."""
        self.running = True
        while self.running:
            now = datetime.now()
            if now >= self.next_sync_time:
                self.orchestrator.run_once()
                self.next_sync_time = now + timedelta(
                    seconds=self.sync_interval_seconds
                )
            time.sleep(60)  # Check every 60 seconds
```

**Installation**: 
```bash
nssm install TallySyncAgent python -m agent.service.windows_service
nssm start TallySyncAgent
nssm stop TallySyncAgent
```

**Logging**:
- File: `C:\logs\tally_sync_service.log`
- Rotation: 10 MB per file, 5 backups
- Format: `YYYY-MM-DD HH:MM:SS - Service - Level - Message`

#### **2. Main Orchestrator (Sync Coordination)**

**File**: `agent/orchestrator.py`

```python
class SyncOrchestrator:
    def run_once(self) -> Dict:
        """Execute one complete sync cycle."""
        
        # Step 1: Extract from Tally
        ledgers = self.tally_client.get_ledgers()
        vouchers = self.tally_client.get_vouchers()
        
        # Step 2: Enqueue locally
        for ledger in ledgers:
            self.queue.enqueue_ledger(ledger)
        for voucher in vouchers:
            self.queue.enqueue_voucher(voucher)
        
        # Step 3: Transmit queued records
        transmitted = self._transmit_queued()
        
        # Step 4: Mark sent
        self.queue.mark_sent_batch()
        
        # Step 5: Advance watermark
        self.watermark.set(datetime.utcnow())
        
        return {
            "extracted": len(ledgers) + len(vouchers),
            "transmitted": transmitted,
            "status": "success"
        }
```

#### **3. Data Transmission (Client Libraries)**

**File**: `agent/transmitter/client.py`

```python
class TransmitterClient:
    def __init__(self, base_url, api_key, client_id=None, device_id=None):
        self.base_url = base_url
        self.api_key = api_key
        self.client_id = client_id
        self.device_id = device_id
    
    def send_sync(self, ledgers, vouchers):
        """Send sync data to platform."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
            "x-client-id": self.client_id,  # ← Client tagging
            "x-device-id": self.device_id,  # ← Device tagging
            "Content-Type": "application/json"
        }
        
        payload = {
            "client_id": self.client_id,
            "device_id": self.device_id,
            "extracted_ledgers": len(ledgers),
            "extracted_vouchers": len(vouchers),
            "raw_data": {...}
        }
        
        response = requests.post(
            f"{self.base_url}/v1/sync-with-client",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise TransmitterError(response.text)
```

#### **4. Local Queue (Retry Buffer)**

**File**: `agent/queue/manager.py`

```python
class QueueManager:
    """
    Local SQLite queue for:
    - Buffering failed transmissions
    - Implementing exponential backoff
    - Tracking transmission status
    """
    
    def enqueue_ledger(self, ledger: Dict):
        """Queue a ledger for transmission."""
        self.db.execute("""
            INSERT INTO pending_ledgers (...)
            VALUES (...)
        """)
    
    def get_pending(self, limit=1000):
        """Get records pending transmission."""
        return self.db.query("""
            SELECT * FROM pending_ledgers
            WHERE status = 'pending'
            LIMIT ?
        """, (limit,))
    
    def mark_sent(self, record_id: str):
        """Mark record as successfully sent."""
        self.db.execute("""
            UPDATE pending_ledgers
            SET status = 'sent', sent_at = NOW()
            WHERE id = ?
        """, (record_id,))
```

### Summary: Sync Mechanism

```
┌─────────────────────────────────────────────────────────┐
│ PUSH MODEL (Not Pull/Listen)                            │
└─────────────────────────────────────────────────────────┘

Agent INITIATES sync every 6 hours:
✓ Extract from Tally (fetch latest changes)
✓ Queue locally (for resilience)
✓ Push to cloud API
✓ Receive acknowledgment
✓ Advance watermark
✓ Report heartbeat

Platform does NOT push signals to agent.
Agent does NOT listen for webhooks/signals.

Why PUSH model?
- Agent behind corporate firewall (inbound blocked)
- No static IP (dynamic/DHCP)
- Simple stateless API (no connection management)
- Proven reliability (email, batch jobs)
```

---

## 🔄 QUESTION 2: OTA UPDATES & DELIVERY PIPELINE

### Current Implementation Status

**What EXISTS**:
- ✅ `agent/updater/__init__.py` (stub, 24 bytes)
- ✅ `installer/wizard/` (installer directory)
- ✅ Agent versioning in `agent/service/windows_service.py`

**What's MISSING**:
- ❌ OTA update logic (not implemented)
- ❌ Version check endpoint
- ❌ Download/patch mechanism
- ❌ Delta updates
- ❌ Rollback strategy
- ❌ Delivery pipeline (CI/CD)

---

## 🏢 ENTERPRISE-GRADE OTA SOLUTIONS (Research)

### Option 1: **Squirrel (Electron/Desktop Focus)** ⭐ RECOMMENDED FOR YOU

**GitHub**: https://github.com/Squirrel/Squirrel.Windows  
**Language**: C# / .NET (best for Windows)  
**Enterprise Grade**: Yes  
**Used By**: Slack, GitHub Desktop, many Fortune 500 companies

**Pros**:
- ✅ Native Windows support
- ✅ Delta/patch updates (small bandwidth)
- ✅ Automatic rollback on failure
- ✅ Background updates (transparent to user)
- ✅ Code signing verification
- ✅ Schedule updates (e.g., 2 AM)
- ✅ Self-contained (no external dependencies)

**Cons**:
- ❌ Originally for Electron (but .NET version exists)
- ❌ No cloud provider UI (you manage releases)

**How It Works**:
```
Agent checks for updates every 24h:
  ↓
GET https://api.github.com/repos/yourrepo/releases/latest
  ↓
Compare versions:
  - Remote: v0.5.0
  - Local: v0.4.0
  ↓
If newer available:
  ├─ Download delta patch (smaller)
  ├─ Verify signature (EV code signing cert)
  ├─ Apply patch atomically
  ├─ Test new version
  ├─ If fails → rollback to previous
  └─ Notify user on next restart

Next startup:
  └─ Run new version v0.5.0
```

**Cost**: Free, open source

---

### Option 2: **AppCenter (Microsoft)**

**Website**: https://appcenter.ms  
**Enterprise Grade**: Yes (Microsoft)  
**Used By**: Millions of enterprise apps

**Pros**:
- ✅ Built-in analytics
- ✅ Crash reporting
- ✅ A/B testing
- ✅ Staged rollouts (1% → 10% → 100%)
- ✅ Rollback capability
- ✅ Deep Azure integration
- ✅ Enterprise SLA

**Cons**:
- ❌ Requires Microsoft account ecosystem
- ❌ Proprietary platform lock-in
- ❌ Costs: $0-1000+/month depending on scale
- ❌ Overkill for standalone Windows app

**Cost**: Freemium ($0-1000+/month)

---

### Option 3: **Winget Package Manager** (New)

**GitHub**: https://github.com/microsoft/winget-cli  
**Enterprise Grade**: Emerging (Microsoft)  
**Used By**: Enterprise IT departments

**Pros**:
- ✅ Microsoft-backed (future-proof)
- ✅ IT admin friendly
- ✅ Centralized management (WSUS-like)
- ✅ Silent updates possible
- ✅ Integrates with Windows management

**Cons**:
- ❌ Requires Windows 10+ (not legacy)
- ❌ Limited fine control over update timing
- ❌ Community-based package submission
- ❌ Not ideal for proprietary apps

**Cost**: Free

---

### Option 4: **InstallShield / Advanced Installer** (Legacy)

**Website**: https://www.advancedinstaller.com  
**Enterprise Grade**: Yes (30+ years)

**Pros**:
- ✅ Mature, battle-tested
- ✅ GUI-based (no coding needed)
- ✅ White-label capable
- ✅ Update chaining (v1→v2→v3)

**Cons**:
- ❌ Expensive ($1500-5000/year)
- ❌ Requires rebuilding for each update
- ❌ No delta updates (full downloads)
- ❌ Less suitable for frequent updates

**Cost**: $1500-5000/year

---

### Option 5: **Omaha (Google's OTA Framework)**

**GitHub**: https://github.com/google/omaha  
**Enterprise Grade**: Yes (Used by Google/Chromium)  
**Used By**: Google Chrome, Chromium, many enterprise apps

**Pros**:
- ✅ Battle-tested (billions of installations)
- ✅ Delta updates (Google refined)
- ✅ Flexible scheduling
- ✅ Telemetry & reporting
- ✅ Multi-app support
- ✅ Free and open source

**Cons**:
- ❌ C++ codebase (complex)
- ❌ Requires custom integration
- ❌ Steeper learning curve
- ❌ No UI out-of-box

**Cost**: Free, open source

---

## 🎯 RECOMMENDATION FOR TALLY SYNC AGENT

### **Phase Strategy**

#### **Phase 4-5 (NOW → 8 weeks)**: Squirrel.Windows
```
Why Squirrel?
✅ Perfect fit for Windows desktop app
✅ Free & open source
✅ Proven in production (Slack, GitHub)
✅ Delta updates (efficient)
✅ Automatic rollback
✅ No external dependencies
✅ Can use GitHub Releases (free)
```

**Implementation Timeline**:
- Week 1: Integrate Squirrel into agent
- Week 2: Set up GitHub Releases pipeline
- Week 3: Test delta updates
- Week 4: Code signing + verification

#### **Phase 6+ (3+ months)**: AppCenter or Custom
```
Why later?
- Squirrel is sufficient for MVP
- AppCenter adds complexity (multi-client)
- Worth revisiting when user base grows
- Custom solution may be better for compliance
```

---

## 🚀 PROPOSED OTA ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│ DELIVERY PIPELINE (GitHuब → Windows → Agent)            │
└─────────────────────────────────────────────────────────┘

1. DEVELOPER COMMITS
   ├─ git push to main
   └─ GitHub Actions triggered
   
2. CI/CD PIPELINE
   ├─ Compile: Python → PyInstaller exe
   ├─ Test: Run test suite
   ├─ Sign: EV Code Signing certificate
   └─ Package: .exe + manifest
   
3. RELEASE MANAGEMENT
   ├─ GitHub Release created (v0.5.0)
   ├─ Artifacts:
   │  ├─ TallySyncAgent-0.5.0.exe (full)
   │  ├─ TallySyncAgent-0.5.0.delta (patch)
   │  └─ RELEASES file (manifest)
   └─ S3/CDN cached for speed
   
4. AGENT UPDATE CHECK
   ├─ Every 24h: GET /api/releases/latest
   ├─ Response: {version: "0.5.0", url: "...", delta: "..."}
   ├─ Compare: local (0.4.0) vs remote (0.5.0)
   ├─ Decide: Update needed?
   └─ Download: Delta patch (~5-50MB vs 100MB full)
   
5. UPDATE APPLICATION
   ├─ Verify: Signature check (EV cert)
   ├─ Test: Dry run in temp directory
   ├─ Apply: Atomic swap (old → backup, new → active)
   ├─ Verify: Launch new binary
   ├─ Rollback: If test fails → restore backup
   └─ Cleanup: Remove old version
   
6. AGENT RESTART
   ├─ Schedule: Next sync cycle or next day (2 AM)
   ├─ Restart: Windows Service restart
   ├─ New Version: v0.5.0 now active
   └─ Telemetry: Report success to platform

7. MONITORING
   ├─ Dashboard: See which agents on which versions
   ├─ Alerting: Notify if update fails repeatedly
   ├─ Rollback: Force previous version if needed
   └─ Analytics: Track adoption % over time
```

---

## 📋 IMPLEMENTATION ROADMAP

### **PHASE 4B (Week 1-2): Squirrel Integration**

**Step 1: Add Squirrel to dependencies**
```toml
[project.optional-dependencies]
agent = [
    "squirrel>=1.0.0",
    ...
]
```

**Step 2: Create UpdateManager**
```python
# agent/updater/manager.py
class UpdateManager:
    def __init__(self, api_url, current_version):
        self.api_url = api_url
        self.current_version = current_version
    
    def check_for_updates(self):
        """Check GitHub Releases for newer version."""
        response = requests.get(
            f"{self.api_url}/repos/YOUR_ORG/tally-sync-agent/releases/latest"
        )
        latest = response.json()
        
        if parse_version(latest["tag_name"]) > parse_version(self.current_version):
            return {
                "available": True,
                "version": latest["tag_name"],
                "download_url": latest["assets"][0]["browser_download_url"],
                "release_notes": latest["body"]
            }
        return {"available": False}
    
    def download_and_apply(self, update_info):
        """Download update and apply it."""
        # Squirrel handles atomic updates
        squirrel.update(
            url=update_info["download_url"],
            verify_signature=True
        )
```

**Step 3: Integrate into service**
```python
# agent/service/windows_service.py
class TallySyncService:
    def run(self):
        self.update_manager = UpdateManager(
            api_url="https://api.github.com",
            current_version=self.orchestrator.version
        )
        
        while self.running:
            # Check for updates once per day
            if should_check_for_update():
                update_info = self.update_manager.check_for_updates()
                if update_info["available"]:
                    logger.info(f"Update available: {update_info['version']}")
                    self.update_manager.download_and_apply(update_info)
                    # Schedule restart (graceful shutdown)
                    self.schedule_restart(delay_hours=6)
            
            # Normal sync cycle
            self.orchestrator.run_once()
            self.sleep_until_next_sync()
```

### **PHASE 4C (Week 3-4): GitHub Actions Pipeline**

**File**: `.github/workflows/build-and-release.yml`

```yaml
name: Build & Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e ".[agent]"
          pip install pyinstaller
      
      - name: Build exe
        run: |
          pyinstaller --onefile \
            --add-data "config:config" \
            agent/main.py
      
      - name: Sign executable
        run: |
          # Use EV Code Signing certificate
          signtool sign /f cert.pfx /p ${{ secrets.CODE_SIGNING_PASSWORD }} \
            dist/TallySyncAgent.exe
      
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/TallySyncAgent.exe
          body_path: RELEASE_NOTES.md
```

---

## 📊 COMPARISON TABLE

| Feature | Squirrel | AppCenter | Omaha | WinGet | Advanced Installer |
|---------|----------|-----------|-------|--------|-------------------|
| **Windows Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Delta Updates** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Limited | ⭐ |
| **Rollback** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Ease of Use** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | Free | $0-1k/mo | Free | Free | $1.5-5k/yr |
| **Learning Curve** | Easy | Easy | Hard | Medium | Medium |
| **Production Ready** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠ New | ✅ Yes |
| **For Your Use Case** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 🎯 FINAL RECOMMENDATION

### **Use Squirrel.Windows for OTA Updates**

**Why**:
1. ✅ Perfect Windows fit
2. ✅ Free & open source
3. ✅ Proven enterprise use (Slack, GitHub Desktop)
4. ✅ Small download sizes (delta)
5. ✅ Automatic rollback
6. ✅ Can leverage GitHub Releases (free)
7. ✅ No vendor lock-in
8. ✅ EV code signing support

**Implementation Cost**: 1-2 weeks engineering time

**Production Timeline**: Ready for Phase 5 (Week 8-10)

---

## 📝 ACTION ITEMS

- [ ] Create `agent/updater/manager.py` with UpdateManager class
- [ ] Add Squirrel to `pyproject.toml` dependencies
- [ ] Set up GitHub Actions for automated builds
- [ ] Obtain EV Code Signing certificate (DigiCert or GlobalSign)
- [ ] Test update flow: v0.4.0 → v0.5.0 (with rollback)
- [ ] Document update process for end users
- [ ] Create dashboard to monitor agent versions
- [ ] Set up staged rollouts (1% → 10% → 100%)

---

**Status**: OTA strategy defined. Ready to implement in Phase 4C.

