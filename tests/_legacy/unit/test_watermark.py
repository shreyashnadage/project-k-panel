"""
Unit tests for watermark/state management

Tests use temporary files (no side effects on real state).
"""

import pytest
import json
from pathlib import Path
from datetime import date, timedelta
from agent.extractor.watermark import WatermarkManager
import tempfile


class TestWatermarkManager:
    """Test watermark tracking"""

    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield Path(f.name)
        # Cleanup
        if Path(f.name).exists():
            Path(f.name).unlink()

    def test_initialization_no_file(self, temp_state_file):
        """Watermark manager initializes with no file"""
        manager = WatermarkManager(temp_state_file)
        assert manager._state == {}

    def test_get_last_synced_date_initial_sync(self, temp_state_file):
        """Initial sync returns date from 1 year ago"""
        manager = WatermarkManager(temp_state_file)
        result = manager.get_last_synced_date("COMP-001", "vouchers")

        expected = date.today() - timedelta(days=365)
        assert result == expected

    def test_advance_watermark(self, temp_state_file):
        """Advancing watermark persists to file"""
        manager = WatermarkManager(temp_state_file)
        sync_date = date(2026, 6, 1)

        manager.advance("COMP-001", "vouchers", sync_date)

        # Verify persisted
        assert temp_state_file.exists()
        data = json.loads(temp_state_file.read_text(encoding='utf-8'))
        assert data["COMP-001:vouchers"] == "2026-06-01"

    def test_get_last_synced_after_advance(self, temp_state_file):
        """After advance, get_last_synced_date returns next day"""
        manager = WatermarkManager(temp_state_file)
        sync_date = date(2026, 6, 1)

        manager.advance("COMP-001", "vouchers", sync_date)

        # Next sync should start from next day
        next_start = manager.get_last_synced_date("COMP-001", "vouchers")
        assert next_start == date(2026, 6, 2)

    def test_multiple_companies_tracked_separately(self, temp_state_file):
        """Different companies have separate watermarks"""
        manager = WatermarkManager(temp_state_file)

        manager.advance("COMP-001", "vouchers", date(2026, 6, 1))
        manager.advance("COMP-002", "vouchers", date(2026, 5, 15))

        # Each should have independent watermark
        next_001 = manager.get_last_synced_date("COMP-001", "vouchers")
        next_002 = manager.get_last_synced_date("COMP-002", "vouchers")

        assert next_001 == date(2026, 6, 2)
        assert next_002 == date(2026, 5, 16)

    def test_multiple_entities_tracked_separately(self, temp_state_file):
        """Different entity types (vouchers, ledgers) have separate watermarks"""
        manager = WatermarkManager(temp_state_file)

        manager.advance("COMP-001", "vouchers", date(2026, 6, 1))
        manager.advance("COMP-001", "ledgers", date(2026, 5, 1))

        next_vouchers = manager.get_last_synced_date("COMP-001", "vouchers")
        next_ledgers = manager.get_last_synced_date("COMP-001", "ledgers")

        assert next_vouchers == date(2026, 6, 2)
        assert next_ledgers == date(2026, 5, 2)

    def test_load_existing_state(self, temp_state_file):
        """Watermark manager loads existing state from file"""
        # Create initial state
        initial_state = {
            "COMP-001:vouchers": "2026-06-01",
            "COMP-001:ledgers": "2026-05-15",
        }
        temp_state_file.write_text(json.dumps(initial_state), encoding='utf-8')

        # Load
        manager = WatermarkManager(temp_state_file)
        assert manager.get_state() == initial_state

    def test_reset_watermark(self, temp_state_file):
        """Reset removes watermark (returns to initial sync)"""
        manager = WatermarkManager(temp_state_file)
        manager.advance("COMP-001", "vouchers", date(2026, 6, 1))

        # Verify it's set
        assert manager.get_last_synced_date("COMP-001", "vouchers") == date(2026, 6, 2)

        # Reset
        manager.reset("COMP-001", "vouchers")

        # Should go back to 1 year ago
        result = manager.get_last_synced_date("COMP-001", "vouchers")
        expected = date.today() - timedelta(days=365)
        assert result == expected

    def test_corrupted_state_file_ignored(self, temp_state_file):
        """Corrupted state file is ignored, starts fresh"""
        # Write invalid JSON
        temp_state_file.write_text("{invalid json", encoding='utf-8')

        # Should not raise, just start fresh
        manager = WatermarkManager(temp_state_file)
        assert manager.get_state() == {}

    def test_get_state_returns_copy(self, temp_state_file):
        """get_state() returns a copy, not reference"""
        manager = WatermarkManager(temp_state_file)
        manager.advance("COMP-001", "vouchers", date(2026, 6, 1))

        state = manager.get_state()
        # Modify returned state (shouldn't affect manager)
        state["COMP-002:vouchers"] = "2026-01-01"

        # Manager should not be affected
        assert "COMP-002:vouchers" not in manager.get_state()

    def test_watermark_persistence_across_instances(self, temp_state_file):
        """Watermark persists across different manager instances"""
        # Instance 1: Set watermark
        manager1 = WatermarkManager(temp_state_file)
        manager1.advance("COMP-001", "vouchers", date(2026, 6, 15))

        # Instance 2: Load same file
        manager2 = WatermarkManager(temp_state_file)
        result = manager2.get_last_synced_date("COMP-001", "vouchers")

        # Should have loaded the watermark from file
        assert result == date(2026, 6, 16)
