# Phase 3.3: End-to-End Integration - Implementation Plan

**Date**: 28 June 2026  
**Status**: Starting Implementation  
**Target**: Complete with full endpoint protection

---

## Overview

Phase 3.3 integrates Phases 3.1 (authorization logic) and 3.2 (middleware/decorators) with all 10 existing API endpoints from Phases 1 & 2, creating a complete authorization system.

---

## What Gets Protected

### Phase 1 Endpoints (6 total)
```
POST   /v1/auth/register          ← Public (skip auth)
POST   /v1/auth/verify-email      ← Public (skip auth)
POST   /v1/auth/login             ← Public (skip auth)
POST   /v1/auth/logout            ← Protected (authenticated users only)
POST   /v1/auth/refresh           ← Protected (authenticated users only)
GET    /v1/auth/me                ← Protected (own data only)
```

### Phase 2 Endpoints (4 total)
```
POST   /v1/devices/register       ← Protected (DEVICE role)
GET    /v1/devices/list           ← Protected (client's devices only)
POST   /v1/devices/rotate-key     ← Protected (device ownership)
GET    /v1/devices/status/{id}    ← Protected (device ownership)
```

---

## Authorization Rules by Endpoint

### Auth Endpoints

**POST /v1/auth/register**
- Public (no auth required)
- Middleware: Skip authorization
- Action: Anyone can register

**POST /v1/auth/verify-email**
- Public (no auth required)
- Middleware: Skip authorization
- Action: Anyone can verify

**POST /v1/auth/login**
- Public (no auth required)
- Middleware: Skip authorization
- Action: Anyone can login

**POST /v1/auth/logout**
- Protected
- Middleware: Check authentication
- Decorator: None needed
- Action: User can logout themselves
- Error: 401 if not authenticated

**POST /v1/auth/refresh**
- Protected
- Middleware: Check authentication
- Decorator: None needed
- Action: User can refresh own token
- Error: 401 if not authenticated

**GET /v1/auth/me**
- Protected
- Middleware: Check authentication
- Decorator: @require_client_ownership("client_id")
- Action: User can view own info
- Error: 401 if not authenticated, 403 if accessing other user

### Device Endpoints

**POST /v1/devices/register**
- Protected
- Middleware: Check authentication + INSTALLATION_KEY permission
- Decorator: @require_permission(Resource.DEVICE, Action.REGISTER_DEVICE)
- Action: User can register device with valid key
- Error: 401 if not authenticated, 403 if no permission, 400 if invalid key

**GET /v1/devices/list**
- Protected
- Middleware: Check authentication + READ permission on DEVICE
- Decorator: Implicit (middleware handles)
- Action: User can list own devices
- Error: 401 if not authenticated, 403 if not allowed

**POST /v1/devices/rotate-key**
- Protected
- Middleware: Check authentication + ROTATE_KEY permission
- Decorator: @require_permission(Resource.DEVICE, Action.ROTATE_KEY)
- Action: User can rotate own device key
- Error: 401 if not authenticated, 403 if not device owner

**GET /v1/devices/status/{id}**
- Protected
- Middleware: Check authentication + READ permission on DEVICE
- Decorator: @require_client_ownership("device_id")
- Action: User can view own device status
- Error: 401 if not authenticated, 403 if not device owner

---

## Test Scenarios (6 workflows)

### Scenario 1: Anonymous User Registration
```
User: None (anonymous)
Action: POST /v1/auth/register
Expected: 200 OK, receives verification token
Authorization: Skipped (public endpoint)
```

### Scenario 2: User Login Flow
```
User: Registered, verified email
Action: POST /v1/auth/login
Expected: 200 OK, receives JWT + refresh token
Authorization: Skipped (public endpoint)
```

### Scenario 3: Finance User Views Own Ledgers
```
User: Finance role, client_id=A
Action: GET /v1/ledgers (hypothetical)
Expected: 200 OK, sees only A's ledgers
Authorization: Middleware checks READ on LEDGER
Result: Allowed (Finance can READ)
```

### Scenario 4: Finance User Tries to Delete Ledger
```
User: Finance role, client_id=A
Action: DELETE /v1/ledgers/ledger_A_123
Expected: 403 Forbidden
Authorization: Middleware checks DELETE on LEDGER
Result: Denied (Finance cannot DELETE)
```

### Scenario 5: User A Tries to Access User B's Data
```
User: Client A
Action: GET /v1/devices/status/device_B_456
Expected: 403 Forbidden
Authorization: Middleware checks ownership
Result: Denied (Cross-client isolation)
```

### Scenario 6: Admin Accesses Any Resource
```
User: Admin role, client_id=admin
Action: DELETE /v1/ledgers/ledger_other_789
Expected: 200 OK, deletes resource
Authorization: Middleware checks DELETE on LEDGER
Result: Allowed (Admin can do anything)
```

