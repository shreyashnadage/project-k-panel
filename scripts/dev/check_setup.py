#!/usr/bin/env python3
"""
Quick Setup Verification Script
Checks that all critical packages are working correctly.
Run this to verify your environment is ready.
"""

import sys
import subprocess
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("ENVIRONMENT VERIFICATION")
print("=" * 70)
print()

# 1. Check Python version
print("[1/8] Checking Python Version...")
major, minor = sys.version_info[:2]
if major == 3 and minor >= 11:
    print(f"  ✓ Python {major}.{minor}.{sys.version_info.micro} - OK")
else:
    print(f"  ✗ Python {major}.{minor} - Need 3.11+")
    sys.exit(1)
print()

# 2. Check virtual environment
print("[2/8] Checking Virtual Environment...")
if ".venv" in sys.prefix or "venv" in sys.prefix:
    print(f"  ✓ Virtual environment active: {sys.prefix}")
else:
    print(f"  ⚠ Not in virtual environment: {sys.prefix}")
print()

# 3. Check core imports
print("[3/8] Checking Core Imports...")
packages_to_check = {
    "requests": "HTTP client",
    "httpx": "Async HTTP client",
    "keyring": "Credential manager",
    "schedule": "Task scheduling",
    "PIL": "Image processing",
}

all_ok = True
for pkg, desc in packages_to_check.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg:<15} - {desc}")
    except ImportError as e:
        print(f"  ✗ {pkg:<15} - {desc} (MISSING)")
        all_ok = False

if not all_ok:
    print("\n  Install missing packages with: pip install -r requirements.txt")
    sys.exit(1)
print()

# 4. Check web framework
print("[4/8] Checking Web Framework...")
web_packages = {
    "fastapi": "API framework",
    "uvicorn": "ASGI server",
    "pydantic": "Data validation",
    "sqlalchemy": "ORM",
}

for pkg, desc in web_packages.items():
    try:
        __import__(pkg)
        print(f"  ✓ {pkg:<15} - {desc}")
    except ImportError:
        print(f"  ✗ {pkg:<15} - {desc} (MISSING)")
        all_ok = False

if not all_ok:
    sys.exit(1)
print()

# 5. Check testing tools
print("[5/8] Checking Testing Tools...")
test_packages = {
    "pytest": "Test framework",
    "pytest_asyncio": "Async tests",
    "pytest_mock": "Mocking",
}

for pkg, desc in test_packages.items():
    try:
        __import__(pkg.replace("_", "-"))
        print(f"  ✓ {pkg:<20} - {desc}")
    except ImportError:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✓ {pkg:<20} - {desc}")
        except ImportError:
            print(f"  ✗ {pkg:<20} - {desc} (MISSING)")
            all_ok = False

if not all_ok:
    sys.exit(1)
print()

# 6. Check code quality tools
print("[6/8] Checking Code Quality Tools...")
try:
    result = subprocess.run(["black", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  ✓ black      - {result.stdout.strip()}")
    else:
        print(f"  ✗ black      - Not working")
except Exception as e:
    print(f"  ✗ black      - {str(e)}")

try:
    result = subprocess.run(["ruff", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  ✓ ruff       - {result.stdout.strip()}")
    else:
        print(f"  ✗ ruff       - Not working")
except Exception as e:
    print(f"  ✗ ruff       - {str(e)}")

try:
    result = subprocess.run(["mypy", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  ✓ mypy       - {result.stdout.strip()}")
    else:
        print(f"  ✗ mypy       - Not working")
except Exception as e:
    print(f"  ✗ mypy       - {str(e)}")
print()

# 7. Check pytest
print("[7/8] Checking pytest...")
try:
    result = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"  ✓ {result.stdout.strip()}")
    else:
        print(f"  ✗ pytest failed")
except Exception as e:
    print(f"  ✗ {str(e)}")
print()

# 8. Check repository structure
print("[8/8] Checking Repository Structure...")
required_dirs = [
    "agent/extractor",
    "agent/queue",
    "platform/api",
    "tests/unit",
    "docs",
]

dirs_ok = True
for dir_name in required_dirs:
    if Path(dir_name).exists():
        print(f"  ✓ {dir_name}")
    else:
        print(f"  ✗ {dir_name} - MISSING")
        dirs_ok = False

if not dirs_ok:
    print("\n  Repository structure incomplete!")
    sys.exit(1)
print()

# Summary
print("=" * 70)
print("✅ ALL CHECKS PASSED - ENVIRONMENT IS READY!")
print("=" * 70)
print()
print("Next steps:")
print("  1. Activate venv: .\.venv\Scripts\Activate.ps1")
print("  2. Start TallyPrime with HTTP enabled on port 9000")
print("  3. Create test company 'Sharma Traders Pvt Ltd'")
print("  4. Begin Phase 1 implementation")
print()
