# scripts/setup/deploy_ec2_app.ps1
# Script to automate deployment of FastAPI application on EC2 and link it to RDS
# Uses local zip & upload to handle private repository deployment without Git credentials

$ErrorActionPreference = "Stop"

$EC2_IP = "15.206.90.21"
$DB_ENDPOINT = "tally-sync-db.cfmeos4ww8s5.ap-south-1.rds.amazonaws.com"
$DB_URL = "postgresql://postgres:TallySync2026PostgresSecure@${DB_ENDPOINT}:5432/tally_sync"
$KEY_FILE = "tally-sync-key.pem"
$ZIP_FILE = "tally-sync-src.zip"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "     Tally Sync EC2 Application Deployer" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# 1. Verify SSH Key
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "ERROR: SSH Key file '$KEY_FILE' not found in current directory." -ForegroundColor Red
    Exit 1
}

# 2. Package local source code
Write-Host "Packaging local source code..." -ForegroundColor Yellow
python -c @"
import zipfile, os

exclude_dirs = {'.git', '.venv', '.pytest_cache', 'artifacts', 'build', '__pycache__', '.claude'}
exclude_files = {
    'tally-sync-key.pem', 
    'tally-sync-admin_accessKeys.csv', 
    'tally-sync-admin_credentials.csv', 
    '.env.local', 
    '.env.local.bak',
    'tally_sync_test.db',
    'tally-sync-src.zip'
}

with zipfile.ZipFile('$ZIP_FILE', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file in exclude_files:
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, '.')
            zipf.write(file_path, rel_path)
"@
Write-Host "Source package created: $ZIP_FILE" -ForegroundColor Green

# 3. Upload zip to EC2
Write-Host "Uploading source package to EC2..." -ForegroundColor Yellow
scp -i $KEY_FILE -o StrictHostKeyChecking=no $ZIP_FILE "ubuntu@${EC2_IP}:/tmp/${ZIP_FILE}"
Write-Host "Upload complete." -ForegroundColor Green

# 4. Clean up local zip
Remove-Item $ZIP_FILE -Force

# 5. Construct Remote Script to extract and install
$remoteScript = @"
set -e

echo '>>> Updating system packages...'
sudo apt-get update -y

echo '>>> Adding deadsnakes PPA for Python 3.12...'
sudo apt-get install -y software-properties-common unzip
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y

echo '>>> Installing Python 3.12, pip, venv and Git...'
sudo apt-get install -y python3.12 python3.12-venv python3-pip git curl

echo '>>> Preparing directory /opt/tally-sync...'
sudo mkdir -p /opt/tally-sync
sudo chown -R ubuntu:ubuntu /opt/tally-sync

echo '>>> Extracting source package...'
unzip -o /tmp/$ZIP_FILE -d /opt/tally-sync

cd /opt/tally-sync

echo '>>> Setting up Python virtual environment...'
python3.12 -m venv venv
source venv/bin/activate

echo '>>> Upgrading pip...'
pip install --upgrade pip

echo '>>> Installing package with platform dependencies...'
pip install -e '.[platform]'

echo '>>> Creating .env file...'
cat << 'EOF' > /opt/tally-sync/.env
DATABASE_URL=$DB_URL
PYTHONUNBUFFERED=1
EOF

echo '>>> Creating systemd service file...'
sudo tee /etc/systemd/system/tally-sync.service > /dev/null << 'EOF'
[Unit]
Description=Tally Sync FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/tally-sync
EnvironmentFile=/opt/tally-sync/.env
ExecStart=/opt/tally-sync/venv/bin/uvicorn cloudplatform.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo '>>> Enabling and starting systemd service...'
sudo systemctl daemon-reload
sudo systemctl enable tally-sync
sudo systemctl restart tally-sync

echo '>>> Checking service status...'
sudo systemctl status tally-sync --no-pager

echo '>>> Running health check locally...'
curl -s http://localhost:8000/health || echo 'Health check failed!'
"@

# 6. Execute Remote Script via SSH
Write-Host "Connecting to EC2 instance ($EC2_IP) and executing installation..." -ForegroundColor Yellow
$remoteScript | ssh -i $KEY_FILE -o StrictHostKeyChecking=no ubuntu@$EC2_IP "bash"

Write-Host "`n===============================================" -ForegroundColor Green
Write-Host "           DEPLOYMENT COMPLETED!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "FastAPI API endpoint: http://${EC2_IP}:8000" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
