#!/bin/bash

################################################################################
# TALLY SYNC AGENT - COMPLETE ONBOARDING TEST
#
# Tests the full client journey:
# 1. Portal Registration
# 2. Device Registration
# 3. First Data Sync
# 4. Verify Statistics
#
# Usage: bash test_complete_onboarding.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API="http://15.206.90.21:8000"
TIMESTAMP=$(date +%s%N | cut -b1-13)  # Millisecond timestamp
TEST_EMAIL="test-$TIMESTAMP@tally-sync.com"
TEST_COMPANY="Test Company $TIMESTAMP"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TALLY SYNC AGENT - COMPLETE ONBOARDING TEST                   ║"
echo "║  Backend: $API                    ║"
echo "║  Test ID: $TIMESTAMP                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to print step
print_step() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ STEP $1: $2${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
}

# Function to print result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Function to extract JSON value
get_json_value() {
    echo "$1" | python -c "import sys, json; print(json.load(sys.stdin).get('$2', ''))" 2>/dev/null
}

################################################################################
# STEP 1: PORTAL REGISTRATION
################################################################################

print_step "1" "PORTAL REGISTRATION"

echo "Registering client:"
echo "  Company: $TEST_COMPANY"
echo "  Email: $TEST_EMAIL"
echo "  Phone: +91 9876543210"
echo "  GST: 18AABCU1234567Z5"

REGISTER_RESPONSE=$(curl -s -X POST "$API/v1/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"company_name\": \"$TEST_COMPANY\",
    \"email\": \"$TEST_EMAIL\",
    \"phone\": \"+91 9876543210\",
    \"gst_id\": \"18AABCU1234567Z5\"
  }")

