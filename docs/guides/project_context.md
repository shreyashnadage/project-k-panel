# Claude Code Configuration

This file contains project context and collaboration guidelines for Claude Code.

## Project Overview

**Tally Sync Agent** — A Windows-based data pipeline that extracts accounting data from TallyPrime and syncs it to a cloud platform for working capital analytics.

- **Current Phase**: 0 (Development Environment Setup)
- **Target Launch**: 8 weeks (pilot-ready at week 3)
- **Primary User**: Shreya Nadage (Founding Engineer)
- **Architecture**: Windows agent (Python) + Cloud backend (FastAPI/PostgreSQL)

## Implementation Strategy

Follow the **6-Phase Implementation & Testing Plan** (see docs/testing/IMPLEMENTATION_PLAN.md):

1. **Phase 0**: Development environment (current)
2. **Phase 1**: Tally extraction script
3. **Phase 2**: Cloud ingest API
4. **Phase 3**: End-to-end pipeline (pilot-ready)
5. **Phase 4**: Windows service + signed installer
6. **Phase 5**: OTA updates + fleet monitoring
7. **Phase 6**: Working capital analytics engine

Each phase has:
- Detailed code examples
- Test plan and gate criteria
- Success metrics

**Do NOT skip phase gates** — they prevent compounding bugs.

## Working Preferences

- **Code Style**: Follow PEP 8; use black (100 char line length)
- **Testing**: Unit tests before integration tests; test-driven development preferred
- **Documentation**: Minimal — only document the WHY, not the WHAT
- **Git**: New commits instead of amends; clear messages focused on intent
- **Scope**: Stay within current phase; flag out-of-scope work for separate tasks

## Critical Context

### Tally Integration
- **HTTP API**: TallyPrime exposes TDML (XML) API on port 9000
- **Single-threaded**: Tally HTTP server is serialized — never send concurrent requests
- **Character Encoding**: Responses are UTF-16; responses may contain Devanagari/Hindi text
- **Watermark Tracking**: Essential for incremental sync; use date-based for MVP, ALTERID for Phase 3+
- **Test Company**: "Sharma Traders Pvt Ltd" (English) + "शर्मा ट्रेडर्स" (Devanagari)

### Cloud Deployment
- **Region**: AWS ap-south-1 (Mumbai) for data residency compliance
- **Start Simple**: Use Railway.app or Render.com for Phase 0–2; migrate to EC2/RDS before pilot
- **API Security**: TLS 1.3, API key in Authorization header, idempotent endpoints
- **Database**: PostgreSQL for prod; SQLite for agent local queue (encrypted with SQLCipher in Phase 4)

### Windows Deployment
- **Target**: Windows 10 (1909) and Windows 11
- **Packaging**: PyInstaller (standalone exe) + Inno Setup (installer script)
- **Service**: NSSM (Non-Sucking Service Manager) for Windows Service management
- **Signing**: EV Code Signing Certificate required before pilot (for SmartScreen trust)
- **Credential Storage**: Windows Credential Manager (via keyring); never store secrets in config files

### Key Gotchas
1. **PyInstaller + Microsoft Store Python** → Does not work; use python.org
2. **SQLCipher dependency** → Fragile; test installation first
3. **Devanagari handling** → UTF-16 decode must happen BEFORE XML parse
4. **Tally inter-request delay** → Enforce 500ms between requests to avoid Tally hangs
5. **Idempotency** → Same (tenant, company_guid, voucher_guid) tuple = duplicate detection

## Repository Structure

```
tally-sync-agent/
├── agent/                          # Windows agent
│   ├── extractor/                  # Tally XML client + parser
│   ├── queue/                      # SQLite queue (SQLCipher in Phase 4)
│   ├── transmitter/                # Cloud API client
│   ├── updater/                    # OTA logic
│   ├── monitor/                    # Heartbeat reporter
│   ├── tray/                       # System tray app
│   ├── orchestrator.py             # Main loop
│   └── main.py                     # Entry point
├── platform/                       # FastAPI backend
│   ├── api/                        # Endpoints
│   ├── db/                         # Models + migrations
│   └── analytics/                  # Working capital engine
├── tests/                          # Test suites
├── docs/testing/                   # Phase-specific testing docs
├── installer/                      # Inno Setup scripts
├── pyproject.toml                  # Dependencies
├── PHASE0_SETUP.md                 # Setup instructions
├── phase0_verify.py                # Verification script
├── Makefile                        # Common commands
└── README.md                       # Quick reference
```

## Testing Philosophy

- **Phase 0–1**: Unit tests with fixtures (no external dependencies)
- **Phase 2**: API tests with mock DB
- **Phase 3**: Integration test against deployed environment
- **Phase 4+**: E2E test from clean Windows VM

**Remote Test Suite** (`tests/e2e/remote_test_suite.py`) is the gold standard — it validates an agent+platform from outside, without SSH access.

## Collaboration Guidelines

### When Starting a Phase
1. Read the phase section in IMPLEMENTATION_PLAN.md
2. Run relevant tests: `make test-unit` (Phase 0–1) or `make test` (Phase 2+)
3. Implement only what the phase specifies
4. Do NOT add features from later phases

### When Making Changes
- Prefer **new commits** over amends
- Run `make lint` and `make format` before committing
- Commit messages: Focus on **why**, not what (the code shows what)
- Example: ❌ "Add client.py"; ✅ "Serialize Tally requests to prevent concurrent API hangs"

### When Flagging Work
- Out-of-scope improvements → Use spawn_task (background task chip)
- Missing test coverage → Flag in code review
- Security issues → Fix immediately or flag as blocker

### Phase Gates
**Do NOT proceed to the next phase until all gate criteria are green.** This is non-negotiable.

Examples of blocker gates:
- Phase 3 → Phase 4: "Idempotency test passes" and "Crash recovery test passes"
- Phase 4 → Phase 5: "SmartScreen shows zero warnings" and "AV scan ≤2 flags"

## Environment

- **OS**: Windows 11 (primary dev machine)
- **Python**: 3.11+ from python.org (NOT Microsoft Store)
- **Tally**: TallyPrime 3.x with HTTP server on localhost:9000
- **Cloud**: Railway.app (Phase 0–2) → AWS ap-south-1 (Phase 3+)
- **IDE**: VS Code with Python extension

## Useful Commands

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[agent,platform,dev]"

# Verification (Phase 0)
python phase0_verify.py

# Testing
make test-unit              # Fast (no external deps)
make test-integration       # Requires Tally
make coverage               # Coverage report

# Code quality
make format                 # Auto-format with black
make lint                   # Check with ruff + mypy

# Build (Phase 4+)
make build-agent            # PyInstaller exe

# Useful Makefile help
make help
```

## Key Files

- `IMPLEMENTATION_PLAN.md` — Complete 6-phase roadmap
- `PHASE0_SETUP.md` — Detailed setup instructions
- `pyproject.toml` — Dependency definitions
- `phase0_verify.py` — Environment verification script
- `.Claude/settings.json` — Claude Code settings (created after first use)

---

**Last Updated**: 27 June 2026  
**Maintained By**: Shreya Nadage  
**Questions?** Refer to IMPLEMENTATION_PLAN.md or flag in GitHub issues.
