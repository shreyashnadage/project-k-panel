#!/bin/bash

#######################################################################
# Tally Sync Agent - Complete AWS Deployment Script
# Usage: ./scripts/deploy.sh
#######################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="ap-south-1"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
ECR_REPOSITORY="tally-sync-agent"
DOCKER_TAG="1.0.0"
STACK_NAME="tally-sync-agent-stack"
APP_NAME="tally-sync-agent"
DB_PASSWORD="${DB_PASSWORD:-}"
JWT_SECRET="${JWT_SECRET:-}"

#######################################################################
# Helper Functions
#######################################################################

print_header() {
    echo -e "\n${BLUE}========================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

#######################################################################
# Step 1: Validate Prerequisites
#######################################################################

validate_prerequisites() {
    print_header "STEP 1: VALIDATING PREREQUISITES"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI."
    fi
    print_success "AWS CLI found"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
    fi
    print_success "Docker found"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
    fi
    print_success "AWS credentials configured"

    # Get AWS Account ID if not provided
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo "AWS Account ID: $AWS_ACCOUNT_ID"
    fi
    print_success "AWS Account ID verified: $AWS_ACCOUNT_ID"

    # Check for required environment variables
    if [ -z "$DB_PASSWORD" ]; then
        print_error "DB_PASSWORD environment variable not set. Export it before running this script."
    fi
    print_success "DB_PASSWORD is set"

    if [ -z "$JWT_SECRET" ]; then
        print_error "JWT_SECRET environment variable not set. Export it before running this script."
    fi
    print_success "JWT_SECRET is set"
}

#######################################################################
# Step 2: Set Up ECR Repository
#######################################################################

setup_ecr() {
    print_header "STEP 2: SETTING UP ECR REPOSITORY"

    # Create ECR repository if it doesn't exist
    if ! aws ecr describe-repositories \
        --repository-names "$ECR_REPOSITORY" \
        --region "$AWS_REGION" &> /dev/null; then

        print_warning "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository \
            --repository-name "$ECR_REPOSITORY" \
            --region "$AWS_REGION" \
            --encryption-configuration encryptionType=AES256

        print_success "ECR repository created"
    else
        print_success "ECR repository already exists"
    fi

    # Get ECR login token
    print_warning "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    print_success "ECR login successful"
}

#######################################################################
# Step 3: Build and Push Docker Image
#######################################################################

build_and_push_image() {
    print_header "STEP 3: BUILDING AND PUSHING DOCKER IMAGE"

    DOCKER_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

    # Build Docker image
    print_warning "Building Docker image..."
    docker build \
        -t "$DOCKER_IMAGE:$DOCKER_TAG" \
        -t "$DOCKER_IMAGE:latest" \
        .

    print_success "Docker image built successfully"

    # Push to ECR
    print_warning "Pushing image to ECR (this may take a few minutes)..."
    docker push "$DOCKER_IMAGE:$DOCKER_TAG"
    docker push "$DOCKER_IMAGE:latest"

    print_success "Docker image pushed to ECR"
    echo "Image URI: $DOCKER_IMAGE:$DOCKER_TAG"
}

#######################################################################
# Step 4: Create Secrets Manager Entries
#######################################################################

create_secrets() {
    print_header "STEP 4: CREATING SECRETS MANAGER ENTRIES"

    # Create database password secret
    print_warning "Creating database password secret..."
    if aws secretsmanager describe-secret \
        --secret-id "$APP_NAME-db-password" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "Database secret already exists, skipping..."
    else
        aws secretsmanager create-secret \
            --name "$APP_NAME-db-password" \
            --secret-string "{\"password\":\"$DB_PASSWORD\"}" \
            --region "$AWS_REGION"
        print_success "Database password secret created"
    fi

    # Create JWT secret
    print_warning "Creating JWT secret..."
    if aws secretsmanager describe-secret \
        --secret-id "$APP_NAME-jwt-secret" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "JWT secret already exists, skipping..."
    else
        aws secretsmanager create-secret \
            --name "$APP_NAME-jwt-secret" \
            --secret-string "{\"secret\":\"$JWT_SECRET\"}" \
            --region "$AWS_REGION"
        print_success "JWT secret created"
    fi
}

#######################################################################
# Step 5: Deploy CloudFormation Stack
#######################################################################

deploy_cloudformation() {
    print_header "STEP 5: DEPLOYING CLOUDFORMATION STACK"

    # Validate template
    print_warning "Validating CloudFormation template..."
    aws cloudformation validate-template \
        --template-body file://cloudformation/infrastructure.yaml \
        --region "$AWS_REGION" > /dev/null

    print_success "CloudFormation template validated"

    # Check if stack already exists
    STACK_EXISTS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "")

    if [ -z "$STACK_EXISTS" ]; then
        print_warning "Creating CloudFormation stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://cloudformation/infrastructure.yaml \
            --parameters \
                ParameterKey=EnvironmentName,ParameterValue=production \
                ParameterKey=DesiredCount,ParameterValue=2 \
                ParameterKey=InstanceType,ParameterValue=t3.medium \
            --capabilities CAPABILITY_IAM \
            --region "$AWS_REGION"

        print_warning "Waiting for stack creation (this takes 10-15 minutes)..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION"
    else
        print_warning "Stack already exists with status: $STACK_EXISTS"
        if [ "$STACK_EXISTS" != "CREATE_COMPLETE" ] && [ "$STACK_EXISTS" != "UPDATE_COMPLETE" ]; then
            print_error "Stack is in status: $STACK_EXISTS. Please fix before deploying."
        fi
    fi

    print_success "CloudFormation stack deployed"
}

