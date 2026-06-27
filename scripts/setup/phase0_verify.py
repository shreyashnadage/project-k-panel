#!/usr/bin/env python3
"""
Phase 0 Environment Verification Script
========================================
Run this script to verify your development environment is correctly set up.
All checks should pass before proceeding to Phase 1.

Usage:
    python phase0_verify.py
"""

import sys
import subprocess
import socket
from pathlib import Path
from typing import Tuple

CHECKS_PASSED = 0
CHECKS_FAILED = 0


def check(name: str) -> Tuple[bool, str]:
    """Execute a check and return (passed, message)."""
    global CHECKS_PASSED, CHECKS_FAILED
    print(f"\n[CHECK] {name}")
    print("  ", end="", flush=True)
    return None, None


def report(name: str, passed: bool, message: str = ""):
    """Report a check result."""
    global CHECKS_PASSED, CHECKS_FAILED
    if passed:
        CHECKS_PASSED += 1
        print(f"✓ PASS: {name}")
        if message:
            print(f"        {message}")
    else:
        CHECKS_FAILED += 1
        print(f"✗ FAIL: {name}")
        if message:
            print(f"        {message}")


def check_python_version() -> bool:
    """Python 3.11+ required."""
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 11:
        report("Python 3.11+", True, f"Current: {major}.{minor}.{sys.version_info.micro}")
        return True
    else:
        report("Python 3.11+", False, f"Found Python {major}.{minor}. Minimum required: 3.11")
        return False


def check_python_not_store() -> bool:
    """Warn if Python is from Microsoft Store (PyInstaller issues)."""
    python_exe = Path(sys.executable)
    is_store = "WindowsApps" in str(python_exe)
    if is_store:
        report("Python from python.org (not Store)", False,
               f"Current: {python_exe} — Get from https://python.org")
        return False
    else:
        report("Python from python.org (not Store)", True,
               f"Current: {python_exe}")
        return True


def check_tally_reachable() -> bool:
    """Test Tally HTTP server on localhost:9000."""
    try:
        sock = socket.create_connection(("localhost", 9000), timeout=3)
        sock.close()
        report("Tally HTTP Server Reachable", True, "localhost:9000 is responding")
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        report("Tally HTTP Server Reachable", False,
               "Cannot reach localhost:9000. Is Tally open? Is HTTP enabled in Tally.ini?")
        return False


def check_sqlcipher() -> bool:
    """Test SQLCipher import."""
    try:
        from pysqlcipher3 import dbapi2
        report("SQLCipher Available", True, "pysqlcipher3 module found")
        return True
    except ImportError:
        report("SQLCipher Available", False,
               "pysqlcipher3 not installed. Run: pip install pysqlcipher3")
        return False


def check_keyring() -> bool:
    """Test Windows Credential Manager via keyring."""
    try:
        import keyring
        # Try a test credential
        keyring.set_password("TallySyncAgent_PhaseZeroTest", "testuser", "testpass123")
        retrieved = keyring.get_password("TallySyncAgent_PhaseZeroTest", "testuser")
        keyring.delete_password("TallySyncAgent_PhaseZeroTest", "testuser")
        if retrieved == "testpass123":
            report("Keyring (Windows Credential Manager)", True,
                   "Can set/get/delete credentials")
            return True
        else:
            report("Keyring (Windows Credential Manager)", False,
                   "Retrieved credential does not match")
            return False
    except Exception as e:
        report("Keyring (Windows Credential Manager)", False, str(e))
        return False


def check_git_installed() -> bool:
    """Test Git is available."""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            report("Git Installed", True, version)
            return True
        else:
            report("Git Installed", False, "git --version failed")
            return False
    except FileNotFoundError:
        report("Git Installed", False,
               "git command not found. Install from https://git-scm.com/")
        return False


def check_pytest_installed() -> bool:
    """Test pytest is available."""
    try:
        result = subprocess.run(["python", "-m", "pytest", "--version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            report("pytest Installed", True, version)
            return True
        else:
            report("pytest Installed", False, "pytest --version failed")
            return False
    except Exception as e:
        report("pytest Installed", False,
               f"pytest not found. Run: pip install pytest pytest-asyncio pytest-mock")
        return False


def check_repository_structure() -> bool:
    """Verify required directory structure exists."""
    required_dirs = [
        "agent/extractor",
        "agent/queue",
        "agent/transmitter",
        "agent/updater",
        "agent/monitor",
        "agent/tray",
        "platform/api",
        "platform/db",
        "platform/analytics",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "docs",
    ]
    missing = [d for d in required_dirs if not Path(d).exists()]
    if not missing:
        report("Repository Structure", True,
               f"All {len(required_dirs)} required directories present")
        return True
    else:
        report("Repository Structure", False,
               f"Missing: {', '.join(missing)}")
        return False


def check_pyproject_exists() -> bool:
    """Verify pyproject.toml exists."""
    if Path("pyproject.toml").exists():
        report("pyproject.toml Exists", True)
        return True
    else:
        report("pyproject.toml Exists", False,
               "pyproject.toml not found in project root")
        return False


def check_venv_exists() -> bool:
    """Check if virtual environment exists."""
    venv_markers = [".venv/pyvenv.cfg", "venv/pyvenv.cfg"]
    for marker in venv_markers:
        if Path(marker).exists():
            report("Virtual Environment Created", True,
                   f"Found: {Path(marker).parent}")
            return True
    report("Virtual Environment Created", False,
           "No .venv or venv found. Create with: python -m venv .venv")
    return False


def main():
    print("=" * 70)
    print("TALLY SYNC AGENT — PHASE 0 ENVIRONMENT VERIFICATION")
    print("=" * 70)
    print("\nRunning checks...\n")

    # Core requirements
    print("\n[SECTION] CORE PYTHON ENVIRONMENT")
    check_python_version()
    check_python_not_store()
    check_venv_exists()

    # Third-party libraries
    print("\n[SECTION] REQUIRED PYTHON PACKAGES")
    check_sqlcipher()
    check_keyring()
    check_pytest_installed()

    # External tools
    print("\n[SECTION] EXTERNAL TOOLS")
    check_git_installed()
    check_tally_reachable()

    # Repository structure
    print("\n[SECTION] REPOSITORY SETUP")
    check_repository_structure()
    check_pyproject_exists()

    # Summary
    print("\n" + "=" * 70)
    total = CHECKS_PASSED + CHECKS_FAILED
    print(f"RESULTS: {CHECKS_PASSED}/{total} checks passed")
    print("=" * 70)

    if CHECKS_FAILED == 0:
        print("\n✓ ALL CHECKS PASSED — YOU ARE READY FOR PHASE 1!")
        return 0
    else:
        print(f"\n✗ {CHECKS_FAILED} check(s) failed — fix above issues before proceeding")
        return 1


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows console
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
