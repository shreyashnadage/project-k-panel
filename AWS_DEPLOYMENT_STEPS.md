# AWS Deployment — Complete Step-by-Step Guide

## PHASE 4: Deploy FastAPI on EC2 (30 min)

### STEP 4.1: SSH into EC2

**On your Windows machine (PowerShell):**

1. Open PowerShell (Windows Terminal)
2. Navigate to where you saved `tally-sync-key.pem`:
   ```powershell
   cd Downloads
   ```
3. Fix permissions:
   ```powershell
   icacls tally-sync-key.pem /grant "%USERNAME%:F" /inheritance:r
   ```
4. SSH into EC2 (use YOUR Public IPv4 address from Step 3.3):
   ```powershell
   ssh -i tally-sync-key.pem ubuntu@13.235.XXX.XXX
   ```
5. Type `yes` when prompted

✓ **WHEN DONE**: You're inside EC2 (prompt shows `ubuntu@ip-...`)

---

### STEP 4.2: Install Dependencies

Run these commands one at a time:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & tools
sudo apt install -y python3.12 python3.12-venv python3-pip git curl

# Create app directory
mkdir -p /opt/tally-sync
cd /opt/tally-sync

# Clone repository
sudo git clone https://github.com/shreyashnadage/tally-sahayak.git .
sudo chown -R ubuntu:ubuntu /opt/tally-sync
```

⏱️ **Takes**: ~5 minutes

✓ **WHEN DONE**: You're in `/opt/tally-sync` directory

---

### STEP 4.3: Install Python Requirements

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -e ".[platform]"
```

⏱️ **Takes**: ~3 minutes

✓ **WHEN DONE**: Prompt shows `(venv)` prefix

---

### STEP 4.4: Configure Environment

```bash
# Create .env file
nano /opt/tally-sync/.env
```

**Paste this** (replace YOUR RDS endpoint and password from Step 2.3):

```
DATABASE_URL=postgresql://postgres:TallySync@Secure2026#P@tally-sync-db.c9akciq32.ap-south-1.rds.amazonaws.com:5432/tally_sync
PYTHONUNBUFFERED=1
```

Replace:
- `TallySync@Secure2026#P` → Your actual RDS password
- `tally-sync-db.c9akciq32.ap-south-1.rds.amazonaws.com` → Your actual RDS endpoint

**Save**: Ctrl+O, Enter, Ctrl+X

✓ **WHEN DONE**: File saved

---

### STEP 4.5: Test FastAPI Locally

```bash
# Make sure venv is activated (should show `(venv)` in prompt)
source venv/bin/activate

# Start FastAPI
uvicorn cloudplatform.main:app --host 0.0.0.0 --port 8000
```

✓ **WHEN DONE**: You see `Uvicorn running on http://0.0.0.0:8000`

⏱️ **Takes**: ~20 seconds

---

### STEP 4.6: Test Health Check (NEW SSH Window)

**Open a NEW PowerShell window:**

```powershell
ssh -i tally-sync-key.pem ubuntu@13.235.XXX.XXX
```

**Test the API:**

```bash
curl http://localhost:8000/health
```

✓ **EXPECTED RESPONSE**:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

If you see that → FastAPI is working! ✅

---

### STEP 4.7: Make FastAPI Auto-Start

**Back to your first SSH window**, stop FastAPI (Ctrl+C)

**Create systemd service:**

```bash
sudo nano /etc/systemd/system/tally-sync.service
```

**Paste this exactly** (replace YOUR RDS credentials):

```ini
[Unit]
Description=Tally Sync FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/tally-sync
Environment="DATABASE_URL=postgresql://postgres:TallySync@Secure2026#P@tally-sync-db.c9akciq32.ap-south-1.rds.amazonaws.com:5432/tally_sync"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/tally-sync/venv/bin/uvicorn cloudplatform.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save**: Ctrl+O, Enter, Ctrl+X

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable tally-sync
sudo systemctl start tally-sync

# Check status
sudo systemctl status tally-sync
```

✓ **WHEN DONE**: Status shows `active (running)` in green

---

## PHASE 5: Update Agent Configuration & Test (10 min)

### STEP 5.1: Update .env.local on Your Windows Machine

**On your Windows machine** (NOT on EC2):

Edit `D:\tally-shayak\.env.local`:

```
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-guid

# Update these to AWS
CLOUD_API_URL=http://13.235.XXX.XXX:8000
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
```

Replace `13.235.XXX.XXX` with your EC2 Public IPv4 address from Step 3.3

✓ **WHEN DONE**: .env.local updated

---

### STEP 5.2: Test Health Check from Your Machine

**Open PowerShell on your machine:**

```powershell
curl http://13.235.XXX.XXX:8000/health
```

✓ **EXPECTED**:
```json
{"status":"ok","service":"tally-sync-ingest"}
```

---

### STEP 5.3: Test End-to-End Data Flow

**Run extraction on your machine:**

```powershell
python scripts/dev/run_extraction_json.py
```

✓ **WATCH FOR**:
- "Extracted N vouchers"
- "Extracted N ledgers"  
- "Transmitted X records"

---

### STEP 5.4: Verify Data Reached Cloud

**Check stats endpoint:**

```powershell
curl -X GET http://13.235.XXX.XXX:8000/v1/stats -H "x-api-key: test-api-key-12345"
```

✓ **EXPECTED**:
```json
{"total_vouchers": N, "total_ledgers": M}
```

If you see the counts → **DATA FLOWED END-TO-END!** 🎉

---

## SUCCESS CHECKLIST

✅ **When ALL of these pass:**

- [ ] AWS account created
- [ ] RDS PostgreSQL deployed (status: Available)
- [ ] EC2 instance running (status: running)
- [ ] SSH connection successful
- [ ] FastAPI starts without errors
- [ ] Health check returns 200 OK
- [ ] DATABASE_URL configured correctly
- [ ] Systemd service active and running
- [ ] Agent .env.local updated with AWS URL
- [ ] Extraction script completes
- [ ] Data appears in /v1/stats endpoint

---

## CLOUD ABSTRACTION PROVEN ✅

**What changed:**
- DATABASE_URL (RDS endpoint, not Railway)
- CLOUD_API_URL (EC2 IP, not Railway domain)

**What stayed the same:**
- agent/ code (ZERO changes)
- cloudplatform/ code (ZERO changes)
- API interface (identical)
- Data flow (extraction → queue → transmission)

**This proves your architecture is cloud-provider agnostic!**

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't SSH | Check security group allows port 22, verify .pem file permissions |
| FastAPI won't start | Check logs: `journalctl -u tally-sync -f`, verify DATABASE_URL is correct |
| 502 Bad Gateway | Check RDS is accessible, verify security groups allow traffic |
| Health check fails | Ensure RDS is Available, check EC2 logs |
| No data in stats | Check extraction script output, verify API key is correct |

---

**You're ready to deploy! Follow Phase 1-5 and report back when complete.** 🚀
