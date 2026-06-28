"""
Cloud Telemetry Transmitter

Async transmission of telemetry events to cloud backend.
Handles batching, retries, and offline resilience.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any
from threading import Thread, Event as ThreadEvent
import time

from agent.telemetry.service import get_telemetry

logger = logging.getLogger(__name__)


class CloudTelemetryTransmitter:
    """
    Transmits telemetry events to cloud backend.

    Features:
    - Batch transmission (accumulates events before sending)
    - Exponential backoff retry (1s, 2s, 4s, 8s)
    - Async operation (non-blocking)
    - Offline resilience (events persist locally)
    - Idempotent (deduplication on server)
    """

    def __init__(
        self,
        cloud_api_url: str,
        cloud_api_key: str,
        batch_size: int = 100,
        batch_timeout_seconds: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize transmitter.

        Args:
            cloud_api_url: Cloud API base URL (e.g., http://15.206.90.21:8000)
            cloud_api_key: API key for authentication
            batch_size: Events to accumulate before sending
            batch_timeout_seconds: Max wait before sending partial batch
            max_retries: Max transmission attempts per event
        """
        self.cloud_api_url = cloud_api_url.rstrip("/")
        self.cloud_api_key = cloud_api_key
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.max_retries = max_retries

        # State
        self._shutdown = ThreadEvent()
        self._transmitter_thread = None
        self._running = False

    def start(self):
        """Start background transmission thread."""
        if self._running:
            logger.warning("Transmitter already running")
            return

        self._running = True
        self._shutdown.clear()
        self._transmitter_thread = Thread(target=self._transmission_loop, daemon=True)
        self._transmitter_thread.start()
        logger.info("Telemetry transmitter started")

    def stop(self):
        """Stop background transmission thread."""
        if not self._running:
            return

        self._running = False
        self._shutdown.set()

        # Wait for thread to finish
        if self._transmitter_thread:
            self._transmitter_thread.join(timeout=5)

        logger.info("Telemetry transmitter stopped")

    def _transmission_loop(self):
        """Main transmission loop (runs in background thread)."""
        while self._running:
            try:
                # Get pending events
                telemetry = get_telemetry()
                events = telemetry.get_untransmitted_events(limit=self.batch_size)

                if events:
                    # Prepare batch
                    batch = self._prepare_batch(events)

                    # Transmit
                    success = self._transmit_batch(batch)

                    if success:
                        # Mark as transmitted
                        event_ids = [e["event_id"] for e in events]
                        telemetry.mark_transmitted(event_ids)
                        logger.debug(f"Transmitted {len(event_ids)} telemetry events")

                # Sleep before next batch
                self._shutdown.wait(timeout=self.batch_timeout_seconds)

            except Exception as e:
                logger.error(f"Error in transmission loop: {e}")
                # Wait before retrying
                self._shutdown.wait(timeout=5)

    def _prepare_batch(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare batch for transmission.

        Args:
            events: List of event dictionaries from storage

        Returns:
            Batch dictionary ready for JSON serialization
        """
        # Parse data field (it's stored as JSON string)
        prepared_events = []
        for event in events:
            try:
                if isinstance(event.get("data"), str):
                    event["data"] = json.loads(event["data"])
            except:
                pass
            prepared_events.append(event)

        return {
            "events": prepared_events,
        }

    def _transmit_batch(self, batch: Dict[str, Any]) -> bool:
        """
        Transmit batch to cloud API.

        Args:
            batch: Batch dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            import requests

            # Prepare request
            url = f"{self.cloud_api_url}/v1/telemetry/events"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.cloud_api_key,
            }
            body = json.dumps(batch)

            # Retry with exponential backoff
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = requests.post(
                        url,
                        data=body,
                        headers=headers,
                        timeout=10,
                    )

                    if response.status_code == 200:
                        return True

                    elif response.status_code >= 400 and response.status_code < 500:
                        # Client error (4xx) - don't retry
                        logger.error(f"Cloud API client error: {response.status_code}")
                        return False

                    else:
                        # Server error (5xx) - retry
                        logger.warning(f"Cloud API error {response.status_code}, retrying...")

                except requests.ConnectionError as e:
                    logger.warning(f"Connection error to cloud API: {e}")

                except requests.Timeout:
                    logger.warning("Timeout connecting to cloud API")

                except Exception as e:
                    logger.error(f"Unexpected error in transmission: {e}")

                # Wait before retry (exponential backoff)
                if attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)  # 1, 2, 4, 8 seconds
                    logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

            logger.error(f"Failed to transmit batch after {self.max_retries} attempts")
            return False

        except ImportError:
            logger.error("requests library required for telemetry transmission")
            return False

        except Exception as e:
            logger.error(f"Fatal error in transmission: {e}")
            return False


# Global transmitter instance
_transmitter: CloudTelemetryTransmitter = None


def initialize_transmitter(
    cloud_api_url: str,
    cloud_api_key: str,
    batch_size: int = 100,
    batch_timeout_seconds: int = 5,
) -> CloudTelemetryTransmitter:
    """
    Initialize global cloud transmitter.

    Args:
        cloud_api_url: Cloud API URL
        cloud_api_key: API key
        batch_size: Batch size
        batch_timeout_seconds: Batch timeout

    Returns:
        CloudTelemetryTransmitter instance
    """
    global _transmitter

    if _transmitter is None:
        _transmitter = CloudTelemetryTransmitter(
            cloud_api_url=cloud_api_url,
            cloud_api_key=cloud_api_key,
            batch_size=batch_size,
            batch_timeout_seconds=batch_timeout_seconds,
        )

    return _transmitter


def get_transmitter() -> CloudTelemetryTransmitter:
    """Get global transmitter instance."""
    global _transmitter

    if _transmitter is None:
        raise RuntimeError("Transmitter not initialized. Call initialize_transmitter() first.")

    return _transmitter
