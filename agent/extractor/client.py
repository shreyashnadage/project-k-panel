"""
Tally HTTP Client (JSON API)

Communicates with TallyPrime via JSON API.
Single-threaded: Tally HTTP server is serialized and cannot handle concurrent requests.
"""

import requests
import time
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

TALLY_URL = "http://localhost:9000"
DEFAULT_INTER_REQUEST_DELAY_MS = 500  # Minimum delay between requests to avoid Tally hangs
REQUEST_TIMEOUT_SECONDS = 30


class TallyClient:
    """
    HTTP client for TallyPrime JSON API.

    CRITICAL: Tally is single-threaded. This class must be used from a single thread only.
    Never call request() concurrently. Enforce inter-request delay to prevent Tally hangs.
    """

    def __init__(self, base_url: str = TALLY_URL, delay_ms: int = DEFAULT_INTER_REQUEST_DELAY_MS):
        self.base_url = base_url.rstrip('/')
        self.delay_ms = delay_ms
        self._last_request_at: float = 0

    def request(self, request_type: str, object_type: str, company_name: str,
                fetch_list: List[str], filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send a JSON request to Tally and return parsed response.

        Args:
            request_type: Type of request (e.g., "export", "action")
            object_type: Object to retrieve (e.g., "Ledger", "Voucher")
            company_name: Company name in Tally
            fetch_list: List of fields to fetch
            filters: Optional filters (not used in Phase 1)

        Returns:
            Parsed JSON response as dictionary

        Raises:
            TallyConnectionError: Cannot reach Tally on configured URL
            TallyTimeoutError: Tally did not respond within timeout
        """
        # Enforce inter-request delay to prevent overwhelming Tally
        elapsed_ms = (time.monotonic() - self._last_request_at) * 1000
        if elapsed_ms < self.delay_ms:
            time.sleep((self.delay_ms - elapsed_ms) / 1000)

        try:
            # Build request headers
            headers = {
                "content-type": "application/json",
                "version": "1",
                "tallyrequest": request_type,
                "type": "object",
                "subtype": object_type,
            }

            # Build request body
            payload = {
                "static_variables": [
                    {"name": "svExportFormat", "value": "jsonEx"},
                    {"name": "svCurrentCompany", "value": company_name}
                ],
                "fetch_list": fetch_list
            }

            # Serialize granular filters into Tally static variables.
            # Tally date format is YYYYMMDD; ISO dates are converted here.
            if filters:
                if "from_date" in filters:
                    payload["static_variables"].append(
                        {"name": "svFromDate", "value": filters["from_date"].replace("-", "")}
                    )
                if "to_date" in filters:
                    payload["static_variables"].append(
                        {"name": "svToDate", "value": filters["to_date"].replace("-", "")}
                    )
                if "voucher_type" in filters:
                    payload.setdefault("fetch_filters", []).append(
                        {"field": "VoucherTypeName", "value": filters["voucher_type"]}
                    )

            # Send request
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            self._last_request_at = time.monotonic()

            # Parse JSON response
            return response.json()

        except requests.exceptions.ConnectionError as e:
            raise TallyConnectionError(
                f"Cannot reach Tally at {self.base_url}. Is Tally open? Is HTTP enabled?"
            ) from e
        except requests.exceptions.Timeout as e:
            raise TallyTimeoutError(
                f"Tally request timed out after {REQUEST_TIMEOUT_SECONDS}s"
            ) from e
        except ValueError as e:
            raise TallyResponseError(
                f"Failed to parse Tally JSON response: {e}"
            ) from e

    def is_reachable(self) -> bool:
        """
        Test if Tally is running and responding on configured URL.

        Returns:
            True if Tally is reachable, False otherwise
        """
        try:
            # Send a minimal request to test connectivity
            self.request("export", "Ledger", "Bhrama Enterprises", ["Name"])
            return True
        except (TallyConnectionError, TallyTimeoutError, TallyResponseError):
            return False


class TallyConnectionError(Exception):
    """Raised when Tally is not reachable."""
    pass


class TallyTimeoutError(Exception):
    """Raised when Tally request times out."""
    pass


class TallyResponseError(Exception):
    """Raised when Tally response cannot be parsed."""
    pass
