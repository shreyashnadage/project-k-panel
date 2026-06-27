# 🔧 Scripts & Utilities

Development and testing scripts for the Tally Sync Agent project.

---

## 📁 Organization

```
scripts/
├── setup/           # Environment setup & verification
│   ├── phase0_verify.py      # Verify development environment
│   └── create_test_tenant.py # Create cloud API test tenant
│
├── dev/             # Development utilities (coming)
│   ├── inspect_queue.py      # Inspect local queue contents
│   ├── database_admin.py      # Database utilities
│   └── log_analyzer.py        # Analyze agent logs
│
└── ci/              # CI/CD scripts (future)
    └── run_tests.sh          # Automated test runner
```

---

## 🚀 Setup Scripts (`scripts/setup/`)

### `phase0_verify.py`
**Purpose**: Verify development environment is properly configured

**Usage**:
```bash
python scripts/setup/phase0_verify.py
```

**Checks**:
- ✅ Python version (3.11+)
- ✅ Virtual environment activated
- ✅ Dependencies installed
- ✅ Tally HTTP server reachable
- ✅ Cloud API reachable
- ✅ Database connectivity

**Output**: Green checkmarks for all passing, red X for failures

---

### `create_test_tenant.py`
**Purpose**: Set up test tenant in cloud API database

**Usage**:
```bash
python scripts/setup/create_test_tenant.py
```

**What it does**:
1. Creates SQLite/PostgreSQL tables (if needed)
2. Creates test tenant with API key
3. Prints tenant ID and API key for testing

**Output**:
```
✓ Tenant created successfully

Tenant Details:
  ID: test-tenant-001
  Name: Bhrama Enterprises
  API Key: test-api-key-12345

Ready to test! Use these values:
  x-api-key: test-api-key-12345
  tenant_id: test-tenant-001
```

---

## 🛠️ Development Utilities (`scripts/dev/` - Coming Soon)

### `inspect_queue.py` (Planned)
**Purpose**: Inspect local queue database

**Usage**:
```bash
python scripts/dev/inspect_queue.py --db agent_queue.db
```

**Features**:
- List pending records
- Show queue statistics
- Filter by status (pending/sent/failed)
- Export to JSON

---

### `database_admin.py` (Planned)
**Purpose**: Manage cloud database

**Usage**:
```bash
python scripts/dev/database_admin.py --action [backup|restore|cleanup]
```

**Features**:
- Backup/restore database
- Clean old records
- Check data integrity

---

### `log_analyzer.py` (Planned)
**Purpose**: Analyze agent logs

**Usage**:
```bash
python scripts/dev/log_analyzer.py --file agent.log
```

**Features**:
- Parse logs by level
- Show error patterns
- Generate summary report

---

## 🔄 CI/CD Scripts (`scripts/ci/` - Future)

### `run_tests.sh` (Planned)
**Purpose**: Run complete test suite

```bash
./scripts/ci/run_tests.sh [--unit|--integration|--all]
```

**Runs**:
- Unit tests
- Integration tests
- Code quality checks
- Coverage report

---

## 📋 Common Usage Patterns

### Verify Environment (First Time)
```bash
python scripts/setup/phase0_verify.py
```

### Set Up Cloud API for Testing
```bash
# 1. Create test tenant
python scripts/setup/create_test_tenant.py

# 2. Start cloud API
python -m uvicorn cloudplatform.main:app --reload --port 8000

# 3. Run tests
python -m pytest tests/ -v
```

### Inspect Queue During Development
```bash
python scripts/dev/inspect_queue.py --db agent_queue.db
```

### Run Full Test Suite
```bash
python -m pytest tests/ -v --cov=agent --cov=cloudplatform
```

---

## 🎯 Script Best Practices

When creating new scripts:

1. **Add shebang** (for shell scripts):
   ```bash
   #!/bin/bash
   ```

2. **Add docstring** (for Python):
   ```python
   """
   Script purpose and usage.
   """
   ```

3. **Use argparse** for CLI arguments:
   ```python
   import argparse
   parser = argparse.ArgumentParser()
   parser.add_argument('--option', help='Description')
   ```

4. **Error handling**:
   ```python
   try:
       # code
   except Exception as e:
       logger.error(f"Failed: {e}")
       sys.exit(1)
   ```

5. **Logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info("Starting script...")
   ```

---

## 📍 Running Scripts

### From Project Root
```bash
# Setup script
python scripts/setup/phase0_verify.py

# Development utility
python scripts/dev/inspect_queue.py

# CI/CD script
./scripts/ci/run_tests.sh
```

### From Any Location
```bash
# Set working directory first
cd D:\tally-shayak
python scripts/setup/create_test_tenant.py
```

---

## 🔍 Script Locations Quick Reference

| Script | Location | Purpose |
|--------|----------|---------|
| Environment verify | `scripts/setup/phase0_verify.py` | Check dev setup |
| Create test tenant | `scripts/setup/create_test_tenant.py` | Set up cloud API |
| Inspect queue | `scripts/dev/inspect_queue.py` | Debug queue *(coming)* |
| Database admin | `scripts/dev/database_admin.py` | Manage DB *(coming)* |
| Log analyzer | `scripts/dev/log_analyzer.py` | Parse logs *(coming)* |
| Test runner | `scripts/ci/run_tests.sh` | Run all tests *(coming)* |

---

## 📝 Adding New Scripts

When adding a new utility script:

1. **Create in appropriate folder** (`setup/`, `dev/`, or `ci/`)
2. **Add to this README** with purpose and usage
3. **Include docstring** and error handling
4. **Make executable** (Linux/Mac):
   ```bash
   chmod +x scripts/dev/my_script.py
   ```
5. **Test it works**:
   ```bash
   python scripts/dev/my_script.py --help
   ```

---

**Last Updated**: 27 June 2026  
**Status**: Phase 1-3 scripts complete, Phase 4+ TBD
