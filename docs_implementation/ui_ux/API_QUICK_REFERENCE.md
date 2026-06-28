# Tally Sync Platform — API Quick Reference Card

> Quick-reference cheat sheet for frontend development.  
> For full details, see [FRONTEND_ARCHITECTURE_PROPOSAL.md](./FRONTEND_ARCHITECTURE_PROPOSAL.md)

---

## Base URL
```
Development: http://localhost:8000
Production:  http://<EC2_PUBLIC_IP>:8000
```

## Authentication Header Formats

| API Group | Header | Format |
|-----------|--------|--------|
| Auth routes (`/v1/auth/*`) | `Authorization` | `Bearer <jwt_access_token>` |
| Device routes (`/v1/devices/*`) | `Authorization` | `Bearer <jwt_access_token>` |
| Dashboard routes (`/api/dashboard/*`) | `x-api-key` | Raw API key string |
| Telemetry routes (`/v1/telemetry/*`) | `x-api-key` | Raw API key string |
| Ingest routes (`/v1/ledgers`, `/v1/vouchers`) | `x-api-key` | Raw API key string (agent only) |

> **⚠️ Note:** Dashboard APIs use `x-api-key` header (tenant API key), NOT JWT Bearer tokens. The frontend will need to handle both auth mechanisms depending on the endpoint being called.

---

## Endpoints at a Glance

### 🔐 Auth (No auth required for login/register)
```
POST /v1/auth/register        → Register new client
POST /v1/auth/verify-email    → Verify email token
POST /v1/auth/login           → Login → {access_token, refresh_token}
POST /v1/auth/logout          → [Bearer] Logout
POST /v1/auth/refresh         → Refresh access token
GET  /v1/auth/me              → [Bearer] Current user info
```

### 🖥️ Devices (Bearer JWT required)
```
POST /v1/devices/register            → [Bearer] Register device
GET  /v1/devices/list                → [Bearer] List all devices
POST /v1/devices/rotate-key?device_id=xxx  → [Bearer] Rotate API key
GET  /v1/devices/status/{device_id}  → [Bearer] Device status
```

### 📊 Dashboard (x-api-key required)
```
GET /api/dashboard/kpis           → KPI metrics
GET /api/dashboard/vouchers       → Paginated vouchers (?skip=0&limit=50)
GET /api/dashboard/cash-flow      → Cash flow trend (?period=monthly&months=6)
GET /api/dashboard/tenant-config  → Tenant branding
GET /api/dashboard/health         → Health check (no auth)
```

### 📡 Telemetry
```
POST /v1/telemetry/events   → [x-api-key] Ingest events
GET  /v1/telemetry/events   → Query events (?event_type=&severity=&limit=100)
GET  /v1/telemetry/stats    → Statistics (?agent_id=)
```

### 📋 Registration (Legacy Portal)
```
POST /v1/register                   → Register client → returns installation_key
POST /v1/register-device            → Register device (agent during install)
GET  /v1/clients/{client_id}/stats  → [x-api-key] Client statistics
POST /v1/sync-with-client           → [x-api-key] Receive sync data
```

### 🏥 Health
```
GET /        → Root status
GET /health  → Health check
```

---

## Response Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | Success | Standard response |
| `400` | Bad Request | Validation error, duplicate email |
| `401` | Unauthorized | Invalid/expired token or API key |
| `403` | Forbidden | Tenant mismatch, device not owned |
| `404` | Not Found | Client/device/key not found |
| `500` | Server Error | Unhandled exception |

---

## CORS Configuration Required

Add to `cloudplatform/main.py` if not already present:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.tallysync.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Missing Endpoints (Need Backend Work)

| Endpoint | For Page | Pattern to Follow |
|----------|----------|-------------------|
| `GET /api/dashboard/ledgers?skip=0&limit=100` | Ledgers page | Copy `/api/dashboard/vouchers` |
| `GET /v1/sync-records?client_id=xxx&skip=0&limit=50` | Sync History | New endpoint |
| `PUT /v1/auth/profile` | Settings page | New endpoint |
| `POST /v1/auth/forgot-password` | Login page | New endpoint |
