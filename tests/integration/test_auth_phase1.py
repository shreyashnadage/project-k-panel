"""
Phase 1: Supabase Authentication - Integration Tests

Tests:
- Client registration
- Email verification
- Login
- JWT token validation
- Token refresh
- Access control
"""

import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloudplatform.main import app
from cloudplatform.db.database import get_db
from cloudplatform.db.models import Base, Client
from cloudplatform.auth.supabase_client import supabase_client

# ============================================================================
# Test Configuration
# ============================================================================

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
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

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# Phase 1 Tests: Registration
# ============================================================================

class TestRegistration:
    """Test client registration flow"""

    def test_register_valid_client(self):
        """Test successful client registration"""
        print("\n[TEST] Register valid client")

        response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 200

        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")

        assert data["status"] == "success"
        assert data["email"] == "shreya@sharma.com"
        assert data["company_name"] == "Sharma Traders"
        assert "client_id" in data
        assert data["verification_required"] is True

        # Verify client stored in database
        db = TestingSessionLocal()
        db_client = db.query(Client).filter(
            Client.email == "shreya@sharma.com"
        ).first()
        assert db_client is not None
        assert db_client.status == "pending_verification"
        db.close()

        print("   ✅ PASS: Client registered successfully\n")

    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        print("\n[TEST] TEST: Register with invalid email")

        response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "invalid-email",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 422  # Validation error

        print("   ✅ PASS: Invalid email rejected\n")

    def test_register_weak_password(self):
        """Test registration with weak password"""
        print("\n[TEST] TEST: Register with weak password")

        response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "weak"  # Too short, no uppercase, no digit
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 422  # Validation error

        print("   ✅ PASS: Weak password rejected\n")

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        print("\n[TEST] TEST: Register with duplicate email")

        # First registration
        client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        # Attempt duplicate registration
        response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Another Company",
                "email": "shreya@sharma.com",
                "phone": "+91-1234567890",
                "password": "AnotherPass123"
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 400

        data = response.json()
        assert "already registered" in data["detail"]

        print("   ✅ PASS: Duplicate email rejected\n")

    def test_register_short_company_name(self):
        """Test registration with short company name"""
        print("\n[TEST] TEST: Register with short company name")

        response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "AB",  # Too short
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 422

        print("   ✅ PASS: Short company name rejected\n")


# ============================================================================
# Phase 1 Tests: Email Verification
# ============================================================================

