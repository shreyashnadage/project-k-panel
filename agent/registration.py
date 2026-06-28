# -*- coding: utf-8 -*-
"""
Client registration — reads/writes credentials from Windows Credential Manager.

The registration wizard (installer/wizard/registration_wizard.py) stores
credentials during install. This module retrieves them for the agent runtime.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

CRED_SERVICE = "TallySyncAgent"
CRED_USERNAME = "registration"


def _get_keyring():
    try:
        import keyring
        return keyring
    except ImportError:
        return None


def get_credentials() -> Optional[Dict[str, str]]:
    """
    Retrieve stored credentials from Windows Credential Manager.

    Returns dict with keys: client_id, device_id, api_key, api_base_url
    or None if not registered.
    """
    kr = _get_keyring()
    if kr is None:
        return None
    try:
        raw = kr.get_password(CRED_SERVICE, CRED_USERNAME)
        if raw:
            return json.loads(raw)
        return None
    except Exception as e:
        logger.debug(f"Could not read credentials: {e}")
        return None


def store_credentials(creds: Dict[str, str]) -> bool:
    kr = _get_keyring()
    if kr is None:
        logger.error("keyring not installed — cannot store credentials")
        return False
    try:
        kr.set_password(CRED_SERVICE, CRED_USERNAME, json.dumps(creds))
        logger.info("Credentials stored in Windows Credential Manager")
        return True
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        return False


def delete_credentials() -> bool:
    kr = _get_keyring()
    if kr is None:
        return False
    try:
        kr.delete_password(CRED_SERVICE, CRED_USERNAME)
        return True
    except Exception:
        return False


def is_registered() -> bool:
    creds = get_credentials()
    if not creds:
        return False
    return all(creds.get(k) for k in ("client_id", "device_id", "api_key"))
