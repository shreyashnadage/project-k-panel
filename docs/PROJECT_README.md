# Tally Sync Agent

A Windows-based agent that extracts accounting data from TallyPrime in real-time and syncs it to a cloud platform for working capital analytics.

## Quick Start

### Phase 0: Environment Setup (2–3 days)
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows

# 2. Install dependencies
pip install -e ".[agent,platform,dev]"

# 3. Verify your setup
python phase0_verify.py
```

See [PHASE0_SETUP.md](PHASE0_SETUP.md) for detailed setup instructions.

### Phase 1: Build Tally Extractor (5–7 days)
Extract ledgers and vouchers from TallyPrime via HTTP/TDML API.

```bash
# Run the extraction script (requires Tally running on localhost:9000)
set TALLY_COMPANY_NAME=Sharma Traders Pvt Ltd
set TALLY_COMPANY_GUID=your-guid-here
python run_extraction.py
```

### Phase 2: Cloud Ingest API (5–7 days)
Deploy a FastAPI backend that accepts and deduplicates incoming voucher data.

### Phase 3: End-to-End Pipeline (5–7 days)
Connect extractor → queue → cloud API. **Pilot-ready milestone.**

### Phase 4: Windows Service + Installer (7–10 days)
Package as signed installer with auto-updates. **Scale-ready milestone.**

### Phase 5: OTA Updates + Fleet Monitoring (5–7 days)
Deploy new versions and monitor agent health from central dashboard.

### Phase 6: Analytics Engine (10–14 days)
Compute working capital metrics (CCC, DSO, DPO, cash flow).

## Repository Structure

```
tally-sync-agent/
├── agent/                          # Python agent (runs on customer machine)
│   ├── extractor/                  # Tally XML extraction logic
│   ├── queue/                      # SQLite/SQLCipher outbound queue
│   ├── transmitter/                # Cloud ingest API client
│   ├── updater/                    # OTA update logic
│   ├── monitor/                    # Heartbeat reporter
│   ├── tray/                       # System tray application
│   ├── orchestrator.py             # Main scheduler loop
│   ├── config.py                   # Configuration loader
│   └── main.py                     # Entry point
│
├── platform/                       # Cloud backend (FastAPI)
│   ├── api/                        # HTTP endpoints
│   ├── db/                         # Database models + migrations
│   ├── analytics/                  # Working capital engine
│   └── main.py                     # FastAPI app
│
├── installer/                      # Inno Setup + NSSM config
│   ├── setup.iss                   # Installer script
│   └── nssm_config.bat             # Service installation
│
├── tests/                          # Test suites
│   ├── unit/                       # Fast unit tests
│   ├── integration/                # Tests requiring Tally/DB
│   └── e2e/                        # Deployed environment tests
│
├── docs/                           # Documentation
│   └── testing/                    # Testing guides per phase
│
├── pyproject.toml                  # Project metadata + dependencies
├── phase0_verify.py                # Environment verification script
├── PHASE0_SETUP.md                 # Phase 0 setup instructions
├── Makefile                        # Common development commands
└── README.md                       # This file
```

## Development Commands

```bash
# Setup
make venv              # Create virtual environment
make install-dev       # Install all dependencies (dev + runtime)

# Testing
make test              # Run all tests
make test-unit         # Fast unit tests only
make coverage          # Generate coverage report
make phase0-verify     # Verify Phase 0 setup

# Code quality
make lint              # Run ruff + mypy
make format            # Format code with black

# Build
make build-agent       # Build Windows executable
```

## Testing

### Phase 0 Verification
Confirms your development environment is ready:
```bash
python phase0_verify.py
```

### Unit Tests (No External Dependencies)
Fast tests that run locally without Tally or cloud:
```bash
make test-unit
```

### Integration Tests (Requires Tally)
Tests against your local Tally instance:
```bash
make test-integration
```

### E2E Tests (Requires Deployed Platform)
Validates a deployed agent and cloud backend:
```bash
python tests/e2e/remote_test_suite.py \
  --phase 3 \
  --api-url https://api.yourplatform.in \
  --api-key your-api-key \
  --tenant-id test-001
```

## Configuration

### Phase 1–3: Environment Variables
```bash
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Sharma Traders Pvt Ltd
TALLY_COMPANY_GUID=your-guid
INGEST_API_URL=https://api.yourplatform.in
INGEST_API_KEY=your-key
TENANT_ID=your-tenant-id
```

### Phase 4+: Windows Credential Manager + Config File
- API key: Stored securely in Windows Credential Manager (not in files)
- Config: `%ProgramData%\TallySyncAgent\config.ini`

## Implementation Plan

See [docs/testing/IMPLEMENTATION_PLAN.md](docs/testing/IMPLEMENTATION_PLAN.md) for the complete 6-phase breakdown with:
- Detailed code examples
- Testing procedures
- Phase gates and success criteria
- Time-to-market milestones
- Troubleshooting guide

## Key Milestones

| Week | Milestone | Status |
|---|---|---|
| End of Week 1 | Phase 0 + Phase 1 | ⏳ |
| End of Week 2 | Phase 2 | ⏳ |
| End of Week 3 | Phase 3 (Pilot-Ready) | ⏳ |
| End of Week 5 | Phase 4 (Scale-Ready) | ⏳ |
| End of Week 6 | Phase 5 | ⏳ |
| End of Week 8 | Phase 6 (Full Product) | ⏳ |

## Support

### Phase 0 Setup Issues
See [PHASE0_SETUP.md](PHASE0_SETUP.md) → "Troubleshooting" section

### Tally Extraction Issues
See docs/testing/IMPLEMENTATION_PLAN.md → "Appendix B: Common Failure Modes"

### Build/Deployment Issues
See docs/testing/IMPLEMENTATION_PLAN.md → Phase 4–5 troubleshooting

## License

MIT

## Author

Shreya Nadage  
Email: shreyashnadage@gmail.com
