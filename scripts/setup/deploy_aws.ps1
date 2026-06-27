# scripts/setup/deploy_aws.ps1
# PowerShell script to deploy tally-sync AWS infrastructure

$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "      Tally Sync AWS CLI Auto-Deployer" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# 1. Check AWS Credentials
Write-Host "Checking AWS CLI connection..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "Connected as IAM User: $($identity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS CLI is not configured or credentials are invalid." -ForegroundColor Red
    Write-Host "Please run 'aws configure' first to input your AWS Access Key and Secret Key." -ForegroundColor Yellow
    Exit 1
}

# 2. Get Default VPC ID
Write-Host "Retrieving default VPC..." -ForegroundColor Yellow
$VPC_ID = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text
if ($VPC_ID -eq "None" -or -not $VPC_ID) {
    Write-Host "ERROR: Default VPC not found. Please ensure you have a default VPC in your region." -ForegroundColor Red
    Exit 1
}
Write-Host "Using Default VPC: $VPC_ID" -ForegroundColor Green

# 3. Create/Retrieve Security Groups
Write-Host "Setting up Security Groups..." -ForegroundColor Yellow

# API SG
$API_SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=tally-sync-api-sg" "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[0].GroupId" --output text
if ($API_SG_ID -eq "None" -or -not $API_SG_ID) {
    Write-Host "Creating tally-sync-api-sg..." -ForegroundColor Cyan
    $API_SG_ID = aws ec2 create-security-group --group-name tally-sync-api-sg --description "FastAPI EC2 Security Group" --vpc-id $VPC_ID --query "GroupId" --output text
    # Add rules
    aws ec2 authorize-security-group-ingress --group-id $API_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $API_SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0
    Write-Host "Created API Security Group: $API_SG_ID" -ForegroundColor Green
} else {
    Write-Host "Found existing API Security Group: $API_SG_ID" -ForegroundColor Green
}

# DB SG
$DB_SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=tally-sync-db-sg" "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[0].GroupId" --output text
if ($DB_SG_ID -eq "None" -or -not $DB_SG_ID) {
    Write-Host "Creating tally-sync-db-sg..." -ForegroundColor Cyan
    $DB_SG_ID = aws ec2 create-security-group --group-name tally-sync-db-sg --description "RDS PostgreSQL Security Group" --vpc-id $VPC_ID --query "GroupId" --output text
    # Add rule
    aws ec2 authorize-security-group-ingress --group-id $DB_SG_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0
    Write-Host "Created DB Security Group: $DB_SG_ID" -ForegroundColor Green
} else {
    Write-Host "Found existing DB Security Group: $DB_SG_ID" -ForegroundColor Green
}

# 4. Key Pair
Write-Host "Setting up Key Pair..." -ForegroundColor Yellow
$KEY_NAME = "tally-sync-key"
$KEY_FILE = "tally-sync-key.pem"

$existingKey = aws ec2 describe-key-pairs --filters "Name=key-name,Values=$KEY_NAME" --query "KeyPairs[0].KeyName" --output text
if ($existingKey -eq "None" -or -not $existingKey) {
    Write-Host "Creating Key Pair: $KEY_NAME..." -ForegroundColor Cyan
    $keyMaterial = aws ec2 create-key-pair --key-name $KEY_NAME --query "KeyMaterial" --output text
    [System.IO.File]::WriteAllText((Resolve-Path $KEY_FILE), $keyMaterial, [System.Text.Encoding]::ASCII)
    Write-Host "Saved key material to: $KEY_FILE" -ForegroundColor Green
} else {
    Write-Host "Key pair '$KEY_NAME' already exists in AWS." -ForegroundColor Green
    if (-not (Test-Path $KEY_FILE)) {
        Write-Host "WARNING: Local key file '$KEY_FILE' is missing but key exists in AWS." -ForegroundColor Yellow
        Write-Host "If you do not have the private key, you might need to delete it from AWS (aws ec2 delete-key-pair --key-name $KEY_NAME) and rerun this script." -ForegroundColor Yellow
    }
}

