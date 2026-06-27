#!/usr/bin/env python3
"""
Phase 1: Manual Tally Extraction Script

PURPOSE: Development/testing. Run this to validate extraction from your Tally instance.
This script is NOT the final agent - it's a test harness for Phase 1.

USAGE:
    python run_extraction.py

PREREQUISITES:
    - TallyPrime running with HTTP server enabled on localhost:9000
    - Test company created in Tally
    - Environment variables or .env.local configured with Tally details

OUTPUT:
    - extraction_output.json: All extracted vouchers in JSON format
    - sync_state.json: Watermark tracking which dates were synced
"""

import json
import logging
import sys
import os
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv

from agent.extractor.client import TallyClient, TallyConnectionError
from agent.extractor.parser import parse_vouchers
from agent.extractor.watermark import WatermarkManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env.local
load_dotenv(Path('.env.local'))

# Configuration from environment
COMPANY_NAME = os.getenv('TALLY_COMPANY_NAME', 'Sharma Traders Pvt Ltd')
COMPANY_GUID = os.getenv('TALLY_COMPANY_GUID', 'unknown')
TALLY_URL = os.getenv('TALLY_URL', 'http://localhost:9000')


def load_tdml_template(template_name: str) -> str:
    """Load TDML request template from file."""
    template_path = Path(f"agent/extractor/tdml_templates/{template_name}")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding='utf-8')


def main():
    logger.info("=" * 70)
    logger.info("TALLY SYNC AGENT — PHASE 1 EXTRACTION TEST")
    logger.info("=" * 70)
    logger.info("")

    # Configuration
    logger.info("Configuration:")
    logger.info(f"  Company: {COMPANY_NAME}")
    logger.info(f"  Company GUID: {COMPANY_GUID}")
    logger.info(f"  Tally URL: {TALLY_URL}")
    logger.info("")

    # Step 1: Initialize client
    logger.info("[STEP 1] Initializing Tally client...")
    client = TallyClient(base_url=TALLY_URL)

    # Step 2: Test connection
    logger.info("[STEP 2] Testing Tally connection...")
    if not client.is_reachable():
        logger.error("ERROR: Cannot reach Tally at {TALLY_URL}")
        logger.error("Is TallyPrime open? Is HTTP server enabled on port 9000?")
        sys.exit(1)
    logger.info("✓ Tally is reachable")
    logger.info("")

    # Step 3: Determine sync window
    logger.info("[STEP 3] Determining sync window...")
    watermark = WatermarkManager()
    from_date = watermark.get_last_synced_date(COMPANY_GUID, "vouchers")
    to_date = date.today()

    logger.info(f"  Syncing from {from_date} to {to_date}")
    if from_date == to_date:
        logger.warning("  ⚠ No new data to sync (from_date == to_date)")
    logger.info("")

    # Step 4: Extract vouchers
    logger.info("[STEP 4] Extracting vouchers...")
    all_vouchers = []
    cursor = from_date

    while cursor < to_date:
        chunk_end = min(cursor + timedelta(days=30), to_date)
        logger.info(f"  Extracting {cursor} → {chunk_end}...")

        try:
            # Load and render template
            template = load_tdml_template("vouchers_tp3.xml")
            tdml = template.format(
                company_name=COMPANY_NAME,
                from_date=cursor.strftime("%Y%m%d"),
                to_date=chunk_end.strftime("%Y%m%d"),
            )

            # Send request
            raw_xml = client.request(tdml)

            # Parse response
            vouchers = parse_vouchers(raw_xml)
            all_vouchers.extend(vouchers)
            logger.info(f"    ✓ Extracted {len(vouchers)} vouchers")

        except TallyConnectionError as e:
            logger.error(f"  ERROR: Tally connection lost: {e}")
            logger.error("  Pausing sync - will resume on next run")
            break
        except Exception as e:
            logger.error(f"  ERROR: {e}", exc_info=True)
            break

        cursor = chunk_end + timedelta(days=1)

    logger.info(f"✓ Total extracted: {len(all_vouchers)} vouchers")
    logger.info("")

    # Step 5: Save extraction output
    logger.info("[STEP 5] Saving extraction output...")
    output_file = Path("extraction_output.json")
    output_file.write_text(
        json.dumps(all_vouchers, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8'
    )
    logger.info(f"✓ Saved to: {output_file}")
    logger.info("")

    # Step 6: Analysis
    logger.info("[STEP 6] Analysis:")
    if all_vouchers:
        voucher_types = {}
        for v in all_vouchers:
            vtype = v.get('voucher_type', 'Unknown')
            voucher_types[vtype] = voucher_types.get(vtype, 0) + 1

        logger.info(f"  Voucher types found:")
        for vtype, count in sorted(voucher_types.items()):
            logger.info(f"    - {vtype}: {count}")

        dates = [v.get('date') for v in all_vouchers if v.get('date')]
        if dates:
            logger.info(f"  Date range: {min(dates)} → {max(dates)}")

        # Check for Unicode names
        non_ascii_names = []
        for v in all_vouchers:
            party = v.get('party_ledger_name', '')
            if party and any(ord(c) > 127 for c in party):
                non_ascii_names.append(party)

        if non_ascii_names:
            logger.info(f"  Non-ASCII party names found: {len(set(non_ascii_names))}")
            logger.info(f"    Examples: {list(set(non_ascii_names))[:3]}")

    logger.info("")

    # Step 7: Validation
    logger.info("[STEP 7] Validation:")
    logger.info("  Compare extraction_output.json with Tally:")
    logger.info("    1. Open Tally → Gateway → Voucher Register")
    logger.info(f"    2. Filter by date: {from_date} to {to_date}")
    logger.info("    3. Count total vouchers")
    logger.info(f"    4. Compare with extracted count: {len(all_vouchers)}")
    logger.info("")

    # Step 8: Update watermark (optional)
    if all_vouchers:
        logger.info("[STEP 8] Update watermark (for next sync)")
        logger.info(f"  Current watermark: {watermark.get_state()}")
        logger.info(f"  To advance watermark to {to_date}, run:")
        logger.info(f"    watermark.advance('{COMPANY_GUID}', 'vouchers', date('{to_date}'))")
        logger.info("")

    # Summary
    logger.info("=" * 70)
    if all_vouchers:
        logger.info("✅ EXTRACTION SUCCESSFUL")
        logger.info(f"   {len(all_vouchers)} vouchers extracted and saved")
    else:
        logger.warning("⚠️  No vouchers extracted (may be normal if no data in period)")
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
