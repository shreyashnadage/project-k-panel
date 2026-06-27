#!/usr/bin/env python3
"""Quick test to verify Tally connection and find company details"""

import os
from pathlib import Path
from dotenv import load_dotenv
from agent.extractor.client import TallyClient

load_dotenv(Path('.env.local'))

TALLY_URL = os.getenv('TALLY_URL', 'http://localhost:9000')
COMPANY_NAME = os.getenv('TALLY_COMPANY_NAME', 'Sharma Traders Pvt Ltd')

print("=" * 70)
print("TALLY CONNECTION TEST")
print("=" * 70)
print()

# Test 1: Can we reach Tally?
print("[TEST 1] Checking if Tally is reachable...")
client = TallyClient(base_url=TALLY_URL)

if client.is_reachable():
    print("✓ Tally is reachable!")
else:
    print("✗ Cannot reach Tally at", TALLY_URL)
    print("  Is TallyPrime open? Is HTTP enabled on port 9000?")
    exit(1)

print()

# Test 2: Try to get company info
print("[TEST 2] Fetching company list from Tally...")
try:
    from pathlib import Path
    template = Path("agent/extractor/tdml_templates/ledgers_tp3.xml").read_text()

    # Try with company name
    tdml = template.format(company_name=COMPANY_NAME)
    response = client.request(tdml)

    print(f"✓ Successfully queried Tally for company: {COMPANY_NAME}")
    print()
    print("[RESULT] Company name works! Use this in .env.local:")
    print(f"  TALLY_COMPANY_NAME={COMPANY_NAME}")
    print(f"  TALLY_COMPANY_GUID={COMPANY_NAME}")

except Exception as e:
    print(f"✗ Error: {e}")
    print()
    print("Try these alternatives:")
    print("  1. Make sure company name is EXACTLY as it appears in Tally")
    print("  2. Check Tally.ini for the actual company name")
    print("  3. Try without spaces or special characters")

print()
print("=" * 70)
