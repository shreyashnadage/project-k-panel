# 📦 Artifacts & Build Outputs

This folder contains build outputs, test data, and ephemeral artifacts generated during development and testing.

---

## 📁 Organization

```
artifacts/
├── phase1/              # Phase 1 artifacts
│   ├── extraction_output.json    # Sample extracted data
│   └── sync_state.json           # Watermark state
│
├── phase2/              # Phase 2 artifacts
│   ├── tally_sync_test.db        # Test database
│   └── api_responses/            # Captured API responses
│
├── phase3/              # Phase 3 artifacts
│   ├── agent_queue.db            # Local queue state
│   ├── orchestrator_logs.txt      # Sync logs
│   └── extraction_outputs/       # Multiple extractions
│
├── backups/             # Backup data
│   ├── database_backups/
│   └── queue_snapshots/
│
└── README.md           # This file
```

---

## 📄 Artifact Types

### Phase 1: Extraction Artifacts

**`extraction_output.json`**
- Sample output from `run_extraction_json.py`
- Contains extracted ledgers and vouchers
- Used for validation against Tally

**`sync_state.json`**
- Watermark state (last synced dates)
- Format: `{company_guid: {entity_type: last_date}}`
- Used by watermark manager for incremental sync

### Phase 2: API Artifacts

**`tally_sync_test.db`**
- SQLite test database for Phase 2 testing
- Contains: tenants, ledgers, vouchers, audit logs
- Reset between test runs

**`api_responses/`**
- Captured JSON responses from cloud API
- Used for integration test fixtures
- Format: `{endpoint}_{scenario}.json`

### Phase 3: Pipeline Artifacts

**`agent_queue.db`**
- Local queue database (SQLite)
- Contains pending/sent/failed records
- Persists across agent restarts

**`orchestrator_logs.txt`**
- Detailed sync cycle logs
- Timestamps, extraction counts, transmission status
- Used for debugging and validation

**`extraction_outputs/`**
- Multiple extraction results (one per sync)
- Timestamped: `extraction_2026-06-27_14-32-01.json`
- Archival and trend analysis

---

## 🔄 Artifact Lifecycle

### Creation
Artifacts are **automatically generated** during:
- Test execution (`phase0_verify.py`, pytest)
- Manual testing (extraction scripts, manual curl tests)
- Development (orchestrator runs, queue inspection)

### Usage
Artifacts are used for:
- **Validation**: Compare extracted data to Tally
- **Debugging**: Inspect queue states, logs
- **Testing**: Fixtures for unit/integration tests
- **Auditing**: Track what was extracted/transmitted

### Cleanup
Artifacts should be:
- **Deleted** between test runs (to avoid stale data)
- **Archived** before major updates (for recovery)
- **Backed up** before production deployment

---

## 📋 Common Artifacts & When They Appear

| Artifact | Created By | When | Size | Keep? |
|----------|-----------|------|------|-------|
| `extraction_output.json` | `run_extraction_json.py` | Manual test | 1-10 MB | Temporary |
| `sync_state.json` | Watermark manager | Every extraction | <1 KB | Permanent* |
| `tally_sync_test.db` | Phase 2 test | pytest phase2 | 1-5 MB | Temporary |
| `agent_queue.db` | Agent runtime | Continuous | 1-50 MB | Permanent |
| `orchestrator_logs.txt` | Orchestrator | Every run | 100 KB | 30 days |

\* Keep current watermark state; archive old ones

---

## 🗑️ Cleaning Up Artifacts

### Before Testing
```bash
# Remove test databases
rm artifacts/phase2/tally_sync_test.db
rm artifacts/phase3/agent_queue.db

# Remove old logs
rm artifacts/phase3/orchestrator_logs.txt

# Keep extraction state for reference
# (watermarks help with next extraction)
```

### Archive Old Artifacts
```bash
# Back up before major changes
tar -czf artifacts/backups/extraction_2026-06-27.tar.gz \
  artifacts/phase1/extraction_output.json \
  artifacts/phase1/sync_state.json
```

---

## 💾 Backup Strategy

### Before Production Deployment
1. **Backup current queue state**:
   ```bash
   cp artifacts/phase3/agent_queue.db \
      artifacts/backups/agent_queue_pre_phase4.db
   ```

2. **Backup cloud database**:
   ```bash
   pg_dump tally_sync_prod > \
      artifacts/backups/db_pre_phase4.sql
   ```

3. **Archive extraction logs**:
   ```bash
   tar -czf artifacts/backups/orchestrator_logs_2026.tar.gz \
      artifacts/phase3/orchestrator_logs.txt
   ```

### In Case of Emergency
```bash
# Restore from backup
cp artifacts/backups/agent_queue_pre_phase4.db \
   artifacts/phase3/agent_queue.db

# Restore database
psql tally_sync_prod < artifacts/backups/db_pre_phase4.sql
```

---

## 📊 Artifact Storage Guidelines

### Keep ✅
- Current `sync_state.json` (needed for next extraction)
- `agent_queue.db` with pending records (data loss risk)
- Monthly archive of `orchestrator_logs.txt`
- Weekly backup of cloud database

### Delete ❌
- Test databases (`tally_sync_test.db`)
- Old extraction outputs (>30 days, archived)
- Debug logs (>7 days old)
- Temporary API response captures

### Archive 📦
- Monthly extraction outputs (for trend analysis)
- Monthly orchestrator logs
- Before major version upgrades
- Before production deployments

---

## 📍 Important Paths

| Purpose | Location | Notes |
|---------|----------|-------|
| Current extraction | `artifacts/phase1/extraction_output.json` | Latest test result |
| Watermark state | `artifacts/phase1/sync_state.json` | **DO NOT DELETE** |
| Local queue | `artifacts/phase3/agent_queue.db` | **DO NOT DELETE** |
| Sync logs | `artifacts/phase3/orchestrator_logs.txt` | Archive monthly |
| Backups | `artifacts/backups/` | Keep 3 month rolling window |

---

## 🔐 Security Notes

⚠️ **These artifacts may contain sensitive data:**
- Database files contain actual Tally/customer data
- Extraction outputs may include customer names, amounts
- Queue states may contain financial records

**Store securely**:
- Encrypt backups before storing externally
- Use `.gitignore` to prevent accidental commits
- Restrict access to artifacts folder
- Audit logs for unauthorized access

---

## 📝 Artifact Metadata

When saving artifacts, include metadata:

```json
{
  "artifact_type": "extraction_output",
  "timestamp": "2026-06-27T14:32:01Z",
  "phase": 1,
  "source": "run_extraction_json.py",
  "company": "Bhrama Enterprises",
  "records": {
    "ledgers": 10,
    "vouchers": 50
  },
  "status": "success"
}
```

This helps with:
- Tracking what was extracted when
- Understanding data freshness
- Debugging issues with specific runs

---

## 🎯 Best Practices

1. **Tag artifacts with phase & date**:
   ```
   extraction_phase1_2026-06-27.json
   agent_queue_phase3_backup_2026-06-27.db
   ```

2. **Keep extraction state**:
   - Watermark (`sync_state.json`) must be preserved
   - Without it, next extraction starts from scratch

3. **Archive before major updates**:
   - Back up queue before Phase 4 service installation
   - Back up database before OTA update (Phase 5)

4. **Don't commit to git**:
   Add to `.gitignore`:
   ```
   artifacts/phase*/*.db
   artifacts/phase*/*.json
   artifacts/backups/
   ```

---

**Last Updated**: 27 June 2026  
**Current Phase**: 3 (End-to-End Pipeline)  
**Next Review**: After Phase 4 (Windows Service)
