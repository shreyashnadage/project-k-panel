# Phase 3: Testing Plan - Cerbos Authorization

**Date**: 28 June 2026  
**Target**: 100% test coverage across all authorization scenarios

---

## Testing Strategy

### Test Pyramid

```
                    /\
                   /  \
                  / E2E \       End-to-end flows
                 /      \       (Small number, high value)
                /--------\
               /          \
              / Integration \  Authorization checks
             /              \ (Medium number)
            /----------------\
           /                  \
          /       Unit Tests    \  Permission logic
         /                      \ (Large number, fast)
        /------------------------\
```

---

## Unit Tests (Level 1)

### Test File: `tests/unit/test_authorization.py`

#### Test Class: CerbosClient

**Tests**:
1. ✅ test_check_permission_allow
   - Principal: admin
   - Resource: ledger
   - Action: read
   - Expected: True

2. ✅ test_check_permission_deny
   - Principal: viewer
   - Resource: ledger
   - Action: delete
   - Expected: False

3. ✅ test_check_permission_cross_client_isolation
   - Principal: client_A
   - Resource: client_B's ledger
   - Action: read
   - Expected: False (denied - different client)

4. ✅ test_check_permission_with_invalid_principal
   - Principal: invalid_id
   - Action: read
   - Expected: ValueError raised

5. ✅ test_check_permission_with_invalid_action
   - Principal: admin
   - Resource: ledger
   - Action: invalid_action
   - Expected: ValueError raised

#### Test Class: PolicyDefinitions

**Tests**:
1. ✅ test_admin_role_has_all_permissions
   - Check admin has: read, write, delete on all resources

2. ✅ test_finance_role_has_limited_permissions
   - Check finance has: read on ledgers/vouchers
   - Check finance NOT: delete, write

3. ✅ test_viewer_role_is_read_only
   - Check viewer has: read only
   - Check viewer NOT: write, delete

4. ✅ test_device_role_has_sync_permissions
   - Check device has: transmit_sync, register_device
   - Check device NOT: read_ledger, delete_voucher

#### Test Class: PermissionChecks

**Tests**:
1. ✅ test_permission_check_with_client_id
   - Verify client_id required in check

2. ✅ test_permission_check_with_role
   - Verify role used for policy lookup

3. ✅ test_permission_check_returns_boolean
   - Verify return type is bool

4. ✅ test_permission_check_with_resource_id
   - Verify resource_id used in check

---

## Integration Tests (Level 2)

### Test File: `tests/authorization/test_cerbos_phase3.py`

#### Test Class: AuthorizationMiddleware

**Tests**:
1. ✅ test_middleware_allows_admin_to_read_ledger
   - Request: GET /v1/ledgers
   - User: admin
   - Expected: 200 OK

2. ✅ test_middleware_denies_viewer_to_delete_ledger
   - Request: DELETE /v1/ledgers/123
   - User: viewer
   - Expected: 403 Forbidden