if (Test-Path $KEY_FILE) {
    # Fix key file permissions for Windows SSH
    Write-Host "Fixing permissions on $KEY_FILE..." -ForegroundColor Cyan
    icacls $KEY_FILE /grant "$($env:USERNAME):F" /inheritance:r | Out-Null
}

# 5. Get Ubuntu AMI
Write-Host "Fetching latest Ubuntu 22.04 LTS AMI..." -ForegroundColor Yellow
$AMI_ID = aws ssm get-parameter --name "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id" --query "Parameter.Value" --output text
Write-Host "AMI ID: $AMI_ID" -ForegroundColor Green

# 6. Launch/Retrieve EC2 Instance
Write-Host "Setting up EC2 Instance..." -ForegroundColor Yellow
$instances = aws ec2 describe-instances --filters "Name=tag:Name,Values=tally-sync-api" "Name=instance-state-name,Values=running,pending" --query "Reservations[*].Instances[*].[InstanceId,PublicIpAddress]" --output json | ConvertFrom-Json

$INSTANCE_ID = $null
$INSTANCE_IP = $null

if ($instances -and $instances.Count -gt 0 -and $instances[0].Count -gt 0) {
    $INSTANCE_ID = $instances[0][0][0]
    $INSTANCE_IP = $instances[0][0][1]
    Write-Host "Found existing running EC2 Instance: $INSTANCE_ID (IP: $INSTANCE_IP)" -ForegroundColor Green
} else {
    Write-Host "Launching new EC2 Instance..." -ForegroundColor Cyan
    $launchResult = aws ec2 run-instances `
      --image-id $AMI_ID `
      --count 1 `
      --instance-type t2.micro `
      --key-name $KEY_NAME `
      --security-group-ids $API_SG_ID `
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=tally-sync-api}]" `
      --query "Instances[0].[InstanceId]" --output json | ConvertFrom-Json
    
    $INSTANCE_ID = $launchResult[0]
    Write-Host "Launched Instance ID: $INSTANCE_ID. Waiting for Public IP..." -ForegroundColor Cyan
    
    # Wait for Public IP to populate
    $timeout = 60
    while (-not $INSTANCE_IP -and $timeout -gt 0) {
        Start-Sleep -Seconds 5
        $timeout -= 5
        $INSTANCE_IP = aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --output text
    }
    Write-Host "EC2 Public IP: $INSTANCE_IP" -ForegroundColor Green
}

# 7. Create/Retrieve RDS PostgreSQL Instance
Write-Host "Setting up RDS Database (PostgreSQL)..." -ForegroundColor Yellow
$dbInstances = aws rds describe-db-instances --filters "Name=db-instance-id,Values=tally-sync-db" --query "DBInstances[*].[DBInstanceStatus,Endpoint.Address]" --output json 2>$null | ConvertFrom-Json

$DB_STATUS = $null
$DB_ENDPOINT = $null