---

## Implementation Tasks

### Task 1: Review Existing Endpoints ✅
- Read all Phase 1 & 2 endpoints
- Identify which are public
- Identify which need authorization

### Task 2: Integrate Middleware ✅
- Add AuthorizationMiddleware to FastAPI app
- Configure public endpoint list
- Test on sample endpoint

### Task 3: Add Route Decorators ✅
- Apply @require_client_ownership where needed
- Apply @require_permission where needed
- Apply @require_role if needed

### Task 4: E2E Test Suite ✅
- Test each endpoint with different roles
- Test cross-client isolation
- Test error responses
- Test audit trail

### Task 5: Regression Testing ✅
- Run all Phase 1 tests (should still pass)
- Run all Phase 2 tests (should still pass)
- Run all Phase 3.1 tests (should still pass)
- Run all Phase 3.2 tests (should still pass)

---

## Expected Test Coverage

### Endpoint Tests (10 endpoints × 3-5 scenarios each = 35-50 tests)

**Auth Endpoints (5)**:
- test_register_public_endpoint
- test_verify_email_public_endpoint
- test_login_public_endpoint
- test_logout_authenticated
- test_logout_unauthenticated
- test_refresh_authenticated
- test_refresh_unauthenticated
- test_me_own_user
- test_me_other_user_denied
- (More for edge cases)

**Device Endpoints (4)**:
- test_register_device_with_valid_key
- test_register_device_without_key
- test_list_devices_shows_own_only
- test_list_devices_cross_client_denied
- test_rotate_key_own_device
- test_rotate_key_other_device_denied
- test_status_own_device
- test_status_other_device_denied
- (More for edge cases)

### Authorization Tests (30-40 tests)
- Role-based access tests
- Permission-based access tests
- Cross-client isolation tests
- Admin override tests
- Error response tests

### Regression Tests (53 tests)
- All Phase 1 tests (16/16)
- All Phase 2 tests (8/8)
- All Phase 3.1 tests (29/29)

---

## Success Criteria

✅ All 10 endpoints properly protected  
✅ Public endpoints remain accessible  
✅ Protected endpoints require authentication  
✅ Authorization rules enforced correctly  
✅ Cross-client isolation verified  
✅ Admin override working  
✅ Error codes correct (401, 403, 400, 500)  
✅ All Phase 1 tests still pass  
✅ All Phase 2 tests still pass  
✅ All Phase 3.1 tests still pass  
✅ All Phase 3.2 tests still pass  
✅ 30-40 new E2E tests passing  
✅ Audit trail logging all decisions  

---

## Architecture Diagram

```
API Request
    ↓
Middleware:
├─ Public? → Skip auth → Endpoint
├─ Authenticated? 
│  ├─ No → 401
│  └─ Yes → Check permission?
│           ├─ No → 403
│           └─ Yes → Endpoint
│
Endpoint:
├─ Decorator: @require_role? → Check role
├─ Decorator: @require_permission? → Check permission
├─ Decorator: @require_client_ownership? → Check ownership
│
Business Logic:
├─ Query database
├─ Process request
├─ Log to audit trail
└─ Return response
```

---

## Files to Create/Modify

### New Files
- `tests/integration/test_e2e_authorization.py` (500+ lines)
  - End-to-end authorization tests
  - All 10 endpoints tested
  - Multiple role scenarios
  - Error case coverage

### Modified Files
- `cloudplatform/main.py`
  - Add AuthorizationMiddleware
  - Import middleware
  
- `cloudplatform/auth/routes.py`
  - Add decorators to protected endpoints
  
- `cloudplatform/keys/device_routes.py`
  - Add decorators to protected endpoints

### Documentation
- `docs_implementation/phase3_cerbos_authorization/PHASE3_3_E2E_RESULTS.md`
  - Test results
  - Coverage summary
  - Issues found and fixed

---

## Timeline

```
Task 1 (Review):        10 min
Task 2 (Middleware):    15 min
Task 3 (Decorators):    20 min
Task 4 (E2E Tests):     30 min
Task 5 (Regression):    15 min
Documentation:          10 min
                       ──────────
Total Estimated:        ~90-100 minutes (1.5-2 hours)
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking existing endpoints | Regression tests on all 53 prior tests |
| Performance impact from middleware | Benchmark and optimize if needed |
| Incorrect authorization logic | Comprehensive E2E test coverage |
| Cross-client isolation breach | Dedicated tests for this scenario |

---

## Sign-Off

**Status**: Ready to start Phase 3.3  
**Prerequisites**: Phase 3.1 & 3.2 complete  
**Estimated Completion**: 1.5-2 hours

---

**Next Step**: Implement E2E integration tests
