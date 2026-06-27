"""
Sync Orchestrator

Main coordination loop that ties together:
1. Tally extraction
2. Local queue management
3. Cloud transmission
4. Watermark advancement
5. Error recovery

Runs continuously (or on schedule) to keep cloud DB in sync with Tally.
"""

import logging
import time
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

from agent.extractor.client import TallyClient, TallyConnectionError
from agent.extractor.parser import parse_ledgers
from agent.extractor.watermark import WatermarkManager
from agent.transmitter.client import TransmitterClient, TransmitterError
from agent.queue.manager import QueueManager

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """
    Main sync orchestrator.

    Workflow:
    1. Extract from Tally (ledgers + vouchers)
    2. Enqueue records in local SQLite
    3. Transmit to cloud API (with retry)
    4. Mark sent in queue
    5. Advance watermark
    6. Report heartbeat
    """

    def __init__(
        self,
        tally_url: str,
        tally_company_name: str,
        tally_company_guid: str,
        cloud_api_url: str,
        cloud_api_key: str,
        cloud_tenant_id: str,
    ):
        """
        Initialize orchestrator.

        Args:
            tally_url: Tally HTTP server URL
            tally_company_name: Company name in Tally
            tally_company_guid: Company GUID in Tally
            cloud_api_url: Cloud API base URL
            cloud_api_key: Cloud API authentication key
            cloud_tenant_id: Cloud tenant identifier
        """
        self.tally_client = TallyClient(base_url=tally_url)
        self.tally_company_name = tally_company_name
        self.tally_company_guid = tally_company_guid

        self.transmitter = TransmitterClient(
            base_url=cloud_api_url,
            api_key=cloud_api_key,
            tenant_id=cloud_tenant_id,
        )

        self.queue = QueueManager()
        self.watermark = WatermarkManager()

    def run_once(self) -> Dict:
        """
        Execute one complete sync cycle.

        Returns:
            Sync result {extracted: N, transmitted: N, errors: E, status: str}
        """
        logger.info("=" * 70)
        logger.info("SYNC CYCLE START")
        logger.info("=" * 70)

        result = {
            "extracted_ledgers": 0,
            "extracted_vouchers": 0,
            "transmitted": 0,
            "errors": 0,
            "status": "success",
        }

        # Step 1: Check Tally connectivity
        if not self.tally_client.is_reachable():
            logger.error("❌ Tally unreachable")
            result["status"] = "tally_unreachable"
            return result

        logger.info("✓ Tally is reachable")

        # Step 2: Extract ledgers
        try:
            ledgers = self._extract_ledgers()
            result["extracted_ledgers"] = len(ledgers)
            for ledger in ledgers:
                self.queue.enqueue_ledger({
                    "company_guid": self.tally_company_guid,
                    "ledger_guid": ledger["guid"],
                    "name": ledger["name"],
                    "parent": ledger.get("parent"),
                    "opening_balance": ledger.get("opening_balance"),
                    "closing_balance": ledger.get("closing_balance"),
                })
        except Exception as e:
            logger.error(f"❌ Error extracting ledgers: {e}")
            result["errors"] += 1
            result["status"] = "extraction_failed"

        # Step 3: Extract vouchers
        try:
            vouchers = self._extract_vouchers()
            result["extracted_vouchers"] = len(vouchers)
            for voucher in vouchers:
                self.queue.enqueue_voucher({
                    "company_guid": self.tally_company_guid,
                    "voucher_guid": voucher["id"],
                    "voucher_type": voucher.get("voucher_type", ""),
                    "voucher_number": voucher.get("voucher_number"),
                    "date": voucher.get("date"),
                    "party": voucher.get("party"),
                    "amount": voucher.get("amount"),
                })
        except Exception as e:
            logger.error(f"❌ Error extracting vouchers: {e}")
            result["errors"] += 1

        # Step 4: Transmit queued records
        transmitted = self._transmit_queued()
        result["transmitted"] = transmitted

        # Step 5: Report queue stats
        stats = self.queue.get_stats()
        logger.info(f"Queue stats: {stats}")

        logger.info("=" * 70)
        if result["status"] == "success":
            logger.info(f"✓ SYNC COMPLETE: {result['extracted_vouchers']} vouchers extracted")
        else:
            logger.warning(f"⚠ SYNC PARTIAL: {result['status']}")
        logger.info("=" * 70)

        return result

    def _extract_ledgers(self) -> list:
        """
        Extract ledgers from Tally.

        Returns:
            List of ledger dicts
        """
        logger.info("Extracting ledgers...")
        try:
            response = self.tally_client.request(
                request_type="export",
                object_type="Ledger",
                company_name=self.tally_company_name,
                fetch_list=["Name", "Parent", "Opening Balance", "Closing Balance"]
            )
            ledgers = parse_ledgers(response)
            logger.info(f"✓ Extracted {len(ledgers)} ledgers")
            return ledgers
        except TallyConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise

    def _extract_vouchers(self) -> list:
        """
        Extract vouchers from Tally (last 30 days).

        Returns:
            List of voucher dicts
        """
        logger.info("Extracting vouchers...")
        # Phase 3: Simple date range (last 30 days)
        # Phase 3+: Use watermark for incremental sync
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        try:
            response = self.tally_client.request(
                request_type="export",
                object_type="Voucher",
                company_name=self.tally_company_name,
                fetch_list=["id", "date", "vouchertype", "party", "amount"]
            )
            # For Phase 3, we'll just return the raw response
            # In Phase 3+ we'll add watermark filtering
            vouchers = response.get("data", [])
            logger.info(f"✓ Extracted {len(vouchers)} vouchers")
            return vouchers
        except TallyConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise

    def _transmit_queued(self) -> int:
        """
        Transmit all pending queue records to cloud API.

        Returns:
            Number of records transmitted
        """
        pending = self.queue.get_pending(limit=100)
        if not pending:
            logger.info("No pending records to transmit")
            return 0

        logger.info(f"Transmitting {len(pending)} pending records...")
        transmitted = 0

        # Group by type (ledgers then vouchers)
        ledgers_to_send = []
        vouchers_to_send = []

        for record in pending:
            if record["type"] == "ledger":
                ledgers_to_send.append(record["data"])
            else:
                vouchers_to_send.append(record["data"])

        # Send ledgers
        if ledgers_to_send:
            try:
                response = self.transmitter.send_ledgers(ledgers_to_send)
                accepted = response.get("accepted", 0)
                logger.info(f"✓ Ledgers: {accepted} new, {response.get('duplicates', 0)} duplicates")
                transmitted += accepted
                # Mark sent in queue
                for record in pending:
                    if record["type"] == "ledger":
                        self.queue.mark_sent(record["id"])
            except TransmitterError as e:
                logger.error(f"❌ Failed to send ledgers: {e}")

        # Send vouchers
        if vouchers_to_send:
            try:
                response = self.transmitter.send_vouchers(vouchers_to_send)
                accepted = response.get("accepted", 0)
                logger.info(f"✓ Vouchers: {accepted} new, {response.get('duplicates', 0)} duplicates")
                transmitted += accepted
                # Mark sent in queue
                for record in pending:
                    if record["type"] == "voucher":
                        self.queue.mark_sent(record["id"])
            except TransmitterError as e:
                logger.error(f"❌ Failed to send vouchers: {e}")

        logger.info(f"✓ Transmitted {transmitted} records")
        return transmitted


