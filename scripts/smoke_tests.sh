#!/bin/bash

#######################################################################
# Smoke Tests - Quick validation of deployed system
#######################################################################

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ALB_DNS>"
    echo "Example: $0 tally-sync-agent-alb-123456.ap-south-1.elb.amazonaws.com"
    exit 1
fi

ALB_DNS=$1
API_BASE="http://$ALB_DNS"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
TEST_EMAIL="smoke_test_${TIMESTAMP}@test.com"
TEST_PASSWORD="TestPassword123!"
TEST_COMPANY="Smoke Test Company"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

print_test() {
    echo -e "\n${BLUE}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    PASSED=$((PASSED + 1))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    FAILED=$((FAILED + 1))
}

#######################################################################
# Test 1: Health Check
#######################################################################

print_test "Health Check Endpoint"

RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" == "200" ]; then
    print_pass "Health check returned 200"
else
    print_fail "Health check returned $HTTP_CODE (expected 200)"
fi

#######################################################################
# Test 2: User Registration
#######################################################################

print_test "User Registration"

REGISTRATION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_BASE/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"company_name\": \"$TEST_COMPANY\",
        \"email\": \"$TEST_EMAIL\",
        \"phone\": \"9999999999\",
        \"password\": \"$TEST_PASSWORD\"
    }")

REG_HTTP=$(echo "$REGISTRATION_RESPONSE" | tail -n1)
REG_BODY=$(echo "$REGISTRATION_RESPONSE" | head -n-1)

if [ "$REG_HTTP" == "200" ]; then
    CLIENT_ID=$(echo "$REG_BODY" | grep -o '"client_id":"[^"]*"' | cut -d'"' -f4)
    VERIFICATION_TOKEN=$(echo "$REG_BODY" | grep -o '"verification_token":"[^"]*"' | cut -d'"' -f4)
    print_pass "User registration returned 200 (client_id: ${CLIENT_ID:0:20}...)"
else
    print_fail "User registration returned $REG_HTTP (expected 200)"
    echo "Response: $REG_BODY"
fi

#######################################################################
# Test 3: User Login
#######################################################################

print_test "User Login"

LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_BASE/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }")

LOGIN_HTTP=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$LOGIN_HTTP" == "200" ]; then
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    print_pass "User login returned 200 (token: ${ACCESS_TOKEN:0:20}...)"
else
    print_fail "User login returned $LOGIN_HTTP (expected 200)"
    echo "Response: $LOGIN_BODY"
fi

#######################################################################
# Test 4: Get Current User
#######################################################################

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "Get Current User"

    ME_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X GET "$API_BASE/v1/auth/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    ME_HTTP=$(echo "$ME_RESPONSE" | tail -n1)
    ME_BODY=$(echo "$ME_RESPONSE" | head -n-1)

    if [ "$ME_HTTP" == "200" ]; then
        print_pass "Get current user returned 200"
    else
        print_fail "Get current user returned $ME_HTTP (expected 200)"
    fi
fi

#######################################################################
# Test 5: Device Registration
#######################################################################

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "Device Registration"

    DEVICE_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_BASE/v1/devices/register" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"device_name\": \"Test Device\",
            \"os_version\": \"Windows 11\",
            \"agent_version\": \"1.0.0\",
            \"installation_key\": \"TSA-TESTKEY-$(date +%s)\"
        }")

    DEVICE_HTTP=$(echo "$DEVICE_RESPONSE" | tail -n1)
    DEVICE_BODY=$(echo "$DEVICE_RESPONSE" | head -n-1)

    if [ "$DEVICE_HTTP" == "200" ]; then
        DEVICE_ID=$(echo "$DEVICE_BODY" | grep -o '"device_id":"[^"]*"' | cut -d'"' -f4)
        print_pass "Device registration returned 200 (device_id: ${DEVICE_ID:0:20}...)"
    else
        print_fail "Device registration returned $DEVICE_HTTP (expected 200)"
        echo "Response: $DEVICE_BODY"
    fi
fi

#######################################################################
# Test 6: List Devices
#######################################################################

if [ -n "$ACCESS_TOKEN" ]; then
    print_test "List Devices"

    LIST_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X GET "$API_BASE/v1/devices/list" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    LIST_HTTP=$(echo "$LIST_RESPONSE" | tail -n1)
    LIST_BODY=$(echo "$LIST_RESPONSE" | head -n-1)

    if [ "$LIST_HTTP" == "200" ]; then
        DEVICE_COUNT=$(echo "$LIST_BODY" | grep -o '"device_id"' | wc -l)
        print_pass "List devices returned 200 ($DEVICE_COUNT devices)"
    else
        print_fail "List devices returned $LIST_HTTP (expected 200)"
    fi
fi

#######################################################################
# Test 7: Unauthorized Access (No Token)
#######################################################################

print_test "Unauthorized Access (No Token)"

UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$API_BASE/v1/devices/list")

UNAUTH_HTTP=$(echo "$UNAUTH_RESPONSE" | tail -n1)

if [ "$UNAUTH_HTTP" == "401" ]; then
    print_pass "Unauthorized access correctly returned 401"
else
    print_fail "Unauthorized access returned $UNAUTH_HTTP (expected 401)"
fi

#######################################################################
# Test 8: Invalid Login
#######################################################################

print_test "Invalid Credentials"

INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_BASE/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"nonexistent@test.com\",
        \"password\": \"wrongpassword\"
    }")

INVALID_HTTP=$(echo "$INVALID_RESPONSE" | tail -n1)

if [ "$INVALID_HTTP" == "401" ]; then
    print_pass "Invalid credentials correctly returned 401"
else
    print_fail "Invalid credentials returned $INVALID_HTTP (expected 401)"
fi

#######################################################################
# Summary
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}SMOKE TEST SUMMARY${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo -e "Pass Rate: ${BLUE}${PASS_RATE}%${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL SMOKE TESTS PASSED${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}\n"
    exit 1
fi
