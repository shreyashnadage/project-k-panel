"""
Unit tests for Tally HTTP client (JSON API version)

Uses mocked HTTP responses (no live Tally connection needed).
"""

import pytest
from unittest.mock import Mock, patch
from agent.extractor.client import (
    TallyClient,
    TallyConnectionError,
    TallyTimeoutError,
    TallyResponseError,
)
import requests


SAMPLE_JSON_RESPONSE = {"data": [{"Name": "Cash", "Parent": "Cash-in-hand"}]}


class TestTallyClient:
    """Test Tally HTTP client"""

    def test_client_initialization(self):
        """Client initializes with correct defaults"""
        client = TallyClient()
        assert client.base_url == "http://localhost:9000"
        assert client.delay_ms == 500

    def test_client_custom_url(self):
        """Client accepts custom Tally URL"""
        client = TallyClient(base_url="http://192.168.1.100:9000")
        assert client.base_url == "http://192.168.1.100:9000"

    @patch('agent.extractor.client.requests.post')
    def test_successful_request(self, mock_post):
        """Successful request returns parsed JSON response"""
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_JSON_RESPONSE
        mock_post.return_value = mock_response

        client = TallyClient()
        result = client.request("export", "Ledger", "Test Company", ["Name", "Parent"])

        assert result == SAMPLE_JSON_RESPONSE
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['headers']['tallyrequest'] == 'export'
        assert call_args[1]['headers']['subtype'] == 'Ledger'
        assert call_args[1]['json']['static_variables'][1]['value'] == 'Test Company'

    @patch('agent.extractor.client.requests.post')
    def test_request_enforces_delay(self, mock_post):
        """Requests are delayed to avoid overwhelming Tally"""
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_JSON_RESPONSE
        mock_post.return_value = mock_response

        client = TallyClient(delay_ms=100)
        import time
        start = time.monotonic()
        client.request("export", "Ledger", "Test Company", ["Name"])
        # Second request should be delayed
        client.request("export", "Ledger", "Test Company", ["Name"])
        elapsed = (time.monotonic() - start) * 1000

        # Should take at least ~100ms (allow 20ms margin for system variance)
        assert elapsed >= 80

    @patch('agent.extractor.client.requests.post')
    def test_connection_error_raises_exception(self, mock_post):
        """Connection error is raised as TallyConnectionError"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = TallyClient()
        with pytest.raises(TallyConnectionError):
            client.request("export", "Ledger", "Test Company", ["Name"])

    @patch('agent.extractor.client.requests.post')
    def test_timeout_error_raises_exception(self, mock_post):
        """Timeout error is raised as TallyTimeoutError"""
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")

        client = TallyClient()
        with pytest.raises(TallyTimeoutError):
            client.request("export", "Ledger", "Test Company", ["Name"])

    @patch('agent.extractor.client.requests.post')
    def test_response_decode_error_raises_exception(self, mock_post):
        """Invalid JSON response raises TallyResponseError"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_post.return_value = mock_response

        client = TallyClient()
        with pytest.raises(TallyResponseError):
            client.request("export", "Ledger", "Test Company", ["Name"])

    @patch('agent.extractor.client.requests.post')
    def test_is_reachable_returns_true_when_responsive(self, mock_post):
        """is_reachable() returns True when Tally responds"""
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_JSON_RESPONSE
        mock_post.return_value = mock_response

        client = TallyClient()
        assert client.is_reachable() is True

    @patch('agent.extractor.client.requests.post')
    def test_is_reachable_returns_false_when_unreachable(self, mock_post):
        """is_reachable() returns False when Tally is down"""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        client = TallyClient()
        assert client.is_reachable() is False

    @patch('agent.extractor.client.requests.post')
    def test_is_reachable_returns_false_on_timeout(self, mock_post):
        """is_reachable() returns False on timeout"""
        mock_post.side_effect = requests.exceptions.Timeout()

        client = TallyClient()
        assert client.is_reachable() is False

    @patch('agent.extractor.client.requests.post')
    def test_multiple_requests_serialize(self, mock_post):
        """Multiple requests are serialized (not concurrent)"""
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_JSON_RESPONSE
        mock_post.return_value = mock_response

        client = TallyClient()
        client.request("export", "Ledger", "Test Company", ["Name"])
        client.request("export", "Ledger", "Test Company", ["Name"])
        client.request("export", "Ledger", "Test Company", ["Name"])

        assert mock_post.call_count == 3

    def test_url_trailing_slash_stripped(self):
        """Trailing slashes in URL are normalized"""
        client = TallyClient(base_url="http://localhost:9000/")
        assert client.base_url == "http://localhost:9000"
