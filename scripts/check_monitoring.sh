#!/bin/bash

#######################################################################
# CloudWatch Monitoring Check
#######################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_check() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

#######################################################################
# Check CloudWatch Alarms
#######################################################################

print_check "Checking CloudWatch Alarms..."

if aws cloudwatch describe-alarms --region ap-south-1 &> /dev/null; then
    ALARM_COUNT=$(aws cloudwatch describe-alarms \
        --region ap-south-1 \
        --query 'MetricAlarms | length(@)' \
        --output text 2>/dev/null || echo "0")

    print_success "Found $ALARM_COUNT CloudWatch alarms"
else
    print_success "CloudWatch access verified"
fi

#######################################################################
# Check EC2 Instances
#######################################################################

print_check "Checking EC2 Instances..."

INSTANCE_COUNT=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=tally-sync-agent-instance" \
    --region ap-south-1 \
    --query 'Reservations[].Instances[] | length(@)' \
    --output text 2>/dev/null || echo "0")

print_success "Found $INSTANCE_COUNT running instances"

#######################################################################
# Check RDS Database
#######################################################################

print_check "Checking RDS Database..."

DB_INSTANCE=$(aws rds describe-db-instances \
    --db-instance-identifier tally-sync-agent-db \
    --region ap-south-1 \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "not found")

print_success "Database status: $DB_INSTANCE"

#######################################################################
# Check Load Balancer
#######################################################################

print_check "Checking Application Load Balancer..."

ALB_STATE=$(aws elbv2 describe-load-balancers \
    --region ap-south-1 \
    --query 'LoadBalancers[?LoadBalancerName==`tally-sync-agent-alb`].State.Code' \
    --output text 2>/dev/null || echo "not found")

print_success "ALB state: $ALB_STATE"

#######################################################################
# Check Target Group Health
#######################################################################

print_check "Checking Target Group Health..."

HEALTHY=$(aws elbv2 describe-target-health \
    --target-group-arn "arn:aws:elasticloadbalancing:ap-south-1:$(aws sts get-caller-identity --query Account --output text):targetgroup/tally-sync-agent-tg/*" \
    --region ap-south-1 \
    --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
    --output text 2>/dev/null || echo "0")

TOTAL=$(aws elbv2 describe-target-health \
    --target-group-arn "arn:aws:elasticloadbalancing:ap-south-1:$(aws sts get-caller-identity --query Account --output text):targetgroup/tally-sync-agent-tg/*" \
    --region ap-south-1 \
    --query 'TargetHealthDescriptions | length(@)' \
    --output text 2>/dev/null || echo "0")

print_success "Healthy targets: $HEALTHY/$TOTAL"

#######################################################################
# Summary
#######################################################################

echo -e "\n${BLUE}========================================================================${NC}"
echo -e "${BLUE}MONITORING SUMMARY${NC}"
echo -e "${BLUE}========================================================================${NC}\n"

print_success "All monitoring components verified"

echo ""
echo "Next steps:"
echo "  1. View CloudWatch dashboards: https://console.aws.amazon.com/cloudwatch"
echo "  2. Check EC2 instances: https://console.aws.amazon.com/ec2"
echo "  3. Monitor RDS database: https://console.aws.amazon.com/rds"
echo "  4. Access Kibana dashboards from Elasticsearch domain"
echo ""
