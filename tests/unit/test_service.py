"""
Unit tests for Windows Service Wrapper (TallySyncService)
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from agent.service.windows_service import TallySyncService


class TestTallySyncService:
    """Test suite for TallySyncService"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for service logs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Remove and close handlers to release the file lock
        from agent.service.windows_service import logger as service_logger
        handlers = list(service_logger.handlers)
        for h in handlers:
            h.close()
            service_logger.removeHandler(h)
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_log_dir):
        """Test service initialization and default settings"""
        service = TallySyncService(sync_interval_hours=2, log_dir=temp_log_dir)
        assert service.sync_interval_hours == 2
        assert service.sync_interval_seconds == 2 * 3600
        assert service.running is False
        assert service.next_sync_time is None

    def test_get_status(self, temp_log_dir):
        """Test status reporting before start"""
        service = TallySyncService(sync_interval_hours=4, log_dir=temp_log_dir)
        status = service.get_status()
        assert status["running"] is False
        assert status["sync_interval_hours"] == 4
        assert status["next_sync"] is None
        assert "tally_sync_service.log" in status["log_file"]

    @patch("agent.service.windows_service.SyncOrchestrator")
    def test_run_sync_cycle_success(self, mock_orchestrator_cls, temp_log_dir):
        """Test that a sync cycle runs successfully and invokes the orchestrator"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_once.return_value = {"status": "success", "ledgers": 5, "vouchers": 10}
        mock_orchestrator_cls.return_value = mock_orchestrator

        service = TallySyncService(sync_interval_hours=6, log_dir=temp_log_dir)
        
        # Run sync cycle
        with patch.dict("os.environ", {
            "TALLY_URL": "http://localhost:9000",
            "TALLY_COMPANY_NAME": "Bhrama Enterprises",
            "TALLY_COMPANY_GUID": "COMP-001",
            "CLOUD_API_URL": "http://localhost:8000",
            "CLOUD_API_KEY": "test-key",
            "CLOUD_TENANT_ID": "tenant-001"
        }):
            service._run_sync_cycle()

        # Check that orchestrator was initialized and run_once was called
        mock_orchestrator_cls.assert_called_once_with(
            tally_url="http://localhost:9000",
            tally_company_name="Bhrama Enterprises",
            tally_company_guid="COMP-001",
            cloud_api_url="http://localhost:8000",
            cloud_api_key="test-key",
            cloud_tenant_id="tenant-001"
        )
        mock_orchestrator.run_once.assert_called_once()

    @patch("agent.service.windows_service.SyncOrchestrator")
    def test_run_sync_cycle_handles_exception(self, mock_orchestrator_cls, temp_log_dir):
        """Test that sync cycle handles exceptions without crashing the service"""
        mock_orchestrator_cls.side_effect = Exception("Connection refused")

        service = TallySyncService(sync_interval_hours=6, log_dir=temp_log_dir)
        
        # This should not raise an exception
        service._run_sync_cycle()
        
        # Verify it attempted to initialize
        mock_orchestrator_cls.assert_called_once()
