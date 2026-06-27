# 🚀 AWS Deployment Guide — EC2 + RDS PostgreSQL

**Duration**: 2-3 hours  
**Cost**: Free tier eligible (~12 months free)  
**Difficulty**: Medium  
**Benefit**: More generous free tier, data in ap-south-1 (India)

---

## Why AWS?

| Aspect | Railway | AWS Free Tier |
|--------|---------|---------------|
| **Compute** | Limited free | EC2 t2.micro (750h/mo) |
| **Database** | Limited free | RDS t2.micro (750h/mo) |
| **Egress** | 5 GB/month | 100 GB/month |
| **Duration** | Limited | 12 months |
| **Region** | US only | ap-south-1 (Mumbai) ✅ |
| **Cost After Free** | ~$5-10/mo | EC2 ~$10 + RDS ~$30/mo |

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Windows Agent (your machine)           │
│  • Extracts from Tally                  │
│  • Queues locally                       │
│  • POSTs to AWS API                     │
└────────────┬────────────────────────────┘
             │ HTTPS
    ┌────────▼────────────────────┐
    │  AWS EC2 (FastAPI)          │
    │  t2.micro instance          │
    │  ap-south-1 region          │
    └────────┬────────────────────┘
             │ TCP 5432
    ┌────────▼────────────────────┐
    │  AWS RDS PostgreSQL         │
    │  db.t2.micro instance       │
    │  ap-south-1 region          │
    │  Multi-AZ for reliability   │
    └─────────────────────────────┘
```

---

## Prerequisites

- AWS Account (free tier eligible)
- AWS CLI installed (optional, we'll use console)
- Your PostgreSQL credentials from Step 2 (saved from Railway)
- Procfile + runtime.txt (already in repo ✓)

---

## Step 1: Create AWS Account & Set Up Free Tier

### 1.1: Create Account

1. Go to https://aws.amazon.com
2. Click "Create AWS Account"
3. Follow signup process
   - Email address
   - Password
   - Account name
   - Billing information (card required but won't charge for free tier)
4. Verify email
5. Choose "Personal" account type
6. Complete phone verification

### 1.2: Enable Free Tier

1. Login to AWS Console
2. Go to **AWS Free Tier** (top right account menu → AWS Free Tier)
3. Verify you're eligible
4. Note the 12-month limit

### 1.3: Set Region to ap-south-1

1. Top right corner: Click region dropdown
2. Select **Asia Pacific (Mumbai)** — ap-south-1
3. All subsequent steps use this region

---

## Step 2: Create RDS PostgreSQL Database

### 2.1: Launch RDS

1. Go to **AWS Console** → Search "RDS"
2. Click **"RDS"** service
3. Click **"Create database"**

### 2.2: Database Configuration

**Engine Options**:
- Engine: PostgreSQL
- Version: PostgreSQL 15.4
- Templates: Free tier

**DB Instance Identifier**:
```
tally-sync-db
```

**Credentials**:
- Master username: `postgres`
- Master password: Generate strong password (25+ characters)
  - Save this! You'll need it.
  - Example: `TallySync@2026PostgreSQL#SecureP@ss`

**DB Instance Class**:
- db.t2.micro (free tier eligible)

**Storage**:
- Type: gp2
- Allocated: 20 GB (free tier max)
- Enable "Disable automated backups" (to save costs)

**Connectivity**:
- VPC: Default VPC
- Public accessibility: YES (so agent can connect)
- Security group: Create new
  - Name: `tally-sync-sg`
  - Inbound rule: PostgreSQL (5432) from 0.0.0.0/0

**Database**:
- Initial database name: `tally_sync`

**Additional options**:
- Enable backups: NO (for free tier)
- Enable encryption: NO (optional for testing)

### 2.3: Create Database

Click **"Create database"** and wait 5-10 minutes

### 2.4: Get Connection Details

1. After creation, click database instance
2. Go to **"Connectivity & Security"** tab
3. Save these values:
   - **Endpoint**: `tally-sync-db.c...region.rds.amazonaws.com`
   - **Port**: `5432`
   - **Master username**: `postgres`
   - **Master password**: (what you set above)
   - **Database name**: `tally_sync`

---

## Step 3: Create EC2 Instance (FastAPI Server)

### 3.1: Launch EC2

1. Go to **AWS Console** → Search "EC2"
2. Click **"EC2"** service
3. Click **"Launch instances"**

### 3.2: Configuration

**Name and tags**:
```
tally-sync-api
```

**AMI (Image)**:
- Ubuntu 22.04 LTS (free tier eligible)
- Architecture: 64-bit (x86)

**Instance Type**:
- t2.micro (free tier)

**Key pair**:
- Click "Create new key pair"
- Name: `tally-sync-key`
- Type: RSA
- Format: .pem
- Click "Create key pair"
- **Download and save the .pem file**
  - You'll use this to SSH into the instance

**Network Security**:
- VPC: Default
- Subnet: ap-south-1a
- Security group: Create new
  - Name: `tally-sync-api-sg`
  - Description: "Allow HTTP, HTTPS, SSH"
  - Inbound rules:
    - SSH (22) from 0.0.0.0/0
    - HTTP (80) from 0.0.0.0/0
    - HTTPS (443) from 0.0.0.0/0

**Storage**:
- 30 GB gp2 (free tier eligible)

### 3.3: Launch Instance

Click **"Launch instance"** and wait 2-3 minutes for startup

### 3.4: Get Instance Details

1. Go to **EC2 Dashboard** → **Instances**
2. Click your `tally-sync-api` instance
3. Copy:
   - **Public IPv4 address**: `1.2.3.4`
   - **Public IPv4 DNS**: `ec2-1-2-3-4.ap-south-1.compute.amazonaws.com`

