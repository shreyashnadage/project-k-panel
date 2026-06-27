# ✅ Cloud Deployment Checklist

**Goal**: Deploy CloudAPI + PostgreSQL to Railway.app  
**Timeline**: 2-4 hours  
**Difficulty**: Easy  
**Status**: Ready to start

---

## 📋 Pre-Deployment Checklist

- [ ] **Repository Ready**
  - [ ] Code committed to main branch
  - [ ] GitHub repository created/updated
  - [ ] All changes pushed to origin

- [ ] **Code Quality**
  - [ ] `make lint` passes
  - [ ] `make test` passes (60+ tests)
  - [ ] No uncommitted changes

- [ ] **Documentation**
  - [ ] README.md up to date
  - [ ] Environment variables documented
  - [ ] Deployment guide ready (this file)

---

## 🚀 Deployment Steps

### STEP 1: Create Railway Account (5 min)

- [ ] Go to https://railway.app
- [ ] Sign up with GitHub
- [ ] Authorize Railway to access repos
- [ ] Dashboard ready

**Status**: ⏳ Waiting for you

---

### STEP 2: Deploy PostgreSQL (10 min)

- [ ] Create new PostgreSQL service
- [ ] Wait for initialization
- [ ] Note credentials:
  - [ ] PGHOST: _________________
  - [ ] PGPORT: 5432
  - [ ] PGUSER: postgres
  - [ ] PGPASSWORD: _________________
  - [ ] PGDATABASE: railway

**Status**: ⏳ Waiting for you

---

### STEP 3: Prepare Deployment Files (5 min)

In your repo root, create:

**File: `Procfile`**
```
web: uvicorn cloudplatform.main:app --host 0.0.0.0 --port $PORT
```

**File: `runtime.txt`**
```
python-3.12.3
```

Then:
```bash
git add Procfile runtime.txt
git commit -m "Add deployment configuration for Railway"
git push origin main
```

- [ ] Procfile created
- [ ] runtime.txt created
- [ ] Changes committed and pushed

**Status**: ⏳ Waiting for you

---

### STEP 4: Deploy FastAPI (30 min)

- [ ] Create new GitHub Repo service in Railway
- [ ] Select your repository
- [ ] Click Deploy
- [ ] Wait for build to complete (~2-3 min)
- [ ] Verify "Deployment Successful"

**Status**: ⏳ Waiting for you

---

### STEP 5: Configure Environment Variables (10 min)

In Railway dashboard → FastAPI service → Variables:

```
DATABASE_URL=postgresql://postgres:PASSWORD@PGHOST:5432/railway
PYTHONUNBUFFERED=1
```

- [ ] DATABASE_URL set correctly
- [ ] Environment verified

**Status**: ⏳ Waiting for you

---

### STEP 6: Get Public URL (5 min)

- [ ] Click FastAPI service → Domain tab
- [ ] Copy Railway.dev URL
- [ ] Note it:
  ```
  API URL: https://tally-sync-api-prod.up.railway.app
  ```

**Status**: ⏳ Waiting for you

---

### STEP 7: Test Deployment (10 min)

```bash
# Test health check
curl https://YOUR-URL/health

# Expected: {"status":"ok","service":"tally-sync-ingest"}
```

- [ ] Health check returns 200 OK
- [ ] Response shows correct service name

**Status**: ⏳ Waiting for you

---

### STEP 8: Update Local Configuration (5 min)

Edit `.env.local`:

```
TALLY_URL=http://localhost:9000
TALLY_COMPANY_NAME=Bhrama Enterprises
TALLY_COMPANY_GUID=your-guid
CLOUD_API_URL=https://YOUR-RAILWAY-URL
CLOUD_API_KEY=test-api-key-12345
CLOUD_TENANT_ID=test-tenant-001
```

- [ ] CLOUD_API_URL updated
- [ ] Other variables verified

**Status**: ⏳ Waiting for you

---

### STEP 9: Test End-to-End (10 min)

```bash
# Run extraction against live cloud API
python scripts/dev/run_extraction_json.py

# Verify data reached cloud
curl -X GET https://YOUR-URL/v1/stats \
  -H "x-api-key: test-api-key-12345"

# Expected: {"total_vouchers": N, "total_ledgers": M}
```

- [ ] Extraction runs without errors
- [ ] Data reaches cloud database
- [ ] Stats endpoint shows correct counts

**Status**: ⏳ Waiting for you

---

## 🎯 Success Criteria

✅ **Deployment Successful When**:

1. [ ] Railway dashboard shows "Deployed" status
2. [ ] Health check endpoint returns 200
3. [ ] PostgreSQL service is healthy
4. [ ] API endpoints respond correctly
5. [ ] Data flows from local agent → cloud DB
6. [ ] Stats endpoint shows synced data

---

## 📊 Post-Deployment

### Optional: Upgrade to Paid Plan

For production use:
- [ ] Go to Railway Account Settings → Billing
- [ ] Add payment method
- [ ] Upgrade to paid (~$5-10/month)
- [ ] Removes 24-hour idle sleep

### Create Production Tenant

```bash
python scripts/setup/create_test_tenant.py \
  --tenant-id tenant-pilot-001 \
  --tenant-name "Pilot Customer"
```

- [ ] Production tenant created
- [ ] API key securely stored

---

## 🔗 Resources

- **Railway Docs**: https://docs.railway.app
- **PostgreSQL Setup**: https://docs.railway.app/databases/postgresql
- **FastAPI Deployment**: https://docs.railway.app/getting-started
- **Troubleshooting**: See railway_deployment.md section

---

## ⏱️ Timeline

| Step | Time | Status |
|------|------|--------|
| Create account + deploy DB | 15 min | ⏳ |
| Prepare files + push | 10 min | ⏳ |
| Deploy FastAPI | 5 min build + 5 min setup | ⏳ |
| Test endpoints | 10 min | ⏳ |
| **TOTAL** | **~45 minutes** | ⏳ |

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Check Procfile, runtime.txt, git push completed |
| 502 error | Check logs, verify DATABASE_URL matches actual credentials |
| Connection refused | Verify PGHOST/PGPORT are correct, wait for DB to initialize |
| Timeout | Check PostgreSQL service is running, not sleeping |

**For help**: Check railway_deployment.md Troubleshooting section or Railway docs.

---

## ✅ Next Steps After Deployment

1. **Phase 4 VM Testing** (start after deployment validates)
   - Build Inno Setup installer
   - Test on Windows VMs
   - Validate service installation

2. **Code Signing** (optional but recommended)
   - Get EV certificate
   - Sign installer
   - Reduces SmartScreen warning

3. **Pilot Launch** (when both above complete)
   - Deploy to first customer
   - Monitor logs
   - Gather feedback

---

**You're ready to deploy! 🚀**

Follow the steps above and you'll have a live cloud backend in 2-4 hours.

Need help? See `docs/deployment/railway_deployment.md` for detailed instructions.