# Check if response is valid JSON
if ! echo "$REGISTER_RESPONSE" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${RED}❌ Invalid response from registration endpoint${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

# Extract values
CLIENT_ID=$(get_json_value "$REGISTER_RESPONSE" "client_id")
INSTALL_KEY=$(get_json_value "$REGISTER_RESPONSE" "installation_key")

if [ -z "$CLIENT_ID" ] || [ -z "$INSTALL_KEY" ]; then
    echo -e "${RED}❌ Failed to extract client_id or installation_key${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

echo ""
echo "Registration Response:"
echo "$REGISTER_RESPONSE" | python -m json.tool

echo ""
echo -e "${GREEN}✅ Client registered successfully${NC}"
echo "  CLIENT_ID: $CLIENT_ID"
echo "  INSTALL_KEY: $INSTALL_KEY"

################################################################################
# STEP 2: DEVICE REGISTRATION
################################################################################

print_step "2" "DEVICE REGISTRATION"

echo "Registering device:"
echo "  Installation Key: $INSTALL_KEY"
echo "  Device Name: TEST-OFFICE-PC-01"
echo "  OS Version: Windows 11 Build 26200"
echo "  Agent Version: 0.4.0"

DEVICE_RESPONSE=$(curl -s -X POST "$API/v1/register-device" \
  -H "Content-Type: application/json" \
  -d "{
    \"installation_key\": \"$INSTALL_KEY\",
    \"device_name\": \"TEST-OFFICE-PC-01\",
    \"os_version\": \"Windows 11 Build 26200\",
    \"agent_version\": \"0.4.0\"
  }")

# Check if response is valid JSON
if ! echo "$DEVICE_RESPONSE" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${RED}❌ Invalid response from device registration endpoint${NC}"
    echo "Response: $DEVICE_RESPONSE"
    exit 1
fi

# Extract values
DEVICE_ID=$(get_json_value "$DEVICE_RESPONSE" "device_id")
API_KEY=$(get_json_value "$DEVICE_RESPONSE" "api_key")
REGISTRATION_TOKEN=$(get_json_value "$DEVICE_RESPONSE" "registration_token")

if [ -z "$DEVICE_ID" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Failed to extract device_id or api_key${NC}"
    echo "Response: $DEVICE_RESPONSE"
    exit 1
fi

echo ""
echo "Device Registration Response:"
echo "$DEVICE_RESPONSE" | python -m json.tool

echo ""
echo -e "${GREEN}✅ Device registered successfully${NC}"
echo "  DEVICE_ID: $DEVICE_ID"
echo "  API_KEY: ${API_KEY:0:20}..."
echo "  REGISTRATION_TOKEN: ${REGISTRATION_TOKEN:0:20}..."

################################################################################
# STEP 3: FIRST DATA SYNC
################################################################################

print_step "3" "FIRST DATA SYNC"

echo "Sending first sync:"
echo "  Ledgers: 150"
echo "  Vouchers: 500"
echo "  Total Records: 650"

SYNC_RESPONSE=$(curl -s -X POST "$API/v1/sync-with-client" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "x-client-id: $CLIENT_ID" \
  -H "x-device-id: $DEVICE_ID" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"device_id\": \"$DEVICE_ID\",
    \"extracted_ledgers\": 150,
    \"extracted_vouchers\": 500,
    \"raw_data\": {}
  }")

# Check if response is valid JSON
if ! echo "$SYNC_RESPONSE" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${RED}❌ Invalid response from sync endpoint${NC}"
    echo "Response: $SYNC_RESPONSE"
    exit 1
fi

# Extract values
SYNC_ID=$(get_json_value "$SYNC_RESPONSE" "sync_id")
RECORDS_RECEIVED=$(get_json_value "$SYNC_RESPONSE" "records_received")
SYNC_STATUS=$(get_json_value "$SYNC_RESPONSE" "status")

if [ -z "$SYNC_ID" ]; then
    echo -e "${RED}❌ Failed to extract sync_id${NC}"
    echo "Response: $SYNC_RESPONSE"
    exit 1
fi

echo ""
echo "Sync Response:"
echo "$SYNC_RESPONSE" | python -m json.tool

echo ""
echo -e "${GREEN}✅ First sync completed successfully${NC}"
echo "  SYNC_ID: $SYNC_ID"
echo "  RECORDS_RECEIVED: $RECORDS_RECEIVED"
echo "  STATUS: $SYNC_STATUS"

################################################################################
# STEP 4: VERIFY STATISTICS
################################################################################

print_step "4" "VERIFY STATISTICS"

echo "Fetching client statistics..."

STATS_RESPONSE=$(curl -s -X GET "$API/v1/clients/$CLIENT_ID/stats" \
  -H "Content-Type: application/json")

# Check if response is valid JSON
if ! echo "$STATS_RESPONSE" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${RED}❌ Invalid response from stats endpoint${NC}"
    echo "Response: $STATS_RESPONSE"
    exit 1
fi

# Extract values
TOTAL_SYNCS=$(get_json_value "$STATS_RESPONSE" "total_syncs")
TOTAL_RECORDS=$(get_json_value "$STATS_RESPONSE" "total_records")
TOTAL_LEDGERS=$(get_json_value "$STATS_RESPONSE" "total_ledgers")
TOTAL_VOUCHERS=$(get_json_value "$STATS_RESPONSE" "total_vouchers")

echo ""
echo "Statistics Response:"
echo "$STATS_RESPONSE" | python -m json.tool

echo ""
echo -e "${GREEN}✅ Statistics retrieved successfully${NC}"
echo "  TOTAL_SYNCS: $TOTAL_SYNCS"
echo "  TOTAL_RECORDS: $TOTAL_RECORDS"
echo "  TOTAL_LEDGERS: $TOTAL_LEDGERS"
echo "  TOTAL_VOUCHERS: $TOTAL_VOUCHERS"

################################################################################
# VERIFICATION
################################################################################

print_step "5" "FINAL VERIFICATION"

PASSED=0
FAILED=0

# Check client_id
if [ ! -z "$CLIENT_ID" ]; then
    echo -e "${GREEN}✅ client_id generated: $CLIENT_ID${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ client_id not generated${NC}"
    ((FAILED++))
fi

# Check installation_key
if [[ "$INSTALL_KEY" =~ ^TSA-2026- ]]; then
    echo -e "${GREEN}✅ installation_key valid format: $INSTALL_KEY${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ installation_key invalid format: $INSTALL_KEY${NC}"
    ((FAILED++))
fi

# Check device_id
if [ ! -z "$DEVICE_ID" ]; then
    echo -e "${GREEN}✅ device_id generated: $DEVICE_ID${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ device_id not generated${NC}"
    ((FAILED++))
fi

# Check sync_id
if [ ! -z "$SYNC_ID" ]; then
    echo -e "${GREEN}✅ sync_id generated: $SYNC_ID${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ sync_id not generated${NC}"
    ((FAILED++))
fi

# Check records received
if [ "$RECORDS_RECEIVED" = "650" ]; then
    echo -e "${GREEN}✅ 650 records received (correct)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Incorrect records received: $RECORDS_RECEIVED (expected 650)${NC}"
    ((FAILED++))
fi

# Check total_syncs
if [ "$TOTAL_SYNCS" = "1" ]; then
    echo -e "${GREEN}✅ total_syncs = 1 (correct)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Incorrect total_syncs: $TOTAL_SYNCS (expected 1)${NC}"
    ((FAILED++))
fi

# Check total_records
if [ "$TOTAL_RECORDS" = "650" ]; then
    echo -e "${GREEN}✅ total_records = 650 (correct)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Incorrect total_records: $TOTAL_RECORDS (expected 650)${NC}"
    ((FAILED++))
fi

################################################################################
# SUMMARY
################################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TEST SUMMARY                                                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

echo ""
echo "Test Data (for reference):"
echo "  Client Email: $TEST_EMAIL"
echo "  Client ID: $CLIENT_ID"
echo "  Installation Key: $INSTALL_KEY"
echo "  Device ID: $DEVICE_ID"
echo "  API Key: ${API_KEY:0:20}..."

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ ALL TESTS PASSED - ONBOARDING SYSTEM WORKING!             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ❌ SOME TESTS FAILED - CHECK ABOVE FOR DETAILS                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
fi
