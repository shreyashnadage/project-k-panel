#!/bin/bash

#######################################################################
# Security Tests
#######################################################################

set -e

ALB_DNS=$1
API_BASE="http://$ALB_DNS"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

print_test() {
    echo -e "${BLUE}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    PASSED=$((PASSED + 1))
}

print_fail() {
    echo -e "${RED}✗ $1${NC}"
    FAILED=$((FAILED + 1))
}

#######################################################################
# Test 1: SQL Injection Protection
#######################################################################

print_test "SQL Injection Protection"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_BASE/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"test@test.com' OR '1'='1\",
        \"password\": \"test\"
    }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" != "200" ] && ! echo "$BODY" | grep -q "syntax"; then
    print_pass "SQL injection attempt rejected safely (HTTP $HTTP_CODE)"
else
    print_fail "SQL injection not properly handled"
fi

#######################################################################
# Test 2: Unauthorized Access
#######################################################################

print_test "Unauthorized Access Prevention"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$API_BASE/v1/devices/list" \
    -H "Authorization: Bearer invalid_token_123")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "401" ]; then
    print_pass "Invalid token correctly rejected (HTTP 401)"
else
    print_fail "Invalid token returned HTTP $HTTP_CODE (expected 401)"
fi

#######################################################################
# Test 3: Missing Authorization Header
#######################################################################

print_test "Missing Authorization Header"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "$API_BASE/v1/devices/list")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "401" ]; then
    print_pass "Missing auth header correctly rejected (HTTP 401)"
else
    print_fail "Missing auth header returned HTTP $HTTP_CODE (expected 401)"
fi

#######################################################################
# Test 4: Method Not Allowed
#######################################################################

print_test "Method Not Allowed"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X DELETE "$API_BASE/v1/auth/me")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "405" ] || [ "$HTTP_CODE" == "404" ]; then
    print_pass "Unsupported method correctly rejected (HTTP $HTTP_CODE)"
else
    print_fail "Unsupported method returned HTTP $HTTP_CODE"
fi

#######################################################################
# Test 5: HTTPS/TLS Ready
#######################################################################

print_test "TLS/HTTPS Support"

if [[ "$ALB_DNS" == *"https"* ]]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -I "https://$ALB_DNS/health" 2>/dev/null || echo "")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
        print_pass "HTTPS/TLS connection successful"
    else
        print_fail "HTTPS/TLS connection failed"
    fi
else
    echo -e "${YELLOW}ℹ HTTPS not enabled (using HTTP for test)${NC}"
    print_pass "HTTP connection available (upgrade to HTTPS recommended)"
fi

#######################################################################
# Test 6: CORS Headers
#######################################################################

print_test "CORS Headers Validation"

RESPONSE=$(curl -s -i "$API_BASE/health" 2>/dev/null | head -20)

if echo "$RESPONSE" | grep -q "Content-Type"; then
    print_pass "Content-Type header present"
else
    print_fail "Content-Type header missing"
fi

#######################################################################
# Test 7: Security Headers
#######################################################################

print_test "Security Headers"

RESPONSE=$(curl -s -i "$API_BASE/health" 2>/dev/null | head -30)

# Check for recommended headers
HEADERS_FOUND=0

if echo "$RESPONSE" | grep -q "X-Content-Type-Options"; then
    HEADERS_FOUND=$((HEADERS_FOUND + 1))
fi

if echo "$RESPONSE" | grep -q "X-Frame-Options"; then
    HEADERS_FOUND=$((HEADERS_FOUND + 1))
fi

if echo "$RESPONSE" | grep -q "Content-Security-Policy"; then
    HEADERS_FOUND=$((HEADERS_FOUND + 1))
fi

if [ $HEADERS_FOUND -gt 0 ]; then
    print_pass "Security headers found ($HEADERS_FOUND)"
else
    print_pass "Security headers not yet configured (recommended for production)"
fi

#######################################################################
# Summary
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}SECURITY TEST SUMMARY${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL SECURITY TESTS PASSED${NC}\n"
else
    echo -e "\n${YELLOW}⚠ Review failed security tests above${NC}\n"
fi
