"""
Watermark & State Management

Tracks the last successfully synced date range per (company_guid, entity_type).
Uses date-based watermarks for Phase 1-3 (simple incremental sync).
Will be upgraded to ALTERID-based watermarks in Phase 3 for full incremental support.
"""

import json
import logging
from pathlib import Path
from datetime import date, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

STATE_FILE = Path("sync_state.json")


class WatermarkManager:
    """
    Manages extraction watermarks: the last successfully synced date/state.

    On first run, syncs from 1 year ago. On subsequent runs, syncs from last
    successful sync date to today. Call advance() only after successful
    cloud delivery to persist the watermark.
    """

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self._state = self._load()

    def _load(self) -> Dict[str, str]:
        """Load watermark state from file, return empty dict if not found."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.error(f"Failed to load watermark state: {e}")
                return {}
        return {}

    def _save(self):
        """Persist current state to file."""
        try:
            self.state_file.write_text(
                json.dumps(self._state, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Failed to save watermark state: {e}")

    def get_last_synced_date(self, company_guid: str, entity: str) -> date:
        """
        Get the start date for the next sync window.

        For initial sync (no watermark found), returns date from 1 year ago.
        For subsequent syncs, returns the day after the last successful sync.

        Args:
            company_guid: Tally company unique identifier
            entity: Entity type ('vouchers', 'ledgers')

        Returns:
            Date to start syncing from (inclusive)
        """
        key = f"{company_guid}:{entity}"
        if key in self._state:
            try:
                last_date = date.fromisoformat(self._state[key])
                # Start from next day after last sync
                return last_date + timedelta(days=1)
            except ValueError as e:
                logger.error(f"Invalid watermark date for {key}: {e}")
                return date.today() - timedelta(days=365)

        # First sync: go back 1 year
        logger.info(f"No watermark found for {key}, starting from 1 year ago")
        return date.today() - timedelta(days=365)

    def advance(self, company_guid: str, entity: str, synced_through: date):
        """
        Advance watermark after successful sync.

        Call this only after records have been successfully delivered to cloud.
        This marks that we've synced up through synced_through date (inclusive).

        Args:
            company_guid: Tally company unique identifier
            entity: Entity type ('vouchers', 'ledgers')
            synced_through: Last date that was successfully synced (inclusive)
        """
        key = f"{company_guid}:{entity}"
        self._state[key] = synced_through.isoformat()
        self._save()
        logger.info(f"Advanced watermark for {key}: {synced_through}")

    def reset(self, company_guid: str, entity: str):
        """
        Reset watermark to start from 1 year ago (for debugging).

        Use carefully - will cause re-extraction of old data.
        """
        key = f"{company_guid}:{entity}"
        if key in self._state:
            del self._state[key]
            self._save()
            logger.warning(f"Reset watermark for {key}")

    def get_state(self) -> Dict[str, str]:
        """Get current watermark state (for debugging/inspection)."""
        return self._state.copy()
