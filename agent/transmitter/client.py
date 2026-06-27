"""
Cloud API Transmitter Client

POSTs extracted ledgers and vouchers to the cloud ingest API.
Handles retries, error recovery, and heartbeat reporting.
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TransmitterClient:
    """
    HTTP client for posting data to cloud ingest API.
    Handles authentication, retries, and graceful failure.
    """

    def __init__(self, base_url: str, api_key: str, tenant_id: str, max_retries: int = 3):
        """
        Initialize transmitter client.

        Args:
            base_url: Cloud API base URL (e.g., http://localhost:8000)
            api_key: API key for authentication
            tenant_id: Tenant ID in cloud system
            max_retries: Number of retry attempts on failure
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.max_retries = max_retries
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }

    def send_ledgers(self, ledgers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST ledgers to cloud API.

        Args:
            ledgers: List of ledger dicts from parser

        Returns:
            API response {accepted, duplicates, errors, message}

        Raises:
            TransmitterError: If all retries exhausted
        """
        if not ledgers:
            logger.debug("No ledgers to send")
            return {"accepted": 0, "duplicates": 0, "errors": 0, "message": "No ledgers"}

        payload = {
            "tenant_id": self.tenant_id,
            "ledgers": ledgers,
        }

        return self._post_with_retries("/v1/ledgers", payload)

    def send_vouchers(self, vouchers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        POST vouchers to cloud API.

        Args:
            vouchers: List of voucher dicts from parser

        Returns:
            API response {accepted, duplicates, errors, message}

        Raises:
            TransmitterError: If all retries exhausted
        """
        if not vouchers:
            logger.debug("No vouchers to send")
            return {"accepted": 0, "duplicates": 0, "errors": 0, "message": "No vouchers"}

        payload = {
            "tenant_id": self.tenant_id,
            "vouchers": vouchers,
        }

        return self._post_with_retries("/v1/vouchers", payload)

    def _post_with_retries(self, endpoint: str, payload: Dict) -> Dict[str, Any]:
        """
        POST to endpoint with exponential backoff retry.

        Args:
            endpoint: API endpoint (e.g., /v1/vouchers)
            payload: Request body

        Returns:
            Parsed JSON response

        Raises:
            TransmitterError: If all retries exhausted
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self.headers,
                    timeout=30,
                )

                # Success (2xx)
                if 200 <= response.status_code < 300:
                    logger.info(
                        f"✓ {endpoint}: {response.json()['message']}"
                    )
                    return response.json()

                # Client error (4xx) — don't retry
                if 400 <= response.status_code < 500:
                    error_msg = response.json().get("detail", response.text)
                    raise TransmitterError(
                        f"Client error ({response.status_code}): {error_msg}"
                    )

                # Server error (5xx) — retry
                if 500 <= response.status_code < 600:
                    raise TransmitterError(
                        f"Server error ({response.status_code}): {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(
                    f"[Attempt {attempt + 1}/{self.max_retries}] "
                    f"{endpoint}: {type(e).__name__}: {e}"
                )

                # Exponential backoff: 1s, 2s, 4s
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                    continue

            except TransmitterError as e:
                logger.error(f"{endpoint}: {e}")
                raise

        # All retries exhausted
        raise TransmitterError(
            f"{endpoint}: Max retries ({self.max_retries}) exhausted. "
            f"Last error: {last_error}"
        )

    def is_healthy(self) -> bool:
        """
        Check if cloud API is reachable.

        Returns:
            True if health check passes, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5,
                headers={"x-api-key": self.api_key},
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


class TransmitterError(Exception):
    """Raised when transmission fails."""
    pass
