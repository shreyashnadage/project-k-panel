# 🚀 Cloud Deployment Guide — Railway.app (FastAPI + PostgreSQL)

**Duration**: 2-4 hours  
**Cost**: ~$5-10/month (free tier available)  
**Difficulty**: Easy  
**Alternative**: AWS (see bottom)

---

## Why Railway.app?

| Aspect | Railway | AWS | Heroku |
|--------|---------|-----|--------|
| **Setup Time** | 30 min | 4-8 hours | 1 hour |
| **Cost** | $5-10/mo | $20-40/mo | $7-50/mo |
| **Ease** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Production Ready** | ✅ Yes | ✅ Yes | ⚠️ Declining |
| **Data Residency (India)** | ⚠️ US Only | ✅ ap-south-1 | ✗ No |

**Choice**: Railway for speed (MVP), migrate to AWS after pilot for data residency.

---

## Step 1: Create Railway Account (5 minutes)

```bash
1. Go to https://railway.app
2. Click "Start Project"
3. Sign up with GitHub (easiest)
4. Authorize railway-app to access GitHub
5. Dashboard loads → Ready!
```

---

## Step 2: Deploy PostgreSQL (10 minutes)

### 2.1: Create PostgreSQL Service

```bash
1. In Railway dashboard: Click "+ New"
2. Search "PostgreSQL"
3. Click "PostgreSQL"
4. Click "Deploy"
5. Wait for database to initialize (~2 min)
```

### 2.2: Note Database Credentials

```bash
Click on PostgreSQL service → Variables tab
Copy these values:

PGHOST=...         (hostname)
PGPORT=5432        (port)
PGUSER=postgres    (username)
PGPASSWORD=...     (password)
PGDATABASE=railway (database name)
```

---

## Step 3: Deploy FastAPI Backend (30 minutes)

### 3.1: Prepare Repository

```bash
# Make sure you're in repo root
cd D:\tally-shayak

# Add Procfile (tells Railway how to start app)
cat > Procfile << 'EOF'
web: uvicorn cloudplatform.main:app --host 0.0.0.0 --port $PORT
EOF

# Add runtime.txt (specify Python version)
cat > runtime.txt << 'EOF'
python-3.12.3
EOF

# Commit changes
git add Procfile runtime.txt
git commit -m "Add deployment configuration for Railway"
```

### 3.2: Create GitHub Repository (if not already)

```bash
# Initialize git (if needed)
git init

# Add remote
git remote add origin https://github.com/YOUR-USERNAME/tally-sync-agent.git

# Push code
git branch -M main
git push -u origin main
```

### 3.3: Deploy from GitHub

```bash
1. In Railway dashboard: Click "+ New"
2. Click "GitHub Repo"
3. Select your repository
4. Click "Deploy"
5. Wait for build (~2-3 min)
```

---

## Step 4: Configure Environment Variables (15 minutes)

### 4.1: Set Database Connection

Railway should auto-detect PostgreSQL. Verify:

```bash
1. Click on FastAPI service
2. Go to Variables tab
3. Should see: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
4. Click "Raw Editor"
5. Paste DATABASE_URL:

DATABASE_URL=postgresql://postgres:PASSWORD@PGHOST:5432/railway
```

(Replace PASSWORD and PGHOST with actual values)

### 4.2: Verify Other Variables

```bash
Variables → Raw Editor

# Should contain:
DATABASE_URL=postgresql://postgres:...@...
PYTHONUNBUFFERED=1
```

---

## Step 5: Test Deployment (10 minutes)

### 5.1: Get Public URL

```bash
1. Click FastAPI service
2. Go to "Domain" tab
3. Copy the Railway.dev URL
   Example: https://tally-sync-api-prod.up.railway.app

4. Test health check:
   curl https://tally-sync-api-prod.up.railway.app/health
   
   Expected: {"status":"ok","service":"tally-sync-ingest"}
```

### 5.2: Test Endpoints

```bash
# Create test tenant (on your dev machine)
python scripts/setup/create_test_tenant.py

# Test with public API
curl -X POST https://tally-sync-api-prod.up.railway.app/v1/ledgers \
  -H "x-api-key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "ledgers": [{
      "company_guid": "COMP-001",
      "company_name": "Test",
      "ledger_guid": "LED-001",
      "name": "Cash"
    }]
  }'

Expected: {"accepted":1,"duplicates":0,"errors":0,...}
```

---