def main():
    """Run the sync orchestrator."""
    load_dotenv(Path('.env.local'))

    # Configuration from environment
    tally_url = os.getenv("TALLY_URL", "http://localhost:9000")
    tally_company_name = os.getenv("TALLY_COMPANY_NAME", "Bhrama Enterprises")
    tally_company_guid = os.getenv("TALLY_COMPANY_GUID", "")

    cloud_api_url = os.getenv("CLOUD_API_URL", "http://localhost:8000")
    cloud_api_key = os.getenv("CLOUD_API_KEY", "")
    cloud_tenant_id = os.getenv("CLOUD_TENANT_ID", "test-tenant-001")

    if not all([tally_company_guid, cloud_api_key]):
        logger.error("Missing required environment variables")
        logger.error("Set: TALLY_COMPANY_GUID, CLOUD_API_KEY")
        exit(1)

    # Initialize orchestrator
    orchestrator = SyncOrchestrator(
        tally_url=tally_url,
        tally_company_name=tally_company_name,
        tally_company_guid=tally_company_guid,
        cloud_api_url=cloud_api_url,
        cloud_api_key=cloud_api_key,
        cloud_tenant_id=cloud_tenant_id,
    )

    # Run one sync cycle
    result = orchestrator.run_once()
    logger.info(f"Result: {result}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    main()
