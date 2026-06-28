"""
Client registration module for Tally Sync Agent.

Handles:
- Storing registration credentials securely
- Retrieving credentials for syncs
- Validating registration status
"""

import json
import logging
import keyring  # Windows Credential Manager
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Credential storage service name
CRED_SERVICE_NAME = "TallySyncAgent"
CRED_USERNAME = "registration"


class ClientRegistration:
    """Manages client registration and credentials."""

    def __init__(self):
        """Initialize registration manager."""
        self.service = CRED_SERVICE_NAME
        self.username = CRED_USERNAME
        self.is_registered = self._check_registration()

    def _check_registration(self) -> bool:
        """Check if agent is already registered."""
        try:
            creds = self._get_credentials()
            return creds is not None
        except Exception:
            return False

    def _store_credentials(self, creds: Dict[str, str]) -> bool:
        """
        Store credentials securely in Windows Credential Manager.

        Args:
            creds: Dictionary with keys:
                - client_id: Unique client identifier
                - device_id: Unique device identifier
                - api_key: API key for authentication
                - registration_token: Registration token

        Returns:
            True if stored successfully
        """
        try:
            creds_json = json.dumps(creds)
            keyring.set_password(self.service, self.username, creds_json)
            logger.info("Credentials stored securely in Windows Credential Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False

    def _get_credentials(self) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from Windows Credential Manager.

        Returns:
            Dictionary with credentials, or None if not found
        """
        try:
            creds_json = keyring.get_password(self.service, self.username)
            if creds_json:
                return json.loads(creds_json)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None

    def _delete_credentials(self) -> bool:
        """Delete stored credentials."""
        try:
            keyring.delete_password(self.service, self.username)
            logger.info("Credentials deleted from Windows Credential Manager")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete credentials: {e}")
            return False

    def register_device(
        self,
        api_base_url: str,
        installation_key: str,
        device_name: str,
        os_version: str,
        agent_version: str
    ) -> bool:
        """
        Register device with the platform.

        Flow:
        1. Send installation key to platform
        2. Platform validates and returns credentials
        3. Store credentials locally
        4. Verify storage

        Args:
            api_base_url: Platform API URL (e.g., http://15.206.90.21:8000)
            installation_key: Key from registration email
            device_name: Name of this PC (e.g., OFFICE-PC-01)
            os_version: Windows version
            agent_version: Agent version (e.g., 0.4.0)

        Returns:
            True if registration successful
        """
        try:
            import httpx

            logger.info("Registering device with platform...")
            logger.info(f"  Device: {device_name}")
            logger.info(f"  OS: {os_version}")
            logger.info(f"  Agent: {agent_version}")

            # POST to platform
            url = f"{api_base_url}/v1/register-device"
            payload = {
                "installation_key": installation_key,
                "device_name": device_name,
                "os_version": os_version,
                "agent_version": agent_version,
            }

            logger.debug(f"Sending registration request to {url}")
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Registration response: {data}")

            if data.get("status") != "registered":
                logger.error(f"Registration failed: {data.get('message')}")
                return False

            # Extract credentials from response
            creds = {
                "client_id": data["client_id"],
                "device_id": data["device_id"],
                "api_key": data["api_key"],
                "registration_token": data["registration_token"],
                "api_base_url": api_base_url,  # Store for future use
            }

            # Store credentials
            if not self._store_credentials(creds):
                logger.error("Failed to store credentials")
                return False

            logger.info("Device registered successfully!")
            logger.info(f"  Client ID: {creds['client_id']}")
            logger.info(f"  Device ID: {creds['device_id']}")

            self.is_registered = True
            return True

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during registration: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return False

    def get_client_id(self) -> Optional[str]:
        """Get stored client ID."""
        creds = self._get_credentials()
        return creds.get("client_id") if creds else None

    def get_device_id(self) -> Optional[str]:
        """Get stored device ID."""
        creds = self._get_credentials()
        return creds.get("device_id") if creds else None

    def get_api_key(self) -> Optional[str]:
        """Get stored API key."""
        creds = self._get_credentials()
        return creds.get("api_key") if creds else None

    def get_all_credentials(self) -> Optional[Dict[str, str]]:
        """Get all stored credentials."""
        return self._get_credentials()

    def verify_registration(self) -> bool:
        """Verify registration is valid."""
        try:
            creds = self._get_credentials()
            if not creds:
                logger.warning("No registration found")
                return False

            required_fields = ["client_id", "device_id", "api_key"]
            for field in required_fields:
                if field not in creds:
                    logger.warning(f"Missing credential field: {field}")
                    return False

            logger.info("Registration verified")
            logger.debug(f"  Client: {creds['client_id']}")
            logger.debug(f"  Device: {creds['device_id']}")
            return True

        except Exception as e:
            logger.error(f"Error verifying registration: {e}")
            return False

    def unregister(self) -> bool:
        """Unregister device and delete credentials."""
        return self._delete_credentials()

    def get_registration_status(self) -> Dict[str, any]:
        """Get current registration status."""
        creds = self._get_credentials()

        if not creds:
            return {
                "is_registered": False,
                "message": "Device not registered"
            }

        return {
            "is_registered": True,
            "client_id": creds.get("client_id"),
            "device_id": creds.get("device_id"),
            "api_base_url": creds.get("api_base_url"),
        }


# Global instance
registration = ClientRegistration()


def get_registration() -> ClientRegistration:
    """Get the global registration instance."""
    global registration
    return registration
