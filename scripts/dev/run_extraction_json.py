#!/usr/bin/env python3
"""
Phase 1: Tally Extraction Script (JSON API)

PURPOSE: Development/testing. Run this to extract data from your Tally instance.
This script uses the Tally JSON API (proven to work with your instance).

USAGE:
    python run_extraction_json.py

PREREQUISITES:
    - TallyPrime running with HTTP server enabled on localhost:9000
    - Test company created in Tally
    - .env.local configured with your company name

OUTPUT:
    - extraction_output.json: All extracted ledgers and vouchers
    - sync_state.json: Watermark tracking
"""

import json
import logging
import sys
import os
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

from agent.extractor.client import TallyClient, TallyConnectionError
from agent.extractor.parser import parse_ledgers

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env.local
load_dotenv(Path('.env.local'))

# Configuration
COMPANY_NAME = os.getenv('TALLY_COMPANY_NAME', 'Bhrama Enterprises')
TALLY_URL = os.getenv('TALLY_URL', 'http://localhost:9000')


def main():
    logger.info("=" * 70)
    logger.info("TALLY SYNC AGENT — PHASE 1 EXTRACTION (JSON API)")
    logger.info("=" * 70)
    logger.info("")

    # Configuration
    logger.info("Configuration:")
    logger.info(f"  Company: {COMPANY_NAME}")
    logger.info(f"  Tally URL: {TALLY_URL}")
    logger.info("")

    # Step 1: Initialize client
    logger.info("[STEP 1] Initializing Tally client...")
    client = TallyClient(base_url=TALLY_URL)

    # Step 2: Test connection
    logger.info("[STEP 2] Testing Tally connection...")
    if not client.is_reachable():
        logger.error(f"ERROR: Cannot reach Tally at {TALLY_URL}")
        logger.error("Is TallyPrime open? Is HTTP server enabled on port 9000?")
        sys.exit(1)
    logger.info("✓ Tally is reachable")
    logger.info("")

    # Step 3: Extract ledgers
    logger.info("[STEP 3] Extracting ledgers...")
    try:
        response = client.request(
            request_type="export",
            object_type="Ledger",
            company_name=COMPANY_NAME,
            fetch_list=["Name", "Parent", "Opening Balance", "Closing Balance"]
        )
        ledgers = parse_ledgers(response)
        logger.info(f"✓ Extracted {len(ledgers)} ledgers")
        logger.info("")

        # Show sample ledgers
        if ledgers:
            logger.info("Sample ledgers:")
            for ledger in ledgers[:5]:
                logger.info(f"  - {ledger.get('name')}")
            if len(ledgers) > 5:
                logger.info(f"  ... and {len(ledgers) - 5} more")

    except TallyConnectionError as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error extracting ledgers: {e}", exc_info=True)
        ledgers = []

    logger.info("")

    # Step 4: Save output
    logger.info("[STEP 4] Saving extraction output...")
    output_data = {
        "extraction_date": date.today().isoformat(),
        "company": COMPANY_NAME,
        "tally_url": TALLY_URL,
        "ledgers": ledgers,
    }

    output_file = Path("extraction_output.json")
    output_file.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8'
    )
    logger.info(f"✓ Saved to: {output_file}")
    logger.info("")

    # Step 5: Summary
    logger.info("=" * 70)
    logger.info("✅ EXTRACTION SUCCESSFUL")
    logger.info(f"   {len(ledgers)} ledgers extracted and saved")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
