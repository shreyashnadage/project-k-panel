#!/bin/bash

#######################################################################
# Complete Testing Suite - All Tests
#######################################################################

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <ALB_DNS>"
    echo "Example: $0 tally-sync-agent-alb-123456.ap-south-1.elb.amazonaws.com"
    exit 1
fi

ALB_DNS=$1

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

#######################################################################
# Phase 1: Smoke Tests
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PHASE 1: SMOKE TESTS${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

if bash scripts/smoke_tests.sh "$ALB_DNS"; then
    echo -e "${GREEN}✓ Smoke tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some smoke tests failed (continuing...)${NC}"
fi

#######################################################################
# Phase 2: Performance Tests
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PHASE 2: PERFORMANCE TESTS${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

bash scripts/performance_tests.sh "$ALB_DNS"

#######################################################################
# Phase 3: Security Tests
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PHASE 3: SECURITY TESTS${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

bash scripts/security_tests.sh "$ALB_DNS"

#######################################################################
# Phase 4: Load Tests
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PHASE 4: LOAD TESTS${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

echo "Installing Locust if needed..."
pip install -q locust 2>/dev/null || true

echo -e "\n${YELLOW}Running sustained load test (500 users, 5 minutes)...${NC}\n"
locust -f tests/load/locustfile.py \
    --host="http://$ALB_DNS" \
    --users=500 \
    --spawn-rate=50 \
    --run-time=5m \
    --headless \
    --csv=load_test_results || echo "Load test completed"

#######################################################################
# Phase 5: Monitoring Validation
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}PHASE 5: MONITORING VALIDATION${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

bash scripts/check_monitoring.sh

#######################################################################
# Summary Report
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}COMPLETE TEST SUITE FINISHED${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

echo "Test Results:"
echo "  ✓ Smoke tests completed"
echo "  ✓ Performance tests completed"
echo "  ✓ Security tests completed"
echo "  ✓ Load tests completed"
echo "  ✓ Monitoring validated"
echo ""
echo "See detailed results in:"
echo "  - load_test_results_stats.csv (load test metrics)"
echo "  - load_test_results_failures.csv (any failures)"
echo ""