3. ✅ test_middleware_denies_cross_client_access
   - Request: GET /v1/ledgers (but client_A accessing client_B's data)
   - Expected: 403 Forbidden

4. ✅ test_middleware_extracts_principal_from_jwt
   - Verify client_id extracted correctly

5. ✅ test_middleware_checks_authorization_on_each_request
   - Make multiple requests with different permissions

#### Test Class: RouteAuthorization

**Tests**:
1. ✅ test_register_device_requires_installation_key
   - Request: POST /v1/devices/register
   - Without key: 400 Bad Request
   - With key: 200 OK

2. ✅ test_list_devices_shows_only_own_devices
   - User A lists devices: sees only A's devices
   - User B lists devices: sees only B's devices

3. ✅ test_rotate_key_requires_device_ownership
   - User A tries to rotate User B's device key: 403 Forbidden
   - User A rotates own device key: 200 OK

4. ✅ test_get_current_user_works_with_auth
   - GET /v1/auth/me
   - Expected: 200 with current user info

#### Test Class: AdminCapabilities

**Tests**:
1. ✅ test_admin_can_view_any_client_ledgers
   - Admin lists ledgers: sees all
   - Finance lists ledgers: sees only own

2. ✅ test_admin_can_override_policies
   - Admin can delete voucher (normally restricted)

3. ✅ test_admin_can_manage_users
   - Admin endpoints for user management

#### Test Class: AuditLogging

**Tests**:
1. ✅ test_authorization_decision_is_logged
   - Allow decision logged
   - Deny decision logged

2. ✅ test_audit_log_contains_principal_resource_action
   - Verify log structure

3. ✅ test_audit_log_contains_decision_timestamp
   - Verify timestamp recorded

---

## End-to-End Tests (Level 3)

### Test File: `tests/integration/test_cerbos_phase3.py` (E2E section)

#### Scenario 1: Finance User Viewing Ledgers

```python
def test_finance_user_workflow():
    # 1. Login as finance user
    # 2. Get ledger list (allowed)
    # 3. Try to delete ledger (denied)
    # 4. Verify correct permissions enforced
```

**Expected Flow**:
- Login → 200 OK
- List ledgers → 200 OK (filtered to own)
- Delete ledger → 403 Forbidden
- Audit logs all decisions

#### Scenario 2: Admin Override

```python
def test_admin_override_workflow():
    # 1. Login as admin
    # 2. Perform restricted action
    # 3. Verify override works
```

**Expected Flow**:
- Delete voucher (normally restricted) → 200 OK
- Audit logs admin action

#### Scenario 3: Cross-Client Isolation

```python
def test_cross_client_isolation():
    # 1. Login as client A
    # 2. Try to access client B's data
    # 3. Verify complete isolation
```

**Expected Flow**:
- Client A lists devices → sees only A's devices
- Client A tries to access B's device → 403 Forbidden

#### Scenario 4: Device Registration

```python
def test_device_registration_workflow():
    # 1. Register device with installation key
    # 2. Verify device gets API key
    # 3. Verify device can transmit data
```

**Expected Flow**:
- Register device → 200 OK, returns api_key
- Use api_key to transmit data → 200 OK

---

## Test Coverage Matrix

### By Role

| Role | Resources Tested | Permissions Tested |
|------|------------------|--------------------|
| Admin | All | read, write, delete, override |
| Finance | Ledger, Voucher, Report | read |
| Viewer | Own data | read only |
| Device | Sync data | transmit, register |

### By Resource

| Resource | Admin | Finance | Viewer | Device |
|----------|-------|---------|--------|--------|
| Ledger | ✅ | ✅ | ✅ | ❌ |
| Voucher | ✅ | ✅ | ✅ | ❌ |
| Device | ✅ | ❌ | ❌ | ✅ |
| Client | ✅ | ❌ | ❌ | ❌ |

### By Action

| Action | Admin | Finance | Viewer | Device |
|--------|-------|---------|--------|--------|
| Read | ✅ | ✅ | ✅ | ✅ |
| Write | ✅ | ❌ | ❌ | ✅ |
| Delete | ✅ | ❌ | ❌ | ❌ |
| Override | ✅ | ❌ | ❌ | ❌ |

---

## Test Execution Plan

### Phase 3.1 - Cerbos Client Tests
```bash
pytest tests/unit/test_authorization.py::TestCerbosClient -v
Expected: 5/5 PASS
Duration: ~10 seconds
```

### Phase 3.2 - Policy Definition Tests
```bash
pytest tests/unit/test_authorization.py::TestPolicyDefinitions -v
Expected: 4/4 PASS
Duration: ~5 seconds
```

### Phase 3.3 - Middleware Integration Tests
```bash
pytest tests/authorization/test_cerbos_phase3.py::TestAuthorizationMiddleware -v
Expected: 5/5 PASS
Duration: ~30 seconds
```

### Phase 3.4 - End-to-End Tests
```bash
pytest tests/authorization/test_cerbos_phase3.py::TestE2E -v
Expected: 4/4 PASS
Duration: ~60 seconds
```

### Full Test Suite
```bash
pytest tests/unit/test_authorization.py tests/authorization/test_cerbos_phase3.py -v --cov
Expected: 22/22 PASS
Coverage: >95%
Duration: ~2 minutes
```

---

## Test Success Criteria

### Coverage
- ✅ All roles tested
- ✅ All resources tested
- ✅ All actions tested
- ✅ All error cases tested
- ✅ >95% code coverage

### Functionality
- ✅ All permission checks working
- ✅ Cross-client isolation enforced
- ✅ Admin override working
- ✅ Audit logging working
- ✅ Error handling working

### Performance
- ✅ Unit tests complete in <5 seconds
- ✅ Integration tests complete in <2 minutes
- ✅ No timeout issues

### Regression
- ✅ All Phase 1 tests still pass
- ✅ All Phase 2 tests still pass
- ✅ No breaking changes to existing APIs

---

## Test Data

### Test Users

```python
admin_user = {
    "client_id": "cli_admin_test",
    "role": "admin",
    "email": "admin@test.com"
}

finance_user = {
    "client_id": "cli_finance_test",
    "role": "finance",
    "email": "finance@test.com"
}

viewer_user = {
    "client_id": "cli_viewer_test",
    "role": "viewer",
    "email": "viewer@test.com"
}
```

### Test Resources

```python
test_ledger = {
    "resource_id": "ledger_test123",
    "owner_client_id": "cli_finance_test"
}

test_voucher = {
    "resource_id": "voucher_test456",
    "owner_client_id": "cli_finance_test"
}
```

---

## Failure Scenarios Tested

1. ✅ Missing JWT token → 401 Unauthorized
2. ✅ Invalid JWT token → 401 Unauthorized
3. ✅ Valid JWT but no permission → 403 Forbidden
4. ✅ Accessing another client's data → 403 Forbidden
5. ✅ Invalid resource ID → 404 Not Found
6. ✅ Invalid action → 400 Bad Request
7. ✅ Service error → 500 Internal Server Error
8. ✅ Cerbos service unavailable → 503 Service Unavailable

---

## Continuous Testing

### During Development
- Run unit tests after each change
- Run integration tests before committing
- Check coverage targets

### Before Deployment
- Run full test suite
- Verify all tests passing
- Check for regressions

### Post-Deployment
- Monitor error logs
- Verify authorization decisions in audit logs
- Check performance metrics

---

## Test Documentation

### Each Test Includes
- ✅ Clear test name describing scenario
- ✅ Docstring explaining what's tested
- ✅ Setup/teardown for test data
- ✅ Assertions with descriptive messages
- ✅ Comments on complex logic

### Test Output
- ✅ Clear pass/fail messages
- ✅ Coverage reports
- ✅ Performance metrics
- ✅ Audit trail of authorization decisions

---

**Status**: Testing plan complete, ready for implementation  
**Expected Coverage**: >95% code coverage  
**Expected Duration**: ~2 minutes for full test suite
