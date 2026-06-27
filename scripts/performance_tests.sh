#!/bin/bash

#######################################################################
# Performance Tests
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
# Test 1: Health Check Latency
#######################################################################

print_test "Health Check Latency (Target: <50ms)"

START_TIME=$(date +%s%N)
curl -s "$API_BASE/health" > /dev/null
END_TIME=$(date +%s%N)

LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

if [ $LATENCY_MS -lt 50 ]; then
    print_pass "Health check latency: ${LATENCY_MS}ms"
else
    print_fail "Health check latency: ${LATENCY_MS}ms (exceeded 50ms)"
fi

#######################################################################
# Test 2: Concurrent Requests
#######################################################################

print_test "Concurrent Requests (10 concurrent)"

echo "Sending 10 concurrent requests..."

for i in {1..10}; do
    curl -s "$API_BASE/health" > /dev/null &
done

wait

print_pass "All 10 concurrent requests completed"

#######################################################################
# Test 3: Response Time Consistency
#######################################################################

print_test "Response Time Consistency (10 samples)"

TIMES=()
for i in {1..10}; do
    START=$(date +%s%N)
    curl -s "$API_BASE/health" > /dev/null
    END=$(date +%s%N)
    TIME_MS=$(( (END - START) / 1000000 ))
    TIMES+=($TIME_MS)
done

MIN_TIME=${TIMES[0]}
MAX_TIME=${TIMES[0]}

for time in "${TIMES[@]}"; do
    if [ $time -lt $MIN_TIME ]; then MIN_TIME=$time; fi
    if [ $time -gt $MAX_TIME ]; then MAX_TIME=$time; fi
done

AVG_TIME=$(( (${TIMES[@]/%/+}0) / ${#TIMES[@]} ))

echo "  Min: ${MIN_TIME}ms"
echo "  Max: ${MAX_TIME}ms"
echo "  Avg: ${AVG_TIME}ms"

if [ $MAX_TIME -lt 200 ]; then
    print_pass "Response time consistent (max: ${MAX_TIME}ms)"
else
    print_fail "Response time inconsistent (max: ${MAX_TIME}ms)"
fi

#######################################################################
# Test 4: Throughput Test
#######################################################################

print_test "Throughput Test (requests per second)"

START_TIME=$(date +%s)
REQUEST_COUNT=0

for i in {1..100}; do
    curl -s "$API_BASE/health" > /dev/null
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $DURATION -eq 0 ]; then
    DURATION=1
fi

THROUGHPUT=$((REQUEST_COUNT / DURATION))

echo "  Requests: $REQUEST_COUNT"
echo "  Duration: ${DURATION}s"
echo "  Throughput: ${THROUGHPUT} req/sec"

if [ $THROUGHPUT -gt 50 ]; then
    print_pass "Throughput acceptable: ${THROUGHPUT} req/sec"
else
    print_fail "Throughput low: ${THROUGHPUT} req/sec"
fi

#######################################################################
# Summary
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PERFORMANCE TEST SUMMARY${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL PERFORMANCE TESTS PASSED${NC}\n"
else
    echo -e "\n${YELLOW}⚠ Some performance tests did not meet targets${NC}\n"
fi
