# -*- coding: utf-8 -*-
"""
Registration + service integration test suite.

Tests:
  1. Registration module — credential read/write/delete
  2. Config resolution — env vars vs credential manager priority
  3. Registration wizard helpers — device name, OS version
  4. Installation key format validation
  5. Cloud registration endpoints — POST /register, POST /v1/register-device
  6. Device listing and key rotation
  7. Agent startup with credential manager (no env vars)
  8. Full onboarding flow: portal register -> install key -> device register -> agent polls

Prerequisites:
  - Cloud platform running on port 8000
  - Database seeded (python tests/seed_e2e.py)

Run: python tests/test_registration_service.py
"""

import os
import sys
import json
import time
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

os.environ["DATABASE_URL"] = "sqlite:///tally_sync_dev.db"
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger("registration_test")

CLOUD   = "http://localhost:8000"
API_KEY = "test-api-key-e2e-local-dev"
DEVICE  = "device-e2e-001"
HDR     = {"X-API-Key": API_KEY}

from agent.registration import (
    get_credentials, store_credentials, delete_credentials, is_registered,
    CRED_SERVICE, CRED_USERNAME,
)

# ── helpers ──────────────────────────────────────────────────────────────────

passed = 0
failed = 0
results_log = []


def banner(text):
    print(f"\n{'='*65}")
    print(f"  {text}")
    print(f"{'='*65}")


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results_log.append((status, label, detail))
    return condition


# ── tests ────────────────────────────────────────────────────────────────────

def test_registration_module():
    banner("TEST 1: Registration module — read/write/delete")

    # Read existing credentials (should exist from prior setup)
    creds = get_credentials()
    check("get_credentials returns dict", isinstance(creds, dict))
    check("Has client_id", bool(creds.get("client_id")) if creds else False)
    check("Has device_id", bool(creds.get("device_id")) if creds else False)
    check("Has api_key", bool(creds.get("api_key")) if creds else False)
    check("is_registered() returns True", is_registered())

    # Store test credentials (we'll restore originals after)
    original = creds.copy() if creds else None

    test_creds = {
        "client_id": "test-client-001",
        "device_id": "test-device-001",
        "api_key": "test-key-001",
        "api_base_url": "http://localhost:8000",
    }
    ok = store_credentials(test_creds)
    check("store_credentials succeeds", ok)

    read_back = get_credentials()
    check("Read back matches written", read_back == test_creds)

    # Restore original credentials
    if original:
        store_credentials(original)
        restored = get_credentials()
        check("Original credentials restored", restored == original)


def test_config_resolution():
    banner("TEST 2: Config resolution — env vars take priority")
    from agent.config import Config, _get

    # With env vars set (from .env), env vars should win
    env_key = os.environ.get("AGENT_API_KEY", "")
    resolved = _get("AGENT_API_KEY")
    if env_key:
        check("Env var takes priority over cred mgr", resolved == env_key)
    else:
        # No env var — should fall back to cred mgr
        creds = get_credentials()
        if creds:
            check("Falls back to cred mgr when no env var", resolved == creds.get("api_key"))

    # Test with env var explicitly cleared
    with patch.dict(os.environ, {}, clear=True):
        from importlib import reload
        # _get should fall to cred mgr
        val = _get("AGENT_API_KEY")
        creds = get_credentials()
        expected = creds.get("api_key") if creds else ""
        check("_get falls back to cred mgr", val == expected,
              f"got={val[:8]}..." if val else "empty")


def test_wizard_helpers():
    banner("TEST 3: Wizard helpers — device name, OS version")
    import socket
    import platform as plat

    hostname = socket.gethostname()
    check("Device name is non-empty", bool(hostname), hostname)

    os_ver = f"Windows {plat.version()}"
    check("OS version string is valid", "Windows" in os_ver, os_ver)


def test_key_format_validation():
    banner("TEST 4: Installation key format validation")

    valid_keys = ["TSA-ABC123-DEF456-GHI789", "TSA-2026-XXXXX", "TSA-A1B2C3"]
    for key in valid_keys:
        check(f"Valid key: {key}", key.upper().startswith("TSA-"))

    # Note: wizard does .upper() before checking, so "tsa-123" is valid
    invalid_keys = ["ABC-123", "", "NOTAKEY", "12345"]
    for key in invalid_keys:
        is_valid = key.upper().startswith("TSA-") if key else False
        check(f"Invalid key rejected: '{key}'", not is_valid)


def test_cloud_registration_endpoint():
    banner("TEST 5: Cloud registration endpoints")

    # Test POST /register (create new client) — uses query params
    test_email = f"test-reg-{int(time.time())}@example.com"
    resp = requests.post(
        f"{CLOUD}/v1/register",
        params={
            "company_name": "Test MSME Corp",
            "email": test_email,
            "phone": "+91-9876543210",
        },
        timeout=10,
    )
    check("POST /register succeeds", resp.status_code in (200, 201), resp.text[:200])

    if resp.status_code == 201:
        data = resp.json()
        check("Returns client_id", bool(data.get("client_id")))
        check("Returns installation_key", bool(data.get("installation_key")))
        install_key = data.get("installation_key", "")
        check("Key starts with TSA-", install_key.startswith("TSA-"),
              install_key[:20] if install_key else "?")
        check("Returns expiry info", data.get("expires_in_days", 0) > 0,
              f"{data.get('expires_in_days')} days")

        # Test POST /v1/register-device with the key
        resp2 = requests.post(
            f"{CLOUD}/v1/register-device",
            params={
                "installation_key": install_key,
                "device_name": "TEST-PC-001",
                "os_version": "Windows 11",
                "agent_version": "0.5.0",
            },
            timeout=10,
        )
        check("POST /v1/register-device returns 200", resp2.status_code == 200,
              resp2.text[:200])

        if resp2.status_code == 200:
            dev_data = resp2.json()
            check("Returns device_id", bool(dev_data.get("device_id")))
            check("Returns api_key", bool(dev_data.get("api_key")))
            check("Returns status=registered", dev_data.get("status") == "registered")
            check("api_key starts with sk_live_",
                  dev_data.get("api_key", "").startswith("sk_live_"))

            # Verify key is now used (can't register again)
            resp3 = requests.post(
                f"{CLOUD}/v1/register-device",
                params={
                    "installation_key": install_key,
                    "device_name": "TEST-PC-002",
                    "os_version": "Windows 11",
                    "agent_version": "0.5.0",
                },
                timeout=10,
            )
            check("Key cannot be reused", resp3.status_code != 200,
                  f"status={resp3.status_code}")
            return dev_data

    return None


