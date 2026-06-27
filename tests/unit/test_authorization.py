"""
Unit Tests for Authorization Module (Phase 3)

Tests:
- Cerbos client permission checking
- Role-based access control
- Policy definitions
- Cross-client isolation
"""

import pytest
from datetime import datetime

from cloudplatform.authorization.cerbos_client import (
    CerbosClient,
    Principal,
    ResourceContext,
    AuthorizationCheck,
    AuthorizationResult,
    Role,
    Action,
    Resource,
    Policies,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def cerbos_client():
    """Create fresh Cerbos client for testing"""
    client = CerbosClient()
    yield client
    # Cleanup
    client.clear_audit_trail()


@pytest.fixture
def admin_principal():
    """Admin user principal"""
    return Principal(
        client_id="cli_admin_test",
        role=Role.ADMIN,
        email="admin@test.com"
    )


@pytest.fixture
def finance_principal():
    """Finance user principal"""
    return Principal(
        client_id="cli_finance_test",
        role=Role.FINANCE,
        email="finance@test.com"
    )


@pytest.fixture
def viewer_principal():
    """Viewer user principal"""
    return Principal(
        client_id="cli_viewer_test",
        role=Role.VIEWER,
        email="viewer@test.com"
    )


@pytest.fixture
def device_principal():
    """Device principal"""
    return Principal(
        client_id="cli_device_test",
        role=Role.DEVICE,
        email="device@test.com"
    )


@pytest.fixture
def test_ledger():
    """Test ledger resource"""
    return ResourceContext(
        resource_type=Resource.LEDGER,
        resource_id="ledger_test123",
        owner_client_id="cli_finance_test"
    )


@pytest.fixture
def test_voucher():
    """Test voucher resource"""
    return ResourceContext(
        resource_type=Resource.VOUCHER,
        resource_id="voucher_test456",
        owner_client_id="cli_finance_test"
    )


@pytest.fixture
def test_device():
    """Test device resource"""
    return ResourceContext(
        resource_type=Resource.DEVICE,
        resource_id="device_test789",
        owner_client_id="cli_device_test"
    )


# ============================================================================
# Test Class: Permission Checks
# ============================================================================

class TestPermissionChecks:
    """Test basic permission checking logic"""

    def test_admin_can_read_ledger(self, cerbos_client, admin_principal, test_ledger):
        """Admin should be able to read any ledger"""
        print("\n[TEST] Admin can read ledger")

        result = cerbos_client.check_permission(
            admin_principal,
            test_ledger,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        assert result.reason != ""
        print("   PASS: Admin read allowed\n")

    def test_admin_can_delete_ledger(self, cerbos_client, admin_principal, test_ledger):
        """Admin should be able to delete any ledger"""
        print("\n[TEST] Admin can delete ledger")

        result = cerbos_client.check_permission(
            admin_principal,
            test_ledger,
            Action.DELETE
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Admin delete allowed\n")

    def test_finance_can_read_own_ledger(self, cerbos_client, finance_principal, test_ledger):
        """Finance user should read their own ledger"""
        print("\n[TEST] Finance can read own ledger")

        result = cerbos_client.check_permission(
            finance_principal,
            test_ledger,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Finance read allowed\n")

    def test_finance_cannot_delete_ledger(self, cerbos_client, finance_principal, test_ledger):
        """Finance user should NOT be able to delete"""
        print("\n[TEST] Finance cannot delete ledger")

        result = cerbos_client.check_permission(
            finance_principal,
            test_ledger,
            Action.DELETE
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is False
        assert "cannot perform" in result.reason
        print("   PASS: Finance delete denied\n")

    def test_viewer_cannot_write_voucher(self, cerbos_client, viewer_principal, test_voucher):
        """Viewer should NOT be able to write"""
        print("\n[TEST] Viewer cannot write voucher")

        result = cerbos_client.check_permission(
            viewer_principal,
            test_voucher,
            Action.WRITE
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is False
        print("   PASS: Viewer write denied\n")

    def test_viewer_can_read_own_voucher(self, cerbos_client, viewer_principal):
        """Viewer should be able to read their own voucher"""
        print("\n[TEST] Viewer can read own voucher")

        # Create voucher owned by viewer (not by finance)
        viewer_voucher = ResourceContext(
            resource_type=Resource.VOUCHER,
            resource_id="voucher_viewer123",
            owner_client_id="cli_viewer_test"  # Owned by viewer
        )

        result = cerbos_client.check_permission(
            viewer_principal,
            viewer_voucher,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Viewer read own data allowed\n")


# ============================================================================
# Test Class: Cross-Client Isolation
# ============================================================================

class TestCrossClientIsolation:
    """Test that clients cannot access each other's data"""

    def test_finance_cannot_access_other_client_ledger(self, cerbos_client, finance_principal):
        """Finance user should NOT access another client's ledger"""
        print("\n[TEST] Finance cannot access other client's ledger")

        other_client_ledger = ResourceContext(
            resource_type=Resource.LEDGER,
            resource_id="ledger_other789",
            owner_client_id="cli_other_test"  # Different client
        )

        result = cerbos_client.check_permission(
            finance_principal,
            other_client_ledger,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is False
        assert "Cross-client" in result.reason
        print("   PASS: Cross-client access denied\n")

    def test_admin_can_access_any_client_data(self, cerbos_client, admin_principal):
        """Admin should be able to access any client's data"""
        print("\n[TEST] Admin can access any client's data")

        other_client_ledger = ResourceContext(
            resource_type=Resource.LEDGER,
            resource_id="ledger_other789",
            owner_client_id="cli_other_test"
        )

        result = cerbos_client.check_permission(
            admin_principal,
            other_client_ledger,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Admin can access other client data\n")

    def test_viewer_cannot_access_other_client_data(self, cerbos_client, viewer_principal):
        """Viewer should NOT access another client's data"""
        print("\n[TEST] Viewer cannot access other client's data")

        other_client_voucher = ResourceContext(
            resource_type=Resource.VOUCHER,
            resource_id="voucher_other123",
            owner_client_id="cli_other_test"
        )

        result = cerbos_client.check_permission(
            viewer_principal,
            other_client_voucher,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is False
        print("   PASS: Viewer cross-client access denied\n")


# ============================================================================
# Test Class: Device Permissions
# ============================================================================

class TestDevicePermissions:
    """Test device-specific permissions"""

    def test_device_can_transmit_sync(self, cerbos_client, device_principal):
        """Device should be able to transmit sync data"""
        print("\n[TEST] Device can transmit sync")

        # TRANSMIT_SYNC is on SYNC_RECORD resource, not DEVICE
        sync_record = ResourceContext(
            resource_type=Resource.SYNC_RECORD,
            resource_id="sync_test123",
            owner_client_id="cli_device_test"
        )

        result = cerbos_client.check_permission(
            device_principal,
            sync_record,
            Action.TRANSMIT_SYNC
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Device sync transmit allowed\n")

    def test_device_can_register_device(self, cerbos_client, device_principal, test_device):
        """Device should be able to register new device"""
        print("\n[TEST] Device can register device")

        result = cerbos_client.check_permission(
            device_principal,
            test_device,
            Action.REGISTER_DEVICE
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is True
        print("   PASS: Device registration allowed\n")

    def test_device_cannot_read_ledger(self, cerbos_client, device_principal, test_device):
        """Device should NOT access ledgers"""
        print("\n[TEST] Device cannot read ledger")

        result = cerbos_client.check_permission(
            device_principal,
            test_device,
            Action.READ
        )

        print(f"   Result: {result.allowed}")
        # Device can't do regular read on device resource
        assert result.allowed is False
        print("   PASS: Device read denied\n")

    def test_finance_cannot_register_device(self, cerbos_client, finance_principal, test_device):
        """Finance user should NOT register devices"""
        print("\n[TEST] Finance cannot register device")

        result = cerbos_client.check_permission(
            finance_principal,
            test_device,
            Action.REGISTER_DEVICE
        )

        print(f"   Result: {result.allowed}")
        assert result.allowed is False
        print("   PASS: Finance device registration denied\n")


# ============================================================================
# Test Class: Policy Definitions
# ============================================================================

class TestPolicyDefinitions:
    """Test that policies are correctly defined"""

    def test_admin_has_all_permissions(self):
        """Admin role should have all permissions"""
        print("\n[TEST] Admin has all permissions")

        admin_perms = Policies.get_permissions(Role.ADMIN)

        print(f"   Admin can perform: {len(admin_perms)} resource types")
        for resource, actions in admin_perms.items():
            print(f"      {resource.value}: {len(actions)} actions")

        # Verify admin has multiple permissions per resource
        for resource, actions in admin_perms.items():
            assert len(actions) > 0, f"Admin should have permissions for {resource.value}"

        print("   PASS: Admin has all permissions\n")

    def test_finance_has_limited_permissions(self):
        """Finance role should have limited permissions"""
        print("\n[TEST] Finance has limited permissions")

        finance_perms = Policies.get_permissions(Role.FINANCE)

        # Finance should have READ and WRITE on some resources
        assert Action.READ in finance_perms[Resource.LEDGER]
        assert Action.WRITE in finance_perms[Resource.LEDGER]
        assert Action.DELETE not in finance_perms[Resource.LEDGER]

        print("   PASS: Finance has limited permissions\n")

    def test_viewer_is_read_only(self):
        """Viewer role should only have read permission"""
        print("\n[TEST] Viewer is read-only")

        viewer_perms = Policies.get_permissions(Role.VIEWER)

        # Viewer should only have READ
        for resource, actions in viewer_perms.items():
            if actions:  # If resource has any permissions
                assert Action.READ in actions
                assert Action.WRITE not in actions
                assert Action.DELETE not in actions

        print("   PASS: Viewer is read-only\n")

    def test_device_has_sync_permissions(self):
        """Device role should have sync-specific permissions"""
        print("\n[TEST] Device has sync permissions")

        device_perms = Policies.get_permissions(Role.DEVICE)

        # Device should have sync and registration permissions
        device_actions = device_perms.get(Resource.DEVICE, [])
        assert Action.REGISTER_DEVICE in device_actions
        assert Action.ROTATE_KEY in device_actions

        sync_actions = device_perms.get(Resource.SYNC_RECORD, [])
        assert Action.TRANSMIT_SYNC in sync_actions

        print("   PASS: Device has sync permissions\n")


# ============================================================================
# Test Class: Batch Checking
# ============================================================================

class TestBatchChecking:
    """Test batch permission checking"""

    def test_check_multiple_permissions(self, cerbos_client, finance_principal, test_ledger):
        """Check multiple permissions in batch"""
        print("\n[TEST] Batch permission checking")

        checks = [
            AuthorizationCheck(finance_principal, test_ledger, Action.READ),
            AuthorizationCheck(finance_principal, test_ledger, Action.WRITE),
            AuthorizationCheck(finance_principal, test_ledger, Action.DELETE),
        ]

        results = cerbos_client.check_multiple(checks)

        print(f"   Checked {len(results)} permissions")
        assert results[0].allowed is True  # READ
        assert results[1].allowed is True  # WRITE
        assert results[2].allowed is False  # DELETE

        print("   PASS: Batch checking works\n")


# ============================================================================
# Test Class: Audit Trail
# ============================================================================

class TestAuditTrail:
    """Test authorization audit logging"""

    def test_decision_logged_on_allow(self, cerbos_client, admin_principal, test_ledger):
        """Authorization decision should be logged"""
        print("\n[TEST] Decision logged on allow")

        cerbos_client.check_permission(
            admin_principal,
            test_ledger,
            Action.READ
        )

        trail = cerbos_client.get_audit_trail()

        print(f"   Audit trail entries: {len(trail)}")
        assert len(trail) == 1
        assert trail[0]["allowed"] is True
        assert trail[0]["principal_client_id"] == "cli_admin_test"

        print("   PASS: Decision logged\n")

    def test_decision_logged_on_deny(self, cerbos_client, viewer_principal):
        """Denied decisions should also be logged"""
        print("\n[TEST] Decision logged on deny")

        # Create resource owned by viewer to avoid cross-client check
        viewer_ledger = ResourceContext(
            resource_type=Resource.LEDGER,
            resource_id="ledger_viewer123",
            owner_client_id="cli_viewer_test"
        )

        cerbos_client.check_permission(
            viewer_principal,
            viewer_ledger,
            Action.DELETE
        )

        trail = cerbos_client.get_audit_trail()

        print(f"   Audit trail entries: {len(trail)}")
        assert len(trail) == 1
        assert trail[0]["allowed"] is False
        assert "cannot perform" in trail[0]["reason"]

        print("   PASS: Deny decision logged\n")

    def test_multiple_decisions_in_trail(self, cerbos_client, admin_principal, finance_principal, test_ledger):
        """Multiple decisions should accumulate in trail"""
        print("\n[TEST] Multiple decisions in trail")

        cerbos_client.check_permission(admin_principal, test_ledger, Action.READ)
        cerbos_client.check_permission(finance_principal, test_ledger, Action.WRITE)
        cerbos_client.check_permission(admin_principal, test_ledger, Action.DELETE)

        trail = cerbos_client.get_audit_trail()

        print(f"   Audit trail entries: {len(trail)}")
        assert len(trail) == 3

        print("   PASS: Multiple decisions logged\n")


# ============================================================================
# Test Class: Helper Methods
# ============================================================================

class TestHelperMethods:
    """Test helper methods"""

    def test_verify_client_ownership_same_client(self, cerbos_client, finance_principal):
        """Verify ownership check for same client"""
        print("\n[TEST] Verify client ownership (same client)")

        is_owner = cerbos_client.verify_client_ownership(
            finance_principal,
            "cli_finance_test"  # Same as principal
        )

        print(f"   Is owner: {is_owner}")
        assert is_owner is True
        print("   PASS: Same client is owner\n")

    def test_verify_client_ownership_different_client(self, cerbos_client, finance_principal):
        """Verify ownership check for different client"""
        print("\n[TEST] Verify client ownership (different client)")

        is_owner = cerbos_client.verify_client_ownership(
            finance_principal,
            "cli_other_test"  # Different client
        )

        print(f"   Is owner: {is_owner}")
        assert is_owner is False
        print("   PASS: Different client not owner\n")

    def test_verify_client_ownership_admin(self, cerbos_client, admin_principal):
        """Admin should be owner of everything"""
        print("\n[TEST] Verify client ownership (admin)")

        is_owner = cerbos_client.verify_client_ownership(
            admin_principal,
            "cli_any_client"
        )

        print(f"   Is owner: {is_owner}")
        assert is_owner is True
        print("   PASS: Admin is owner of all\n")

    def test_has_role_same_role(self, cerbos_client, finance_principal):
        """Check if principal has matching role"""
        print("\n[TEST] Has role (same role)")

        has_role = cerbos_client.has_role(finance_principal, Role.FINANCE)

        print(f"   Has role: {has_role}")
        assert has_role is True
        print("   PASS: Has matching role\n")

    def test_has_role_admin_has_all(self, cerbos_client, admin_principal):
        """Admin should have all roles"""
        print("\n[TEST] Has role (admin has all)")

        assert cerbos_client.has_role(admin_principal, Role.ADMIN)
        assert cerbos_client.has_role(admin_principal, Role.FINANCE)
        assert cerbos_client.has_role(admin_principal, Role.VIEWER)

        print("   PASS: Admin has all roles\n")


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_missing_client_id_raises_error(self, cerbos_client, test_ledger):
        """Missing client_id should raise error"""
        print("\n[TEST] Missing client_id raises error")

        invalid_principal = Principal(
            client_id="",  # Empty
            role=Role.ADMIN,
            email="test@test.com"
        )

        with pytest.raises(ValueError):
            cerbos_client.check_permission(
                invalid_principal,
                test_ledger,
                Action.READ
            )

        print("   PASS: Missing client_id raises error\n")

    def test_missing_resource_type_raises_error(self, cerbos_client, admin_principal):
        """Missing resource type should raise error"""
        print("\n[TEST] Missing resource type raises error")

        with pytest.raises(ValueError):
            cerbos_client.check_permission(
                admin_principal,
                None,  # None resource
                Action.READ
            )

        print("   PASS: Missing resource raises error\n")

    def test_missing_action_raises_error(self, cerbos_client, admin_principal, test_ledger):
        """Missing action should raise error"""
        print("\n[TEST] Missing action raises error")

        with pytest.raises(ValueError):
            cerbos_client.check_permission(
                admin_principal,
                test_ledger,
                None  # None action
            )

        print("   PASS: Missing action raises error\n")


if __name__ == "__main__":
    print("Running authorization unit tests...")
    pytest.main([__file__, "-v", "-s"])
