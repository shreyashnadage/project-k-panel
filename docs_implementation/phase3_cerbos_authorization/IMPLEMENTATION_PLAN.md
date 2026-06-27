# Phase 3: Cerbos Authorization - Implementation Plan

**Date**: 28 June 2026  
**Status**: Starting Implementation  
**Target**: Complete with 100% test coverage

---

## Overview

Phase 3 adds **Role-Based Access Control (RBAC)** using Cerbos, enabling fine-grained authorization policies for multi-tenant SaaS security.

---

## Architecture

### Layer Structure

```
Request → Authentication (Phase 1) → Authorization (Phase 3) → Endpoint
              (JWT validation)        (Role/Policy check)     (Business logic)
                   ↓                          ↓
              ClientInfo                  Access Decision
           (who are you?)            (are you authorized?)
```

### Components

1. **Cerbos Client** - Integration with Cerbos API/service
2. **Policy Definitions** - RBAC policies in Cerbos format
3. **Authorization Middleware** - FastAPI middleware for checks
4. **Route-level Decorators** - @require_permission decorators
5. **Audit Logging** - Track authorization decisions

---

## Implementation Tasks

### Task 1: Cerbos Client Service ✅
**File**: `cloudplatform/authorization/cerbos_client.py`

Features:
- Cerbos API integration (or mock for testing)
- Check resource access permissions
- Check actions on resources
- Policy validation
- Caching for performance

```python
class CerbosClient:
    def check_permission(principal, resource, action) -> bool
    def check_resource(principal, resource) -> Resource
    def batch_check(checks) -> CheckResults
```

### Task 2: RBAC Policy Definitions ✅
**File**: `cloudplatform/authorization/policies.py`

Policies:
- Admin: Full access to all resources
- Finance: Access to ledgers, vouchers, reports
- Viewer: Read-only access to own data
- Device: System access for agent devices

### Task 3: Authorization Middleware ✅
**File**: `cloudplatform/authorization/middleware.py`

Features:
- Extract principal from JWT
- Extract resource from request
- Check permissions with Cerbos
- Return 403 if unauthorized
- Log authorization decisions

### Task 4: Route Decorators ✅
**File**: `cloudplatform/authorization/decorators.py`

Decorators:
- `@require_role(role_name)` - Check user has role
- `@require_permission(resource, action)` - Check permission
- `@require_client_ownership(resource_id_param)` - Verify client owns resource

### Task 5: Comprehensive Tests ✅
**Files**: 
- `tests/unit/test_authorization.py` - Unit tests
- `tests/authorization/test_cerbos_phase3.py` - Integration tests

Test Coverage:
- Permission checks (allow/deny)
- Role-based access
- Cross-client data isolation
- Admin override capabilities
- Audit logging

---

## Role Definitions

### Admin Role
```
Permissions:
- Full access to all resources
- Can manage users and roles
- Can view audit logs
- Can override policies
```

### Finance Role
```
Permissions:
- View ledgers
- View vouchers
- View reports
- Cannot delete data
- Cannot modify settings
```

### Viewer Role
```
Permissions:
- Read-only access
- View own data only
- Cannot modify anything
- No delete access
```

### Device Role (For Agents)
```
Permissions:
- Transmit sync data
- Query installation keys
- Register devices
- Rotate API keys
```

---

## Resource Types

1. **Ledger** - Chart of accounts
   - Principal: client_id
   - Actions: read, write, delete
   - Ownership: one ledger per client

2. **Voucher** - Accounting transactions
   - Principal: client_id
   - Actions: read, write, delete
   - Ownership: one voucher per client

3. **Device** - Registered devices
   - Principal: client_id
   - Actions: read, write, delete
   - Ownership: devices belong to client

4. **Client** - MSME account
   - Principal: client_id
   - Actions: read, write, delete
   - Ownership: self-access only

---

## Testing Strategy

### Unit Tests
- Permission check logic
- Role validation
- Policy evaluation
- Error handling

### Integration Tests
- End-to-end authorization flow
- Cross-client isolation
- Admin capabilities
- Audit trail generation

### Scenarios
1. Admin accessing any resource → Allow
2. Finance viewing ledgers → Allow
3. Viewer deleting voucher → Deny
4. Client A accessing Client B data → Deny
5. Device registering with valid key → Allow
6. Device accessing without key → Deny

---

## Implementation Phases

### Phase 3.1: Cerbos Client & Policies
- Create CerbosClient class
- Define policy structure
- Implement permission checking
- Unit test all logic

### Phase 3.2: Middleware & Decorators
- Create authorization middleware
- Create route decorators
- Integrate with FastAPI
- Test middleware behavior

### Phase 3.3: End-to-End Integration
- Add authorization to existing endpoints
- Test all authorization flows
- Verify cross-client isolation
- Document all policies

### Phase 3.4: Audit & Verification
- Implement audit logging
- Run full integration test suite
- Document all security decisions
- Prepare for Phase 4

---

## Success Criteria

- ✅ All authorization checks working
- ✅ Cross-client data isolation enforced
- ✅ Admin role has full access
- ✅ Finance and Viewer roles properly restricted
- ✅ Device authentication working
- ✅ All unit tests passing (100%)
- ✅ All integration tests passing (100%)
- ✅ No regressions in existing functionality
- ✅ Comprehensive documentation

---

## Files to Create

### Code Files
- `cloudplatform/authorization/__init__.py`
- `cloudplatform/authorization/cerbos_client.py` (250 lines)
- `cloudplatform/authorization/policies.py` (200 lines)
- `cloudplatform/authorization/middleware.py` (150 lines)
- `cloudplatform/authorization/decorators.py` (100 lines)

### Test Files
- `tests/unit/test_authorization.py` (400 lines)
- `tests/authorization/test_cerbos_phase3.py` (600 lines)

### Documentation Files
- `docs_implementation/phase3_cerbos_authorization/IMPLEMENTATION_PLAN.md` (this file)
- `docs_implementation/phase3_cerbos_authorization/TESTING_PLAN.md`
- `docs_implementation/phase3_cerbos_authorization/PROGRESS.md`

---

## Dependencies

### Python Packages
- pydantic (already installed)
- httpx (for Cerbos API calls, already installed)
- fastapi (already installed)

### External Services
- Cerbos API (will mock for testing)

---

## Timeline

```
Task 1 (Cerbos Client):      30 min + 20 min tests
Task 2 (Policy Definitions): 20 min + 15 min tests
Task 3 (Middleware):         30 min + 30 min tests
Task 4 (Decorators):         20 min + 20 min tests
Task 5 (Full Integration):   30 min + 60 min tests
                            ─────────────────────
Total Estimated Time:        4-5 hours
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Cerbos API unavailable | Use mock/in-memory implementation for testing |
| Performance issues | Implement caching for policy checks |
| Incorrect policies | Comprehensive test coverage with all scenarios |
| Data isolation breach | Explicit client_id verification in every check |
| Regression in existing | Full regression test suite for all endpoints |

---

## Next Steps

1. ✅ Create implementation plan (this document)
2. ⏳ Create Cerbos client service
3. ⏳ Define RBAC policies
4. ⏳ Create middleware and decorators
5. ⏳ Write comprehensive tests
6. ⏳ Integration with existing endpoints
7. ⏳ Documentation and verification

---

**Status**: Ready to start Phase 3.1  
**Expected Completion**: ~4-5 hours of focused work