## Step 6: Update Local Configuration (5 minutes)

### 6.1: Update .env.local

```bash
# Edit .env.local
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-guid

# Update cloud API URL to public endpoint
CLOUD_API_URL=https://tally-sync-api-prod.up.railway.app
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
```

### 6.2: Test Agent → Cloud Flow

```bash
# Run extraction
python scripts/dev/run_extraction_json.py

# Verify data reaches cloud DB
curl -X GET https://tally-sync-api-prod.up.railway.app/v1/stats \
  -H "x-api-key: test-api-key-12345"

Expected: {"tenant_id":"test-tenant-001","total_vouchers":N,"total_ledgers":M}
```

---

## Step 7: Production Setup (20 minutes)

### 7.1: Upgrade to Paid Plan

Railway free tier has limits:
- 5GB bandwidth/month
- CPU/RAM limits
- 24-hour project sleep after inactivity

For production:
```bash
1. Go to Account Settings → Billing
2. Add payment method
3. Upgrade to paid plan (~$5-10/month)
4. Project gets dedicated resources + no sleep
```

### 7.2: Create Production Tenant

```bash
# On dev machine
python -c "
import hashlib
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cloudplatform.db.models import Base, Tenant

# Connect to Railway PostgreSQL
DATABASE_URL = 'postgresql://postgres:PASSWORD@HOST:5432/railway'
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create production tenant
api_key = 'prod-api-key-XXXXXXXXXXXX'  # Generate random
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

tenant = Tenant(
    id='tenant-pilot-001',
    name='First Pilot Customer',
    api_key_hash=api_key_hash,
    is_active=True,
)
session.add(tenant)
session.commit()

print(f'Tenant ID: tenant-pilot-001')
print(f'API Key: {api_key}')
"
```

### 7.3: Configure for Pilot

```bash
# Update .env.local for pilot customer
CLOUD_API_URL=https://tally-sync-api-prod.up.railway.app
CLOUD_API_KEY=prod-api-key-XXXXXXXXXXXX
CLOUD_TENANT_ID=tenant-pilot-001
```

---

## Monitoring & Logs

### View Logs

```bash
Railway Dashboard:
1. Click FastAPI service
2. Click "Logs" tab
3. See real-time logs
4. Filter by error/warning
```

### Monitor Health

```bash
# Check API health
curl https://tally-sync-api-prod.up.railway.app/health

# Check database connection
curl -X GET https://tally-sync-api-prod.up.railway.app/v1/stats \
  -H "x-api-key: your-api-key"
```

### Database Backup

```bash
Railway → PostgreSQL service → Backups
Auto-backup enabled (every 24 hours)
Manual backup available anytime
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check Procfile, runtime.txt, requirements.txt |
| 502 Bad Gateway | Check logs, verify DATABASE_URL is correct |
| Database connection error | Verify PGHOST/PGPASSWORD in environment |
| API returns 404 | Endpoint path may be wrong, check /health first |
| Slow response | Check Railway CPU/memory metrics, upgrade if needed |

---

## Cost Breakdown

| Item | Free Tier | Paid Tier |
|------|-----------|-----------|
| **FastAPI** | $0 (limited) | $5-10/mo |
| **PostgreSQL** | $0 (limited) | Included |
| **Bandwidth** | 5 GB/mo | Unlimited |
| **Sleep** | Yes (after 24h) | No |
| **Support** | Community | Community |

**Recommendation**: Start free tier, upgrade to paid after pilot validation.

---

## Next: AWS Migration (After Pilot)

If you need:
- Data residency in India (ap-south-1)
- Higher scale (100+ customers)
- Custom networking/security

Then migrate to AWS:
- EC2 t3.small (FastAPI)
- RDS PostgreSQL t3.micro
- S3 for OTA updates
- See AWS_DEPLOYMENT.md

---

## Checklist

- [ ] Create Railway account
- [ ] Deploy PostgreSQL
- [ ] Deploy FastAPI from GitHub
- [ ] Configure environment variables
- [ ] Test health check endpoint
- [ ] Test API endpoints
- [ ] Create test tenant
- [ ] Test agent → cloud flow
- [ ] Upgrade to paid plan (optional)
- [ ] Create production tenant
- [ ] Configure .env.local
- [ ] Document API keys securely

---

**Estimated Total Time**: 2-4 hours  
**Next Step**: Phase 4 VM Testing (after deployment validates)

🎉 **Your cloud backend is live!**
