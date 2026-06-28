"""
Phase 2: Device Registration - Integration Tests

Tests:
- Installation key generation
- Installation key validation
- Device registration
- API key generation and rotation
- Device management
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloudplatform.main import app
from cloudplatform.db.database import get_db
from cloudplatform.db.models import Base, Client, InstallationKey, DeviceRegistration
from cloudplatform.keys.key_service import installation_key_service, api_key_service

# Test DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase2.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestInstallationKeyService:
    """Test installation key generation and validation"""

    def test_generate_installation_key(self):
        """Test generating installation key"""
        print("\n[TEST] Generate installation key")

        result = installation_key_service.generate_installation_key("cli_test123")

        print(f"   Generated key: {result['installation_key'][:30]}...")
        assert "TSA-" in result["installation_key"]
        assert result["status"] == "active"
        assert result["client_id"] == "cli_test123"
        assert result["key_id"]
        assert result["expires_at"]

        print("   PASS: Installation key generated\n")

    def test_validate_installation_key_valid(self):
        """Test validating valid installation key"""
        print("\n[TEST] Validate valid key")

        # Generate key
        key_data = installation_key_service.generate_installation_key("cli_test123")

        # Validate it
        is_valid, error = installation_key_service.validate_installation_key(
            key_data["installation_key"],
            key_data
        )

        print(f"   Validation result: {is_valid}")
        assert is_valid is True
        assert error == ""

        print("   PASS: Key validated\n")

    def test_validate_installation_key_invalid(self):
        """Test validating invalid installation key"""
        print("\n[TEST] Validate invalid key")

        key_data = installation_key_service.generate_installation_key("cli_test123")

        is_valid, error = installation_key_service.validate_installation_key(
            "WRONG-KEY",
            key_data
        )

        print(f"   Validation result: {is_valid}, Error: {error}")
        assert is_valid is False
        assert "Invalid" in error

        print("   PASS: Invalid key rejected\n")

    def test_validate_installation_key_expired(self):
        """Test validating expired installation key"""
        print("\n[TEST] Validate expired key")

        # Generate key but set it as expired
        key_data = installation_key_service.generate_installation_key("cli_test123")
        key_data["expires_at"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        is_valid, error = installation_key_service.validate_installation_key(
            key_data["installation_key"],
            key_data
        )

        print(f"   Validation result: {is_valid}, Error: {error}")
        assert is_valid is False
        assert "expired" in error.lower()

        print("   PASS: Expired key rejected\n")


class TestAPIKeyService:
    """Test API key generation and rotation"""

    def test_generate_api_key(self):
        """Test generating API key"""
        print("\n[TEST] Generate API key")

        result = api_key_service.generate_api_key("device_test123", "cli_test123")

        print(f"   Generated key: {result['api_key'][:30]}...")
        assert result["api_key"].startswith("sk_live_")
        assert result["status"] == "active"
        assert result["device_id"] == "device_test123"
        assert result["client_id"] == "cli_test123"

        print("   PASS: API key generated\n")

    def test_validate_api_key_valid(self):
        """Test validating valid API key"""
        print("\n[TEST] Validate valid API key")

        key_data = api_key_service.generate_api_key("device_test123", "cli_test123")

        is_valid, returned_data = api_key_service.validate_api_key(
            key_data["api_key"],
            key_data
        )

        print(f"   Validation result: {is_valid}")
        assert is_valid is True
        assert returned_data["api_key"] == key_data["api_key"]

        print("   PASS: API key validated\n")

    def test_validate_api_key_invalid(self):
        """Test validating invalid API key"""
        print("\n[TEST] Validate invalid API key")

        key_data = api_key_service.generate_api_key("device_test123", "cli_test123")

        is_valid, returned_data = api_key_service.validate_api_key(
            "WRONG-KEY",
            key_data
        )

        print(f"   Validation result: {is_valid}")
        assert is_valid is False
        assert returned_data == {}

        print("   PASS: Invalid API key rejected\n")

    def test_rotate_api_key(self):
        """Test rotating API key"""
        print("\n[TEST] Rotate API key")

        # Generate old key
        old_key = api_key_service.generate_api_key("device_test123", "cli_test123")

        # Generate new key
        new_key_id = "apikey_new123"
        new_api_key = "sk_live_new_key_xyz"

        # Rotate
        revoked_key, new_key_data = api_key_service.rotate_api_key(
            old_key,
            new_key_id,
            new_api_key
        )

        print(f"   Old key status: {revoked_key['status']}")
        print(f"   New key status: {new_key_data['status']}")

        assert revoked_key["status"] == "revoked"
        assert new_key_data["status"] == "active"
        assert new_key_data["api_key"] == new_api_key
        assert new_key_data["rotated_from"] == old_key["key_id"]

        print("   PASS: API key rotated\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
