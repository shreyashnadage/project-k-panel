# Tally Sync Agent — Phase-by-Phase Implementation & Testing Plan
**Version**: 1.0  
**Date**: 26 June 2026  
**Audience**: Founding Engineer / Product Owner  

---

## How to Read This Document

Each phase has four sections:
1. **Build** — what to implement and in what order
2. **Test Locally** — tests you run on your own machine before declaring the phase done
3. **Test Suite** — automated tests that validate a deployed environment (runs against any environment: dev, staging, or customer machine)
4. **Phase Gate** — a checklist you must pass before starting the next phase

> If a phase gate item is not green, do not proceed. Skipping gates is the #1 cause of compounding bugs that are expensive to fix in later phases.

---

## Time-to-Market Strategy

The fastest path is a two-track approach:

| Track | Milestone | Estimated Time | What It Unlocks |
|---|---|---|---|
| **Pilot-ready** | Data flowing from Tally → cloud dashboard. Manual install. You assist each customer. | **~3 weeks** | First paying customer. Real data. Real feedback. |
| **Scale-ready** | Signed installer, self-service install, OTA updates, fleet monitoring. | **~7 weeks** | 50–100 customers without 1:1 hand-holding. |
| **Full product** | Analytics engine, working capital dashboard, WhatsApp alerts. | **~10–11 weeks** | Retention-driving value. Loan routing pipeline ready. |

The key insight: **you do not need a polished installer to onboard your first 10 customers.** You need working data. Build the pipeline first (Phases 0–3), then build the packaging (Phases 4–5), then build the analytics layer (Phase 6). This is not a quality compromise — it is sequencing correctly.

---

## Phase Gates Summary

| Phase | Gate | Must Pass |
|---|---|---|
| 0 → 1 | Environment verified | `phase0_verify.py` returns all ✓ |
| 1 → 2 | Extraction validated | Unit tests + manual extraction match Tally record count |
| 2 → 3 | API idempotent | Same POST twice → 0 new, 1 duplicate |
| 3 → 4 | Pipeline resilient | Offline test + crash recovery test pass |
| **3 → Pilot** | **Data flowing** | **Cloud DB has customer vouchers; watermark advances** |
| 4 → 5 | Service reliable | Clean VM install; service auto-starts; NSSM restart works |
| 5 → 6 | OTA working | v1.0 → v1.1 applies silently; hash validation works |

---

## Phase 0: Development Environment Setup

**Duration**: 2–3 days  
**Goal**: Every tool you need is installed and verified before writing a single line of production code. This phase is boring and critical.

### 0.1 What to Set Up

#### Your Development Machine (Windows 11 recommended — you are building for Windows)
```
Windows 11 (your primary dev machine)
├── Python 3.11.x (from python.org, NOT Microsoft Store — PyInstaller has issues with Store version)
├── Git + GitHub CLI
├── VS Code with Python extension
├── TallyPrime 3.x — install a licensed or educational copy
│     └── Activate HTTP server (Tally.ini → [HTTP] → Enabled=Yes; Port=9000)
├── DB Browser for SQLite (to inspect local SQLite files during dev)
├── Wireshark (to verify TLS encryption in Phase 3)
├── Inno Setup 6 (https://jrsoftware.org/isinfo.php) — for Phase 4
└── NSSM (https://nssm.cc) — download, put on PATH — for Phase 4
```

**Why Windows as your primary dev machine**: PyInstaller, NSSM, and Inno Setup are Windows-only. If you develop on Mac/Linux and cross-compile, you will spend days fighting build issues. Use Windows from the start.

#### Virtual Machines (Set These Up Now — You Will Need Them in Phase 4)
Use VirtualBox (free) or Windows Sandbox:
```
VM-1: Windows 10 (1909) — Clean, no Tally, no Python
      Purpose: Test installer on a machine that has nothing pre-installed
VM-2: Windows 11 — Clean, no Tally, no Python
      Purpose: Test installer on latest Windows
VM-3: Windows 10 + TallyPrime 3.x (HTTP disabled initially)
      Purpose: Test the full install + Tally activation wizard
```
Take **snapshots** of each VM in their clean state. You will revert to these snapshots repeatedly in Phase 4.

#### Cloud Environment (AWS ap-south-1 — Mumbai)
```bash
# Minimum for development:
# - 1x EC2 t3.small (FastAPI ingest API)
# - 1x RDS PostgreSQL t3.micro (or start with SQLite on EC2 for first 2 weeks)
# - 1x S3 bucket for OTA update hosting (Phase 5)
# Use Railway.app or Render.com for the first 3 weeks if you want zero infra overhead.
# Migrate to EC2/RDS before pilot launch (data residency requirement).
```

#### Python Dependencies (install in a venv now)
```bash
# Create the project venv
python -m venv .venv
.venv\Scripts\activate  # Windows

# Agent dependencies
pip install requests httpx pysqlcipher3 keyring schedule pywin32 pystray Pillow

# Platform dependencies  
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic

# Testing dependencies
pip install pytest pytest-asyncio pytest-mock responses httpx coverage

# Build dependencies (for later phases)
pip install pyinstaller

# Save pinned versions
pip freeze > requirements.txt
```

> **Potential gotcha**: `pysqlcipher3` requires the SQLCipher C library. On Windows, use the pre-built wheel from [https://github.com/rigglemania/pysqlcipher3](https://github.com/rigglemania/pysqlcipher3) or use `sqlcipher3` package. Test this install first — it is the most brittle dependency.

#### Tally Test Environment
Create a test company in TallyPrime with realistic data:
```
Test Company: "Sharma Traders Pvt Ltd" (use this — test Devanagari separately)
Test Company 2: "शर्मा ट्रेडर्स" (Devanagari name — critical test)
Minimum data to enter manually (or import):
- 10 ledger accounts (5 debtors, 3 creditors, 1 bank, 1 cash)
- 20 Sales vouchers (spread across 2 months)
- 15 Purchase vouchers
- 10 Receipt vouchers (against sales)
- 8 Payment vouchers (against purchases)
- 3 Journal vouchers
```

This data set is your reference fixture. Every extraction test will be validated against it.

### 0.2 Phase 0 Verification Checklist

Run each check manually. Do not proceed until all pass.

```bash
# 1. Python version
python --version
# Expected: Python 3.11.x

# 2. Tally HTTP server is running
curl http://localhost:9000
# Expected: Some XML response (even an error XML is fine — it means Tally answered)

# 3. SQLCipher works
python -c "from pysqlcipher3 import dbapi2 as sqlite; print('SQLCipher OK')"
# Expected: SQLCipher OK

# 4. Keyring works (Windows Credential Manager)
python -c "import keyring; keyring.set_password('test', 'user', 'pass123'); print(keyring.get_password('test', 'user'))"
# Expected: pass123

# 5. Cloud reachable (after deploying FastAPI stub)
curl https://your-ingest-api.com/health
# Expected: {"status": "ok"}
```

**Phase 0 is done when**: All 5 checks pass and all 3 VMs have clean snapshots.

---

[Note: Remaining phases (1-6) abbreviated here. See full plan in docs/testing/IMPLEMENTATION_PLAN.md or refer to the planning document for complete details on each phase.]

---

**For complete implementation details including code examples, testing procedures, and troubleshooting, see the full IMPLEMENTATION_PLAN.md document.**