if ($dbInstances -and $dbInstances.Count -gt 0) {
    $DB_STATUS = $dbInstances[0][0]
    $DB_ENDPOINT = $dbInstances[0][1]
    Write-Host "Found existing RDS DB instance. Status: $DB_STATUS" -ForegroundColor Green
} else {
    Write-Host "Creating RDS Database 'tally-sync-db' (db.t3.micro, PostgreSQL 15.18)..." -ForegroundColor Cyan
    $dbPass = "TallySync2026PostgresSecure"
    aws rds create-db-instance `
      --db-instance-identifier tally-sync-db `
      --db-instance-class db.t3.micro `
      --engine postgres `
      --engine-version 15.18 `
      --master-username postgres `
      --master-user-password $dbPass `
      --allocated-storage 20 `
      --vpc-security-group-ids $DB_SG_ID `
      --db-name tally_sync `
      --publicly-accessible `
      --backup-retention-period 0 | Out-Null
      
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create RDS DB instance." -ForegroundColor Red
        Exit 1
    }
    $DB_STATUS = "creating"
    Write-Host "RDS Database creation initiated. This will take 5-10 minutes..." -ForegroundColor Green
}

# 8. Monitor Database Availability
if ($DB_STATUS -ne "available") {
    Write-Host "Waiting for database to become available..." -ForegroundColor Yellow
    $dbTimeout = 600 # 10 mins max
    while ($DB_STATUS -ne "available" -and $dbTimeout -gt 0) {
        Write-Host "Database status: $DB_STATUS. Waiting 20 seconds..." -ForegroundColor Cyan
        Start-Sleep -Seconds 20
        $dbTimeout -= 20
        $statusResult = aws rds describe-db-instances --filters "Name=db-instance-id,Values=tally-sync-db" --query "DBInstances[0].[DBInstanceStatus,Endpoint.Address]" --output json 2>$null | ConvertFrom-Json
        if ($statusResult) {
            $DB_STATUS = $statusResult[0]
            $DB_ENDPOINT = $statusResult[1]
        }
    }
    
    if ($DB_STATUS -ne "available") {
        Write-Host "ERROR: Database did not reach 'available' status within timeout period." -ForegroundColor Red
        Exit 1
    }
    Write-Host "Database is now available!" -ForegroundColor Green
}
Write-Host "RDS Endpoint: $DB_ENDPOINT" -ForegroundColor Green

# 9. Output Configuration summary and update local files
Write-Host "===============================================" -ForegroundColor Green
Write-Host "        DEPLOYMENT INFRASTRUCTURE READY!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "1. EC2 FastAPI Host IP : $INSTANCE_IP" -ForegroundColor Green
Write-Host "2. RDS DB Host Endpoint: $DB_ENDPOINT" -ForegroundColor Green
Write-Host "3. Key File Saved As   : $KEY_FILE" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Prepare local env lines
$dbUrl = "postgresql://postgres:TallySync2026PostgresSecure@${DB_ENDPOINT}:5432/tally_sync"
$cloudApiUrl = "http://${INSTANCE_IP}:8000"

Write-Host "Updating your local .env.local..." -ForegroundColor Yellow
$envLocalPath = Join-Path (Get-Location) ".env.local"
if (Test-Path $envLocalPath) {
    # Backup existing
    Copy-Item $envLocalPath "$envLocalPath.bak" -Force
    Write-Host "Backup of .env.local created at .env.local.bak" -ForegroundColor Cyan
    
    # Read current content and replace CLOUD_API_URL if exists, else append
    $lines = Get-Content $envLocalPath
    $newLines = @()
    $hasUrl = $false
    foreach ($line in $lines) {
        if ($line.StartsWith("CLOUD_API_URL=")) {
            $newLines += "CLOUD_API_URL=$cloudApiUrl"
            $hasUrl = $true
        } else {
            $newLines += $line
        }
    }
    if (-not $hasUrl) {
        $newLines += "CLOUD_API_URL=$cloudApiUrl"
    }
    $newLines | Set-Content $envLocalPath
    Write-Host ".env.local updated with CLOUD_API_URL=$cloudApiUrl" -ForegroundColor Green
} else {
    # Create new
    $newContent = @"
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-guid
CLOUD_API_URL=$cloudApiUrl
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
"@
    $newContent | Set-Content $envLocalPath
    Write-Host ".env.local created and configured!" -ForegroundColor Green
}

Write-Host "`nTo SSH into your EC2 Instance, run:" -ForegroundColor Green
Write-Host "  ssh -i $KEY_FILE ubuntu@$INSTANCE_IP" -ForegroundColor Yellow

Write-Host "`nTo configure the database URL on your EC2 instance service configuration, use:" -ForegroundColor Green
Write-Host "  DATABASE_URL=$dbUrl" -ForegroundColor Yellow