#######################################################################
# Step 6: Get Stack Outputs
#######################################################################

get_stack_outputs() {
    print_header "STEP 6: RETRIEVING STACK OUTPUTS"

    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
        --output text)

    RDS_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text)

    ASG_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`AutoScalingGroupName`].OutputValue' \
        --output text)

    if [ -z "$ALB_DNS" ] || [ -z "$RDS_ENDPOINT" ]; then
        print_error "Failed to retrieve stack outputs"
    fi

    echo "Load Balancer DNS: $ALB_DNS"
    echo "RDS Endpoint: $RDS_ENDPOINT"
    echo "Auto Scaling Group: $ASG_NAME"

    # Export for later use
    export ALB_DNS
    export RDS_ENDPOINT
    export ASG_NAME

    print_success "Stack outputs retrieved"
}

#######################################################################
# Step 7: Wait for Instances to be Healthy
#######################################################################

wait_for_instances() {
    print_header "STEP 7: WAITING FOR INSTANCES TO BE HEALTHY"

    print_warning "Waiting for instances to launch and pass health checks (5-10 minutes)..."

    MAX_ATTEMPTS=60
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        HEALTHY_COUNT=$(aws elbv2 describe-target-health \
            --target-group-arn "arn:aws:elasticloadbalancing:$AWS_REGION:$AWS_ACCOUNT_ID:targetgroup/$APP_NAME-tg/*" \
            --region "$AWS_REGION" \
            --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
            --output text 2>/dev/null || echo "0")

        if [ "$HEALTHY_COUNT" -ge 2 ]; then
            print_success "Instances are healthy ($HEALTHY_COUNT/2)"
            break
        fi

        ATTEMPT=$((ATTEMPT + 1))
        echo "Health check attempt $ATTEMPT/$MAX_ATTEMPTS... ($HEALTHY_COUNT/2 healthy)"
        sleep 10
    done

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        print_error "Instances failed to become healthy. Check EC2 and target group."
    fi
}

#######################################################################
# Step 8: Verify API Health
#######################################################################

verify_api_health() {
    print_header "STEP 8: VERIFYING API HEALTH"

    print_warning "Testing API health endpoint..."

    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "http://$ALB_DNS/health" 2>/dev/null || echo "000")
    HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
    BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" == "200" ]; then
        print_success "API health check passed (HTTP 200)"
        echo "Response: $BODY"
    else
        print_error "API health check failed (HTTP $HTTP_CODE)"
    fi
}

#######################################################################
# Step 9: Run Smoke Tests
#######################################################################

run_smoke_tests() {
    print_header "STEP 9: RUNNING SMOKE TESTS"

    print_warning "Running smoke tests against deployment..."

    bash scripts/smoke_tests.sh "$ALB_DNS"

    if [ $? -eq 0 ]; then
        print_success "Smoke tests passed"
    else
        print_error "Smoke tests failed"
    fi
}

#######################################################################
# Step 10: Generate Summary Report
#######################################################################

generate_summary() {
    print_header "STEP 10: DEPLOYMENT SUMMARY"

    cat > deployment_summary.txt << EOF
================================================================================
DEPLOYMENT SUMMARY
================================================================================

Project: Tally Sync Agent
Environment: Production (AWS ap-south-1)
Deployment Date: $(date)
Stack Name: $STACK_NAME

================================================================================
INFRASTRUCTURE
================================================================================

Load Balancer DNS: $ALB_DNS
API Endpoint: http://$ALB_DNS/v1

RDS Endpoint: $RDS_ENDPOINT
Database Name: tally_sync

Auto Scaling Group: $ASG_NAME
Instance Type: t3.medium
Desired Capacity: 2
Max Capacity: 10

================================================================================
NEXT STEPS
================================================================================

1. Run load tests:
   bash scripts/run_load_tests.sh "$ALB_DNS"

2. Monitor CloudWatch:
   aws cloudwatch get-metric-statistics \
     --namespace AWS/EC2 \
     --metric-name CPUUtilization \
     --dimensions Name=AutoScalingGroupName,Value=$ASG_NAME \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Average

3. Access Kibana dashboards at: http://<elasticsearch-endpoint>:5601

4. Monitor application logs:
   aws logs tail /aws/ec2/tally-sync-agent --follow

================================================================================
DEPLOYMENT STATUS: SUCCESS ✅
================================================================================
EOF

    cat deployment_summary.txt
    print_success "Deployment summary saved to deployment_summary.txt"
}

#######################################################################
# Main Execution
#######################################################################

main() {
    print_header "TALLY SYNC AGENT - AWS PRODUCTION DEPLOYMENT"
    echo "Starting deployment to AWS region: $AWS_REGION"
    echo "Deployment started: $(date)"
    echo ""

    validate_prerequisites
    setup_ecr
    build_and_push_image
    create_secrets
    deploy_cloudformation
    get_stack_outputs
    wait_for_instances
    verify_api_health
    run_smoke_tests
    generate_summary

    print_header "🚀 DEPLOYMENT COMPLETE ✅"
    echo ""
    echo "Your application is now running at: http://$ALB_DNS"
    echo ""
    echo "To run load tests, execute:"
    echo "  bash scripts/run_load_tests.sh $ALB_DNS"
    echo ""
}

# Run main function
main "$@"
