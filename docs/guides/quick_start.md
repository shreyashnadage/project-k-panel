# Quick Start — Phase 0 Setup

**You are here**: Phase 0 — Development Environment Setup  
**Goal**: Get your machine ready to start Phase 1  
**Time**: ~4–5 hours of hands-on work

---

## 1. Install Python 3.11+

⚠️ **Critical**: Download from https://python.org, NOT the Microsoft Store

```bash
# After installation, verify:
python --version
# Expected: Python 3.11.x or higher
```

---

## 2. Create and Activate Virtual Environment

```bash
# In C:\Users\shrey\tally-shayak\
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# You should see (.venv) in your prompt now
```

---

## 3. Install Project Dependencies

```bash
# From within activated venv:
pip install -e ".[agent,platform,dev]"

# This takes 2-3 minutes. Let it finish.
```

---

## 4. Verify Your Setup

```bash
python phase0_verify.py
```

**Expected output**: All 11 checks should show ✓

If any checks fail, see [PHASE0_SETUP.md → Troubleshooting](PHASE0_SETUP.md#troubleshooting)

---

## 5. Set Up Tally Test Environment

### In TallyPrime 3.x:

1. **Enable HTTP Server**
   - Open or create `Tally.ini`
   - Add section:
     ```ini
     [HTTP]
     Enabled=Yes
     Port=9000
     ```
   - Restart Tally

2. **Create Test Company**
   - Company: "Sharma Traders Pvt Ltd"
   - Add sample data:
     - 10 ledgers (mix of debtors, creditors, bank, cash)
     - 20+ sales vouchers
     - 10+ purchase/receipt/payment vouchers
   - Note the company GUID (Company Info page)

3. **Create Devanagari Test Company**
   - Company: "शर्मा ट्रेडर्स"
   - Add 3–5 vouchers (tests Unicode handling)

---

## 6. Save Configuration

Create `.env.local` (copy from `.env.example` and fill in):

```bash
# .env.local — DO NOT COMMIT TO GIT
TALLY_COMPANY_NAME=Sharma Traders Pvt Ltd
TALLY_COMPANY_GUID=<get-from-tally-company-info>
TALLY_DEVANAGARI_COMPANY=शर्मा ट्रेडर्स
TALLY_URL=http://localhost:9000
```

---

## 7. (Optional) Set Up Virtual Machines for Phase 4

Later in Phase 4 you will need clean VMs to test the installer. Set them up now:

- **VM 1**: Windows 10 (1909) — no Python, no Tally
- **VM 2**: Windows 11 — no Python, no Tally  
- **VM 3**: Windows 10 + TallyPrime 3.x (HTTP disabled)

Take snapshots of each so you can revert repeatedly during testing.

---

## 8. (Optional) Set Up Cloud Environment

- **Option A (Fast)**: Use Railway.app with PostgreSQL
- **Option B (Production)**: AWS ap-south-1 (EC2 + RDS)

Come back to this after Phase 1 if you just want to get started.

---

## 9. Verify Tally is Reachable

```bash
# In PowerShell with .venv activated:
python phase0_verify.py

# Look for: ✓ PASS: Tally HTTP Server Reachable — localhost:9000 is responding
```

---

## 10. (Optional) Initialize Git

```bash
git init
git config user.name "Shreya Nadage"
git config user.email "shreyashnadage@gmail.com"
git add .
git commit -m "Phase 0: Initial project structure and dependencies"

# To push to GitHub:
# git remote add origin https://github.com/yourorg/tally-sync-agent.git
# git push -u origin main
```

---

## Useful Commands Once Setup is Done

```bash
# Activate venv
.venv\Scripts\activate

# Verify everything is good
make phase0-verify  # or: python phase0_verify.py

# Run tests
make test-unit

# Format code
make format

# Get help on available commands
make help
```

---

## Phase 0 Gate — Am I Ready for Phase 1?

✅ Pass ALL of these before proceeding:

- [ ] `python phase0_verify.py` shows all ✓ checks
- [ ] Tally running on localhost:9000 with HTTP enabled
- [ ] Test company "Sharma Traders Pvt Ltd" exists with 20+ vouchers
- [ ] Devanagari company "शर्मा ट्रेडर्स" exists with 3–5 vouchers
- [ ] `.env.local` has Tally details filled in
- [ ] VM snapshots created (for Phase 4 testing)
- [ ] Virtual environment working: `(.venv)` shows in prompt

---

## Troubleshooting

### Python Issues
- **"Python not found"** → Install from https://python.org, add to PATH
- **"PyInstaller doesn't recognize this Python"** → You're using Microsoft Store version; uninstall, get from python.org
- **"pysqlcipher3 won't install"** → See PHASE0_SETUP.md for alternatives

### Tally Issues
- **"Cannot reach localhost:9000"** → Tally not running, or HTTP disabled. Check Tally.ini, restart Tally
- **"Tally HTTP returns garbled XML"** → Encoding issue; Phase 1 handles it

### Virtual Environment Issues
- **"No module named 'X'"** → Activate venv first, then `pip install -e ".[agent,platform,dev]"`

---

## What's Next: Phase 1

Once Phase 0 gate is passed:

→ **Phase 1: Build the Tally Extractor** (5–7 days)

You'll implement:
- Tally HTTP client (`agent/extractor/client.py`)
- XML parser (`agent/extractor/parser.py`)
- Watermark tracker (`agent/extractor/watermark.py`)
- Unit tests

Then run extraction script and validate it matches Tally data.

---

## Quick Reference

| What | Command | Time |
|---|---|---|
| Create venv | `python -m venv .venv` | 1 min |
| Activate venv | `.venv\Scripts\activate` | Instant |
| Install deps | `pip install -e ".[agent,platform,dev]"` | 3 min |
| Verify setup | `python phase0_verify.py` | 30 sec |
| Run tests | `make test-unit` | 5–10 sec |
| Format code | `make format` | 5 sec |
| See all commands | `make help` | Instant |

---

## Files to Know

| File | Purpose |
|---|---|
| `README.md` | Overview of the whole project |
| `PHASE0_SETUP.md` | Detailed setup instructions |
| `PHASE0_STATUS.md` | What was implemented in Phase 0 |
| `phase0_verify.py` | Verification script you just ran |
| `pyproject.toml` | Python dependencies |
| `Makefile` | Common commands |
| `CLAUDE.md` | Project context for Claude |
| `docs/testing/IMPLEMENTATION_PLAN.md` | Full 6-phase roadmap |

---

**Questions?** See [PHASE0_SETUP.md](PHASE0_SETUP.md) for detailed troubleshooting.

**Ready to start Phase 1?** Proceed once all gate items above are ✓.
