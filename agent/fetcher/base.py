# -*- coding: utf-8 -*-
"""
TallyHTTPClient — raw JSON API client for TallyPrime 3.x/4.x

API shape (confirmed working):
  Headers: Content-Type=application/json, version=1, tallyrequest=export,
           type=collection|object, subtype=Ledger|Voucher|..., id=<must match subtype>
  Body:    { static_variables: [{name, value}], fetch_list: [...] }
  Response: { status: "1", data: { collection: [...] } }

CRITICAL: Tally is single-threaded. Never send concurrent requests.
          TallyAPIConnectorV1.0.exe must be running before any call.
"""

import time
import logging
import threading
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

TALLY_URL = "http://localhost:9000"
REQUEST_TIMEOUT = 30          # seconds
INTER_REQUEST_DELAY = 0.5     # seconds between requests


class TallyAPIError(Exception):
    pass

class TallyConnectionError(TallyAPIError):
    pass

class TallyTimeoutError(TallyAPIError):
    pass

class TallyResponseError(TallyAPIError):
    pass


class TallyHTTPClient:
    """
    Low-level HTTP client for the TallyPrime JSON API.

    One instance should be shared across all fetchers — it holds the
    inter-request lock that prevents concurrent Tally calls.
    """

    def __init__(self, base_url: str = TALLY_URL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._lock = threading.Lock()       # enforces single-threaded access
        self._last_call_at: float = 0.0

    # ── Public methods ────────────────────────────────────────────────────────

    def export_collection(
        self,
        subtype: str,
        fetch_list: List[str],
        company: Optional[str] = None,
        extra_static_vars: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all objects of a given subtype from Tally.

        id MUST equal subtype — any other value causes Tally to hang.
        """
        static_vars = self._base_static_vars(company)
        if extra_static_vars:
            static_vars.extend(extra_static_vars)

        resp = self._post(
            headers=self._headers(tallyrequest="export", type_="collection",
                                  subtype=subtype, id_=subtype),
            body={"static_variables": static_vars, "fetch_list": fetch_list},
        )
        return self._extract_collection(resp, subtype)

    def export_object(
        self,
        subtype: str,
        name: str,
        fetch_list: List[str],
        company: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single named object (e.g. one ledger by name)."""
        resp = self._post(
            headers=self._headers(tallyrequest="export", type_="object",
                                  subtype=subtype, id_=name),
            body={
                "static_variables": self._base_static_vars(company),
                "fetch_list": fetch_list,
            },
        )
        msgs = resp.get("tallymessage", [])
        return msgs[0] if msgs else None

    def is_ready(self) -> bool:
        """Quick HTTP-level health check — returns True if Tally responds."""
        xml = (
            "<ENVELOPE><HEADER><VERSION>1</VERSION>"
            "<TALLYREQUEST>Export</TALLYREQUEST>"
            "<TYPE>Data</TYPE><ID>Trial Balance</ID></HEADER>"
            "<BODY><DESC><STATICVARIABLES>"
            "<SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>"
            "</STATICVARIABLES></DESC></BODY></ENVELOPE>"
        )
        try:
            r = requests.post(
                self.base_url,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
                timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _headers(self, tallyrequest: str, type_: str,
                 subtype: str, id_: str) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "version": "1",
            "tallyrequest": tallyrequest,
            "type": type_,
            "subtype": subtype,
            "id": id_,
        }

    def _base_static_vars(self, company: Optional[str]) -> List[Dict]:
        vars_ = [{"name": "svExportFormat", "value": "jsonEx"}]
        if company:
            vars_.append({"name": "svCurrentCompany", "value": company})
        return vars_

    def _post(self, headers: Dict, body: Dict) -> Dict[str, Any]:
        with self._lock:
            self._throttle()
            try:
                resp = requests.post(
                    self.base_url,
                    headers=headers,
                    json=body,
                    timeout=self.timeout,
                )
                self._last_call_at = time.monotonic()
            except requests.exceptions.ConnectionError as e:
                raise TallyConnectionError(
                    f"Cannot connect to Tally at {self.base_url}. "
                    "Is TallyPrime open and TallyAPIConnectorV1.0.exe running?"
                ) from e
            except requests.exceptions.Timeout as e:
                raise TallyTimeoutError(
                    f"Tally did not respond in {self.timeout}s. "
                    "Another request may be in flight (Tally is single-threaded)."
                ) from e

        if resp.status_code != 200:
            raise TallyResponseError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
        except Exception as e:
            raise TallyResponseError(f"Non-JSON response: {resp.text[:300]}") from e

        if str(data.get("status")) != "1":
            errs = data.get("error_list", data.get("error", data))
            raise TallyResponseError(f"Tally error: {errs}")

        return data

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call_at
        if elapsed < INTER_REQUEST_DELAY:
            time.sleep(INTER_REQUEST_DELAY - elapsed)

    def _extract_collection(self, resp: Dict, label: str) -> List[Dict[str, Any]]:
        collection = resp.get("data", {}).get("collection", [])
        if not isinstance(collection, list):
            logger.warning(f"Unexpected collection shape for {label}: {type(collection)}")
            return []
        logger.info(f"Tally returned {len(collection)} {label} record(s)")
        return collection
