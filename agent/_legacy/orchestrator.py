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
from agent.registration import get_registration

logger = logging.getLogger(__name__)

# Command types the agent will execute. Any type not in this set is rejected
# even if the cloud sends it, preventing server-side misconfiguration from
# triggering unintended actions on the client machine.
COMMAND_ALLOWLIST = {
    "sync_vouchers",
    "sync_vouchers_by_type",
    "sync_ledgers",
    "sync_full",
    "health_check",
}


class CommandExecutor:
    """
    Executes on-demand commands received from the cloud admin.

    Each command type maps to a specific Tally extraction. Results are
    transmitted immediately so the admin sees data as soon as the command
    completes rather than waiting for the next scheduled sync.
    """

    def __init__(self, orchestrator: "SyncOrchestrator"):
        self.orch = orchestrator

    def execute(self, command: dict) -> dict:
        """
        Dispatch and execute a single command dict from the cloud.

        Returns result dict: { records_synced, errors }
        Raises ValueError for unknown or disallowed command types.
        """
        cmd_type = command.get("command_type", "")
        params = command.get("params", {})

        if cmd_type not in COMMAND_ALLOWLIST:
            raise ValueError(f"Command type '{cmd_type}' is not in allowlist")

        logger.info(f"Executing command type={cmd_type} params={params}")

        if cmd_type == "health_check":
            reachable = self.orch.tally_client.is_reachable()
            return {"tally_reachable": reachable, "records_synced": 0, "errors": 0}

        if cmd_type == "sync_full":
            result = self.orch.run_once()
            return {
                "records_synced": result.get("transmitted", 0),
                "errors": result.get("errors", 0),
            }

        if cmd_type == "sync_ledgers":
            return self._sync_ledgers(params)

        if cmd_type in ("sync_vouchers", "sync_vouchers_by_type"):
            return self._sync_vouchers(params)

        raise ValueError(f"Unhandled command type: {cmd_type}")

    def _sync_ledgers(self, params: dict) -> dict:
        company_name = params.get("company_name", self.orch.tally_company_name)
        company_guid = params.get("company_guid", self.orch.tally_company_guid)

        ledgers = self.orch.tally_client.get_ledgers(company_name)

        for ledger in ledgers:
            self.orch.queue.enqueue_ledger({
                "company_guid": company_guid,
                "ledger_guid": ledger["guid"],
                "name": ledger["name"],
                "parent": ledger.get("parent"),
                "opening_balance": ledger.get("opening_balance"),
                "closing_balance": ledger.get("closing_balance"),
            })

        transmitted = self.orch._transmit_queued()
        return {"records_synced": transmitted, "errors": 0}

    def _sync_vouchers(self, params: dict) -> dict:
        from datetime import datetime, timedelta
        company_name = params.get("company_name", self.orch.tally_company_name)
        company_guid = params.get("company_guid", self.orch.tally_company_guid)

        today = datetime.now().date()
        from_date = params.get("from_date", (today - timedelta(days=30)).strftime("%Y%m%d"))
        to_date = params.get("to_date", today.strftime("%Y%m%d"))
        # Normalise: allow YYYY-MM-DD or YYYYMMDD
        from_date = from_date.replace("-", "")
        to_date = to_date.replace("-", "")

        vouchers = self.orch.tally_client.get_vouchers(company_name, from_date, to_date)

        for v in vouchers:
            self.orch.queue.enqueue_voucher({
                "company_guid": company_guid,
                "voucher_guid": v["id"],
                "voucher_type": v.get("voucher_type", ""),
                "voucher_number": v.get("voucher_number"),
                "date": v.get("date"),
                "party": v.get("party"),
                "amount": v.get("amount"),
            })

        transmitted = self.orch._transmit_queued()
        return {"records_synced": transmitted, "errors": 0}


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

        # Get registration info if available
        registration = get_registration()
        client_id = registration.get_client_id()
        device_id = registration.get_device_id()

        # Log registration status
        if client_id:
            logger.info(f"Agent registered as: {client_id}")
            logger.info(f"Device ID: {device_id}")
        else:
            logger.warning("Agent not registered - data will not be tagged with client_id")

        self.transmitter = TransmitterClient(
            base_url=cloud_api_url,
            api_key=cloud_api_key,
            tenant_id=cloud_tenant_id,
            client_id=client_id,
            device_id=device_id,
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
        logger.info("Extracting ledgers...")
        try:
            ledgers = self.tally_client.get_ledgers(self.tally_company_name)
            logger.info(f"✓ Extracted {len(ledgers)} ledgers")
            return ledgers
        except TallyConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise

    def _extract_vouchers(self) -> list:
        logger.info("Extracting vouchers...")
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        try:
            vouchers = self.tally_client.get_vouchers(
                company_name=self.tally_company_name,
                from_date=start_date.strftime("%Y%m%d"),
                to_date=end_date.strftime("%Y%m%d"),
            )
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

    def poll_and_execute_commands(self) -> int:
        """
        Poll cloud for admin commands and execute them immediately.

        Called from the service's command poller thread every 60s.
        Returns number of commands executed this cycle.
        """
        device_id = self.transmitter.device_id
        if not device_id:
            logger.debug("No device_id registered, skipping command poll")
            return 0

        commands = self.transmitter.get_pending_commands(device_id)
        if not commands:
            return 0

        logger.info(f"Received {len(commands)} command(s) from cloud")
        executor = CommandExecutor(self)
        executed = 0

        for cmd in commands:
            cmd_id = cmd["id"]
            try:
                result = executor.execute(cmd)
                self.transmitter.mark_command_done(cmd_id, result)
                logger.info(f"Command {cmd_id} completed: {result}")
                executed += 1
            except Exception as e:
                logger.error(f"Command {cmd_id} failed: {e}", exc_info=True)
                self.transmitter.mark_command_failed(cmd_id, str(e))

        return executed


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
