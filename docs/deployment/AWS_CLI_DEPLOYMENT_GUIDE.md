# 🚀 AWS CLI Deployment & User Guide

This guide describes how to deploy, configure, and operate the Tally Sync FastAPI service and RDS PostgreSQL database on AWS using the AWS CLI.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────┐
│  Windows Agent (Local Machine)          │
│  • Extracts voucher/ledger data         │
│  • Queues data locally in SQLite        │
│  • Transmits data to AWS API            │
└────────────┬────────────────────────────┘
             │ HTTPS (Port 8000)
    ┌────────▼────────────────────┐
    │  AWS EC2 (FastAPI Server)   │
    │  • Instance: t2.micro       │
    │  • OS: Ubuntu 22.04 LTS     │
    │  • App running on Systemd   │
    └────────┬────────────────────┘
             │ TCP (Port 5432)
    ┌────────▼────────────────────┐
    │  AWS RDS PostgreSQL DB      │
    │  • Instance: db.t3.micro    │
    │  • Engine: PostgreSQL 15.18 │
    └─────────────────────────────┘
```

---

## 2. Infrastructure Setup (How AWS is Deployed)

The entire AWS infrastructure has been automated via two PowerShell scripts using the AWS CLI.

### 2.1 Security Groups
Two security groups are created in your default VPC:
* **`tally-sync-api-sg`** (for the EC2 FastAPI Server):
  * Inbound rule: Port `22` (SSH) allowed from `0.0.0.0/0`.
  * Inbound rule: Port `8000` (FastAPI) allowed from `0.0.0.0/0`.
* **`tally-sync-db-sg`** (for the RDS Database):
  * Inbound rule: Port `5432` (PostgreSQL) allowed from `0.0.0.0/0` (to allow local agent and test script connectivity).

### 2.2 Key Pair
An SSH key pair named `tally-sync-key` is generated in AWS, saved locally as [tally-sync-key.pem](file:///d:/tally-shayak/tally-sync-key.pem), and configured with correct Windows file permissions to make it usable for OpenSSH.

### 2.3 EC2 Instance
* A `t2.micro` EC2 instance is launched using the latest Ubuntu 22.04 LTS AMI.
* The script automatically retrieves the public IP address once it is provisioned.

### 2.4 RDS Database Instance
* A `db.t3.micro` instance is provisioned with the PostgreSQL 15.18 engine.
* Storage is set to `20 GB gp2`.
* Backup retention is set to `0` (disabled for cost-saving on development/testing instances).
* The instance is made publicly accessible.

---

## 3. Deployment Scripts (How to Deploy)

If you need to redeploy the infrastructure or app on a new AWS account/region, use the following steps.

### Step 3.1: Configure AWS CLI Credentials
Before running the scripts, make sure the CLI is authenticated:
```powershell
aws configure
```
Provide your **Access Key ID**, **Secret Access Key**, default region (`ap-south-1`), and output format (`json`).

### Step 3.2: Provision Infrastructure
Run the provisioning script from the workspace root:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/deploy_aws.ps1
```
This script will create the security groups, key-pair, EC2 instance, and RDS database, wait for the database to become `available`, and output their endpoints. It also updates the `CLOUD_API_URL` inside your local [\.env.local](file:///d:/tally-shayak/.env.local) automatically.

### Step 3.3: Deploy Application Code to EC2
Run the application deployer:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/deploy_ec2_app.ps1
```
This script will:
1. Package the local code into a temporary ZIP file.
2. Upload the ZIP file to EC2 using `scp`.
3. Add the `deadsnakes` PPA on EC2 to install Python 3.12.
4. Extract the code into `/opt/tally-sync`.
5. Create a virtual environment and install dependencies.
6. Generate a `/opt/tally-sync/.env` file containing the RDS connection string.
7. Install and enable the `tally-sync` systemd service.

---

## 4. User Guide (Steps to Run & Test)

Once the setup is complete, follow these steps to verify and run the synchronization.

### Step 4.1: Create a Test Tenant
In order for the API to accept voucher payloads, a tenant must exist in the database. Run the following script locally to seed the test tenant into the remote RDS database:
```powershell
$env:DATABASE_URL="postgresql://postgres:TallySync2026PostgresSecure@tally-sync-db.cfmeos4ww8s5.ap-south-1.rds.amazonaws.com:5432/tally_sync"
$env:PYTHONPATH="."
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python scripts/setup/create_test_tenant.py
```
This registers the tenant `test-tenant-001` with API key `test-api-key-12345`.

### Step 4.2: Verify Health Check
Ensure that the API is reachable externally by running:
```powershell
curl.exe -s http://15.206.90.21:8000/health
```
**Expected Response**:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

### Step 4.3: Run Sync Extraction
To manually trigger the extraction client and save Tally data locally:
```powershell
.venv\Scripts\python scripts/dev/run_extraction_json.py
```
This will fetch all ledgers and save them to `extraction_output.json`.

### Step 4.4: Run the Orchestrator (Full Sync Cycle)
To run a complete sync cycle (extraction from Tally → queue locally → transmit to AWS RDS):
```powershell
$env:PYTHONPATH="."
.venv\Scripts\python -m agent.orchestrator
```
*Note: Make sure Tally is open and the company named in `.env.local` is loaded.*

---

## 5. Operations & Maintenance

### SSH access to the EC2 Server
To connect to your FastAPI server, open PowerShell and run:
```powershell
ssh -i tally-sync-key.pem ubuntu@15.206.90.21
```

### Managing the FastAPI Service on EC2
Once SSH'd into the instance, use the following systemd commands:
* **Check Status**: `sudo systemctl status tally-sync`
* **Restart**: `sudo systemctl restart tally-sync`
* **Stop**: `sudo systemctl stop tally-sync`
* **Start**: `sudo systemctl start tally-sync`
* **View Logs in Real-time**: `sudo journalctl -u tally-sync -f`

---

## 6. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"Permission denied (publickey)" on SSH** | Key file permissions are too open or key is in wrong format | The script sets permissions automatically. If it still fails, run `icacls tally-sync-key.pem /grant "$($env:USERNAME):F" /inheritance:r` or recreate the key. |
| **FastAPI won't start on EC2** | Database connection issues | Run `sudo journalctl -u tally-sync -n 50` to inspect stack traces. Verify that RDS endpoint in `/opt/tally-sync/.env` matches the active RDS instance. |
| **Connection Timeout to Port 8000** | Security Group issue | Run `aws ec2 describe-security-groups --group-ids sg-0d4c19b7390f8f06e` and confirm that port 8000 allows ingress from your IP. |
