#!/bin/bash

#######################################################################
# AWS Deployment Setup Script
# Configures environment and verifies AWS CLI access
#######################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

#######################################################################
# Check AWS CLI
#######################################################################

print_header "STEP 1: CHECKING AWS CLI INSTALLATION"

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found!"
    echo "Please install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

AWS_CLI_VERSION=$(aws --version)
print_success "AWS CLI installed: $AWS_CLI_VERSION"

#######################################################################
# Check AWS Credentials
#######################################################################

print_header "STEP 2: CHECKING AWS CREDENTIALS"

if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured!"
    echo ""
    echo "Please configure AWS CLI with:"
    echo "  aws configure"
    echo ""
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region: ap-south-1"
    echo "  - Default output format: json"
    exit 1
fi

# Get account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ARN=$(aws sts get-caller-identity --query Arn --output text)
CURRENT_REGION=$(aws configure get region)

print_success "AWS credentials configured"
echo "Account ID: $ACCOUNT_ID"
echo "ARN: $ARN"
echo "Region: $CURRENT_REGION"

#######################################################################
# Verify Required Permissions
#######################################################################

print_header "STEP 3: VERIFYING AWS PERMISSIONS"

REQUIRED_SERVICES=(
    "ec2"
    "rds"
    "elasticloadbalancing"
    "autoscaling"
    "cloudformation"
    "ecr"
    "secretsmanager"
    "cloudwatch"
)

print_info "Checking permissions for required services..."

MISSING_PERMS=0

for service in "${REQUIRED_SERVICES[@]}"; do
    if aws "$service" describe-regions --region-names "$CURRENT_REGION" &> /dev/null 2>&1; then
        print_success "$service access verified"
    else
        print_error "$service access denied (may need IAM permissions)"
        MISSING_PERMS=$((MISSING_PERMS + 1))
    fi
done

if [ $MISSING_PERMS -gt 0 ]; then
    print_error "Some services cannot be accessed. Check IAM permissions."
else
    print_success "All required services accessible"
fi

#######################################################################
# Check Docker
#######################################################################

print_header "STEP 4: CHECKING DOCKER INSTALLATION"

if ! command -v docker &> /dev/null; then
    print_error "Docker not found!"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

DOCKER_VERSION=$(docker --version)
print_success "Docker installed: $DOCKER_VERSION"

if ! docker ps &> /dev/null; then
    print_error "Docker daemon not running!"
    echo "Please start Docker and try again."
    exit 1
fi

print_success "Docker daemon running"

#######################################################################
# Set Environment Variables
#######################################################################

print_header "STEP 5: CONFIGURING ENVIRONMENT VARIABLES"

print_info "Setting up required environment variables..."

# AWS Account ID
export AWS_ACCOUNT_ID="$ACCOUNT_ID"
export AWS_REGION="${CURRENT_REGION:-ap-south-1}"

print_success "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"
print_success "AWS_REGION: $AWS_REGION"

# Generate secure passwords if not provided
if [ -z "$DB_PASSWORD" ]; then
    print_info "Generating database password..."
    DB_PASSWORD=$(openssl rand -base64 32)
    export DB_PASSWORD
    print_success "DB_PASSWORD generated"
fi

if [ -z "$JWT_SECRET" ]; then
    print_info "Generating JWT secret..."
    JWT_SECRET=$(openssl rand -base64 32)
    export JWT_SECRET
    print_success "JWT_SECRET generated"
fi

#######################################################################
# Create .env File
#######################################################################

print_header "STEP 6: CREATING DEPLOYMENT CONFIGURATION"

cat > .env.deployment << EOF
# AWS Deployment Configuration
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
AWS_REGION=$AWS_REGION
APP_NAME=tally-sync-agent
STACK_NAME=tally-sync-agent-stack
ECR_REPOSITORY=tally-sync-agent
DOCKER_TAG=1.0.0

# Database Configuration
DB_PASSWORD=$DB_PASSWORD

# JWT Configuration
JWT_SECRET=$JWT_SECRET

# Deployment Settings
DESIRED_CAPACITY=2
MIN_CAPACITY=2
MAX_CAPACITY=10
INSTANCE_TYPE=t3.medium

# Deployment Date
DEPLOYMENT_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

print_success ".env.deployment created"

#######################################################################
# Save Credentials Securely
#######################################################################

print_header "STEP 7: SAVING DEPLOYMENT CREDENTIALS"

mkdir -p .deployment

cat > .deployment/credentials.sh << EOF
#!/bin/bash
# Source this file before running deployment

export AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
export AWS_REGION=$AWS_REGION
export DB_PASSWORD="$DB_PASSWORD"
export JWT_SECRET="$JWT_SECRET"
export APP_NAME=tally-sync-agent
export STACK_NAME=tally-sync-agent-stack
export ECR_REPOSITORY=tally-sync-agent
export DOCKER_TAG=1.0.0
EOF

chmod 600 .deployment/credentials.sh
print_success "Credentials saved to .deployment/credentials.sh"
print_info "⚠️  KEEP THIS FILE SECURE - It contains sensitive data"

#######################################################################
# Summary
#######################################################################

print_header "✅ SETUP COMPLETE"

cat << EOF

Your AWS environment is ready for deployment!

ACCOUNT DETAILS:
  Account ID: $ACCOUNT_ID
  Region: $AWS_REGION
  ARN: $ARN

NEXT STEPS:
1. Review deployment parameters:
   cat .env.deployment

2. Start deployment:
   source .deployment/credentials.sh
   bash scripts/deploy.sh

3. After deployment, run tests:
   bash scripts/smoke_tests.sh <ALB_DNS>
   bash scripts/run_load_tests.sh <ALB_DNS>

IMPORTANT:
  - Keep .deployment/credentials.sh secure
  - Don't commit .deployment/ to git
  - Save DB_PASSWORD and JWT_SECRET somewhere safe

Database Password: ${DB_PASSWORD:0:20}...
JWT Secret: ${JWT_SECRET:0:20}...

Ready to deploy? Run:
  source .deployment/credentials.sh && bash scripts/deploy.sh

EOF