class TestEmailVerification:
    """Test email verification flow"""

    def test_verify_email_valid_token(self):
        """Test successful email verification"""
        print("\n[EMAIL]  TEST: Verify email with valid token")

        # Register first
        register_response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        verification_token = register_response.json()["verification_token"]

        # Verify email
        verify_response = client.post(
            "/v1/auth/verify-email",
            json={"token": verification_token}
        )

        print(f"   Status: {verify_response.status_code}")
        assert verify_response.status_code == 200

        data = verify_response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")

        assert data["status"] == "success"
        assert data["email"] == "shreya@sharma.com"

        # Verify client status updated
        db = TestingSessionLocal()
        db_client = db.query(Client).filter(
            Client.email == "shreya@sharma.com"
        ).first()
        assert db_client.email_verified is True
        assert db_client.status == "active"
        db.close()

        print("   ✅ PASS: Email verified successfully\n")

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        print("\n[EMAIL]  TEST: Verify email with invalid token")

        response = client.post(
            "/v1/auth/verify-email",
            json={"token": "invalid-token"}
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 400

        print("   ✅ PASS: Invalid token rejected\n")


# ============================================================================
# Phase 1 Tests: Login
# ============================================================================

class TestLogin:
    """Test login flow"""

    def test_login_valid_credentials(self):
        """Test successful login"""
        print("\n[LOGIN] TEST: Login with valid credentials")

        # Register first
        client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        # Verify email
        register_response = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        # For test, manually verify
        db = TestingSessionLocal()
        db_client = db.query(Client).filter(
            Client.email == "shreya@sharma.com"
        ).first()
        if db_client:
            db_client.email_verified = True
            db_client.status = "active"
            db.commit()
        db.close()

        # Login
        login_response = client.post(
            "/v1/auth/login",
            json={
                "email": "shreya@sharma.com",
                "password": "SecurePass123"
            }
        )

        print(f"   Status: {login_response.status_code}")
        assert login_response.status_code == 200

        data = login_response.json()
        print(f"   Response keys: {list(data.keys())}")

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        print("   ✅ PASS: Login successful\n")

    def test_login_unverified_email(self):
        """Test login with unverified email"""
        print("\n[LOGIN] TEST: Login with unverified email")

        # Register
        client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        # Try login without verifying
        login_response = client.post(
            "/v1/auth/login",
            json={
                "email": "shreya@sharma.com",
                "password": "SecurePass123"
            }
        )

        print(f"   Status: {login_response.status_code}")
        assert login_response.status_code == 401

        print("   ✅ PASS: Unverified login rejected\n")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        print("\n[LOGIN] TEST: Login with invalid credentials")

        response = client.post(
            "/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123"
            }
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 401

        print("   ✅ PASS: Invalid credentials rejected\n")


# ============================================================================
# Phase 1 Tests: Token Management
# ============================================================================

class TestTokenManagement:
    """Test JWT token management"""

    def test_verify_valid_token(self):
        """Test token verification"""
        print("\n[TOKEN] TEST: Verify valid token")

        # Create token
        token = supabase_client._create_access_token(
            client_id="cli_test123",
            email="test@example.com"
        )

        # Verify token
        client_info = supabase_client.verify_token(token)

        print(f"   Client ID: {client_info.client_id}")
        print(f"   Email: {client_info.email}")

        assert client_info.client_id == "cli_test123"
        assert client_info.email == "test@example.com"

        print("   ✅ PASS: Token verified successfully\n")

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        print("\n[TOKEN] TEST: Verify invalid token")

        with pytest.raises(ValueError):
            supabase_client.verify_token("invalid-token")

        print("   ✅ PASS: Invalid token rejected\n")

    def test_refresh_token(self):
        """Test token refresh"""
        print("\n[TOKEN] TEST: Refresh token")

        # Create refresh token
        refresh_token = supabase_client._create_refresh_token(
            client_id="cli_test123"
        )

        # Refresh
        token_response = supabase_client.refresh_access_token(refresh_token)

        print(f"   New token type: {token_response.token_type}")
        assert token_response.token_type == "bearer"
        assert len(token_response.access_token) > 0
        assert token_response.expires_in > 0

        print("   PASS: Token refreshed successfully\n")


# ============================================================================
# Phase 1 Tests: Access Control
# ============================================================================

class TestAccessControl:
    """Test authentication middleware and access control"""

    def test_get_current_user_authenticated(self):
        """Test accessing protected endpoint with valid token"""
        print("\n[USER] TEST: Get current user (authenticated)")

        # Setup: Register, verify, and login
        register_resp = client.post(
            "/v1/auth/register",
            json={
                "company_name": "Sharma Traders",
                "email": "shreya@sharma.com",
                "phone": "+91-9876543210",
                "password": "SecurePass123"
            }
        )

        print(f"   Register status: {register_resp.status_code}")
        assert register_resp.status_code == 200
        client_id = register_resp.json()["client_id"]

        # Manually verify - keep DB session open
        db = TestingSessionLocal()
        db_client = db.query(Client).filter(
            Client.client_id == client_id
        ).first()

        if not db_client:
            print(f"   ERROR: Client not found in DB with id: {client_id}")
            # Try by email
            db_client = db.query(Client).filter(
                Client.email == "shreya@sharma.com"
            ).first()
            if db_client:
                print(f"   Found by email, client_id: {db_client.client_id}")

        if db_client:
            db_client.email_verified = True
            db_client.status = "active"
            db.commit()
        db.close()

        # Login
        login_response = client.post(
            "/v1/auth/login",
            json={
                "email": "shreya@sharma.com",
                "password": "SecurePass123"
            }
        )

        print(f"   Login status: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"   Login error: {login_response.json()}")

        access_token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.json()}")

        assert response.status_code == 200

        data = response.json()
        print(f"   User: {data['email']}")

        assert data["email"] == "shreya@sharma.com"
        assert data["company_name"] == "Sharma Traders"
        assert data["status"] == "active"

        print("   PASS: Protected endpoint accessible with token\n")

    def test_get_current_user_unauthenticated(self):
        """Test accessing protected endpoint without token"""
        print("\n[USER] TEST: Get current user (unauthenticated)")

        response = client.get("/v1/auth/me")

        print(f"   Status: {response.status_code}")
        # 401 = Unauthorized (missing credentials), 403 = Forbidden (invalid credentials)
        assert response.status_code in [401, 403]

        print("   PASS: Protected endpoint denied without token\n")

    def test_get_current_user_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        print("\n[USER] TEST: Get current user (invalid token)")

        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )

        print(f"   Status: {response.status_code}")
        assert response.status_code == 401

        print("   ✅ PASS: Invalid token rejected\n")


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 1: SUPABASE AUTHENTICATION - TEST SUITE")
    print("="*70)

    pytest.main([__file__, "-v", "-s"])