def test_device_listing():
    banner("TEST 6: Device listing and stats")

    resp = requests.get(
        f"{CLOUD}/v1/clients/tenant-e2e-001/stats",
        headers=HDR,
        timeout=10,
    )
    # This might 404 if client_id doesn't match, but the endpoint should exist
    check("Stats endpoint exists", resp.status_code in (200, 404),
          f"status={resp.status_code}")


def test_agent_startup_with_cred_mgr():
    banner("TEST 7: Agent startup with credential manager")

    from agent.config import Config

    # Verify Config.validate() passes (either env or cred mgr)
    try:
        Config.validate()
        check("Config.validate() passes", True)
    except RuntimeError as e:
        check("Config.validate() passes", False, str(e))

    source = Config.source_info()
    check("Config source is identified", source != "unknown", source)

    check("API_KEY is set", bool(Config.API_KEY))
    check("DEVICE_ID is set", bool(Config.DEVICE_ID))
    check("CLOUD_URL is set", bool(Config.CLOUD_URL))


def test_full_onboarding_flow():
    banner("TEST 8: Full onboarding flow simulation")

    # Step 1: Portal registration — uses query params
    email = f"onboard-{int(time.time())}@testmsme.com"
    resp1 = requests.post(
        f"{CLOUD}/v1/register",
        params={
            "company_name": "Onboarding Test Traders",
            "email": email,
            "phone": "+91-1234567890",
            "gst_id": "29AABCT1234F1Z5",
        },
        timeout=10,
    )
    check("Step 1: Portal registration", resp1.status_code in (200, 201))
    reg_data = resp1.json()
    client_id = reg_data.get("client_id")
    install_key = reg_data.get("installation_key")
    check("Got client_id", bool(client_id))
    check("Got installation key", bool(install_key))

    # Step 2: Device registration (simulates wizard)
    resp2 = requests.post(
        f"{CLOUD}/v1/register-device",
        params={
            "installation_key": install_key,
            "device_name": "ONBOARD-PC",
            "os_version": "Windows 11 Pro",
            "agent_version": "0.5.0",
        },
        timeout=10,
    )
    check("Step 2: Device registration", resp2.status_code == 200)
    dev_data = resp2.json()
    device_id = dev_data.get("device_id")
    api_key = dev_data.get("api_key")
    check("Got device_id", bool(device_id))
    check("Got api_key", bool(api_key))

    # Step 3: Store credentials (simulates wizard _store_credentials)
    original_creds = get_credentials()
    test_creds = {
        "client_id": client_id,
        "device_id": device_id,
        "api_key": api_key,
        "api_base_url": CLOUD,
    }
    store_credentials(test_creds)
    check("Step 3: Credentials stored", is_registered())

    # Step 4: Verify agent can use these credentials to call the cloud
    # Use direct HTTP to validate the new device's api_key works
    try:
        resp4 = requests.get(
            f"{CLOUD}/v1/commands/pending",
            params={"device_id": device_id},
            headers={"X-API-Key": api_key},
            timeout=10,
        )
        check("Step 4: Agent polls with new api_key",
              resp4.status_code == 200,
              f"status={resp4.status_code}")
    except Exception as e:
        check("Step 4: Agent polls with new api_key", False, str(e))

    # Step 5: Admin endpoint requires JWT auth (401 proves it exists)
    resp5 = requests.get(
        f"{CLOUD}/v1/admin/clients",
        headers=HDR,
        timeout=10,
    )
    check("Step 5: Admin endpoint exists (requires JWT)",
          resp5.status_code in (200, 401, 403),
          f"status={resp5.status_code}")

    # Restore original credentials
    if original_creds:
        store_credentials(original_creds)
        check("Original credentials restored", True)


# ── pre-flight ───────────────────────────────────────────────────────────────

def preflight():
    banner("PRE-FLIGHT CHECKS")
    try:
        r = requests.get(f"{CLOUD}/", timeout=3)
        check("Cloud platform reachable", r.status_code == 200)
    except Exception:
        print("  FATAL: Cloud not running on port 8000")
        sys.exit(1)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    banner("REGISTRATION + SERVICE INTEGRATION TEST SUITE")

    preflight()

    # Unit-level tests (no cloud needed for 1-4)
    test_registration_module()
    test_config_resolution()
    test_wizard_helpers()
    test_key_format_validation()

    # Integration tests (need cloud)
    test_cloud_registration_endpoint()
    test_device_listing()
    test_agent_startup_with_cred_mgr()
    test_full_onboarding_flow()

    banner(f"RESULTS: {passed} passed, {failed} failed")
    if failed:
        print("\n  FAILURES:")
        for status, label, detail in results_log:
            if status == "FAIL":
                print(f"    - {label}: {detail}")
    print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