---

## Step 4: Install FastAPI on EC2

### 4.1: SSH into Instance

```bash
# On your machine (Windows PowerShell or WSL)
# First, change permissions on the .pem file
chmod 400 tally-sync-key.pem

# SSH into EC2
ssh -i tally-sync-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
# Or use DNS:
ssh -i tally-sync-key.pem ubuntu@ec2-1-2-3-4.ap-south-1.compute.amazonaws.com
```

### 4.2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & pip
sudo apt install -y python3.12 python3.12-venv python3-pip git

# Install Uvicorn & dependencies
pip3 install uvicorn fastapi sqlalchemy psycopg2-binary pydantic python-dotenv

# Create app directory
mkdir -p /opt/tally-sync
cd /opt/tally-sync

# Clone repository
git clone https://github.com/YOUR-USERNAME/tally-sahayak.git .
```

### 4.3: Install Requirements

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install from pyproject.toml
pip install -e ".[platform]"
```

---

## Step 5: Configure FastAPI Service

### 5.1: Create Environment File

```bash
sudo nano /opt/tally-sync/.env
```

Add:
```
DATABASE_URL=postgresql://postgres:YOUR-RDS-PASSWORD@YOUR-RDS-ENDPOINT:5432/tally_sync
PYTHONUNBUFFERED=1
```

Replace:
- `YOUR-RDS-PASSWORD`: Master password from Step 2
- `YOUR-RDS-ENDPOINT`: RDS endpoint from Step 2.4

### 5.2: Test FastAPI

```bash
# Navigate to repo
cd /opt/tally-sync

# Activate venv
source venv/bin/activate

# Run FastAPI
uvicorn cloudplatform.main:app --host 0.0.0.0 --port 8000
```

Should see:
```
Uvicorn running on http://0.0.0.0:8000
```

Test in new SSH session:
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

### 5.3: Set Up Systemd Service

```bash
# Exit from running server (Ctrl+C)

# Create systemd service file
sudo nano /etc/systemd/system/tally-sync.service
```

Paste:
```ini
[Unit]
Description=Tally Sync FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/tally-sync
Environment="DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@YOUR-ENDPOINT:5432/tally_sync"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/tally-sync/venv/bin/uvicorn cloudplatform.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace credentials!

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tally-sync
sudo systemctl start tally-sync

# Check status
sudo systemctl status tally-sync

# View logs
sudo journalctl -u tally-sync -f
```

---

## Step 6: Set Up Public HTTPS (Optional but Recommended)

### 6.1: Create Elastic IP

1. EC2 Dashboard → **Elastic IPs**
2. Click **"Allocate Elastic IP address"**
3. Associate with your instance
4. Save the IP

### 6.2: Use Domain + SSL

**Option A: Use Elastic IP directly**
```
http://52.XX.XX.XX:8000
```

**Option B: Use custom domain + Route53**
1. Buy domain (or use existing)
2. Create Route53 hosted zone
3. Point A record to Elastic IP
4. Use AWS Certificate Manager for free SSL

For testing, Option A is fine.

---

## Step 7: Update Agent Configuration

### Back on Your Windows Machine

Edit `.env.local`:

```bash
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Your Company
TALLY_COMPANY_GUID=your-guid

# Update to AWS
CLOUD_API_URL=http://YOUR-EC2-PUBLIC-IP:8000
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
```

Or if using domain:
```
CLOUD_API_URL=https://your-domain.com
```

---

## Step 8: Test End-to-End

### 8.1: Health Check

```powershell
curl http://YOUR-EC2-PUBLIC-IP:8000/health
```

Expected:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

### 8.2: Extract & Verify

```powershell
python scripts/dev/run_extraction_json.py
```

### 8.3: Check Data Reached Cloud

```powershell
curl -X GET http://YOUR-EC2-PUBLIC-IP:8000/v1/stats `
  -H "x-api-key: test-api-key-12345"
```

Expected:
```json
{"total_vouchers": N, "total_ledgers": M}
```

---

## Cost Breakdown (Free Tier)

| Service | Free Tier | Cost |
|---------|-----------|------|
| **EC2 t2.micro** | 750h/month | $0 (12 mo) |
| **RDS db.t2.micro** | 750h/month | $0 (12 mo) |
| **Data transfer** | 100 GB/month | $0 (12 mo) |
| **Storage** | 30 GB + 20 GB | $0 (12 mo) |
| **TOTAL** | All included | **$0** |

After 12 months:
- EC2: ~$8-10/month
- RDS: ~$30/month
- Total: ~$40/month

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to RDS | Check security group allows 5432 from EC2 |
| FastAPI won't start | Check logs: `journalctl -u tally-sync -f` |
| 502 Bad Gateway | Check DATABASE_URL is correct |
| SSH connection refused | Check security group allows port 22 |
| High costs | Verify free tier is active, check billing dashboard |

---

## Cleanup (If Needed)

To avoid unexpected charges:

```bash
# Stop instances (don't delete — might need later)
EC2 → Instances → Stop

# Delete if not needed
EC2 → Instances → Terminate
RDS → Delete (uncheck "Create final snapshot")
```

---

## Summary

✅ **AWS is now running your FastAPI + PostgreSQL**
✅ **Same code, different provider**
✅ **Zero changes to agent code**
✅ **Only .env.local changed**

This demonstrates the cloud abstraction perfectly! 🎯

---

**Next**: Follow these steps and report back when:
1. ✓ RDS is created and accessible
2. ✓ EC2 is running
3. ✓ FastAPI deployed and healthy
4. ✓ Data flows to cloud
