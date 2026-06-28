# 📊 Agent Telemetry Service — Architecture Document

## Executive Summary

We're implementing a **event-driven telemetry service** that captures, buffers, and transmits agent lifecycle events to the cloud for real-time monitoring and analytics.

**Key Insight**: Events are the heartbeat of the system. By instrumenting every critical operation, we gain unprecedented visibility into agent health, performance, and user behavior.

---

## 1. Design Goals

| Goal | Rationale |
|------|-----------|
| **Non-blocking** | Telemetry must never block sync operations |
| **Resilient** | Works offline; queues events locally; retries failed sends |
| **Real-time** | Dashboard updates within seconds of events |
| **Structured** | Events are typed, validated, and queryable |
| **Extensible** | Easy to add new event types |
| **Low overhead** | Minimal memory/CPU footprint |
| **Production-ready** | Tested, logged, documented |

---

## 2. Event Model

### Event Structure

```typescript
interface TelemetryEvent {
  // Core fields
  event_id: string                 // UUID for deduplication
  event_type: string               // "agent.startup", "extraction.complete", etc.
  timestamp: string                // ISO 8601 UTC
  agent_id: string                 // Machine/agent identifier
  tenant_id: string                // Customer ID
  
  // Context
  source: string                   // "agent", "tally", "cloud", "service"
  severity: "info" | "warning" | "error" | "critical"
  
  // Event-specific data
  data: Record<string, any>        // Extensible payload
  
  // Metadata
  agent_version: string            // e.g., "0.4.0"
  python_version: string           // e.g., "3.12.3"
  platform: string                 // "windows"
  hostname: string                 // Machine name
  
  // Error context (if applicable)
  error?: {
    message: string
    code: string
    stack_trace: string | null
  }
}
```

### Event Type Categories

```
Agent Lifecycle:
  ✓ agent.startup              - Agent started
  ✓ agent.shutdown             - Agent stopped
  ✓ agent.health_check         - Periodic health report
  ✓ agent.error                - Unhandled exception

Tally Integration:
  ✓ tally.connection_check     - Tally API connectivity test
  ✓ tally.connection_success   - Connected to Tally
  ✓ tally.connection_failed    - Failed to connect
  ✓ tally.setup_started        - TallyAPIConnector initialization
  ✓ tally.setup_completed      - TallyAPIConnector ready

Extraction:
  ✓ extraction.started         - Extraction cycle began
  ✓ extraction.completed       - Extraction finished
  ✓ extraction.ledgers_found   - N ledgers extracted
  ✓ extraction.vouchers_found  - N vouchers extracted
  ✓ extraction.error           - Extraction failed

Queue:
  ✓ queue.records_enqueued     - Added to local queue
  ✓ queue.queue_size           - Current queue depth
  ✓ queue.error                - Queue operation failed

Transmission:
  ✓ transmission.started       - Sending to cloud
  ✓ transmission.completed     - Cloud transmission done
  ✓ transmission.success       - N records sent
  ✓ transmission.failed        - Transmission error
  ✓ transmission.retry         - Retrying failed send
  ✓ transmission.api_error     - Cloud API error

Sync Cycle:
  ✓ sync.cycle_started         - Full sync began
  ✓ sync.cycle_completed       - Full sync finished
  ✓ sync.cycle_duration        - Time taken (ms)
  ✓ sync.summary               - Extracted, transmitted, errors

Cloud API:
  ✓ cloud.health_check         - Backend connectivity test
  ✓ cloud.connected            - Backend is reachable
  ✓ cloud.disconnected         - Backend unreachable
  ✓ cloud.api_error            - Cloud returned error

Service:
  ✓ service.sync_scheduled     - Next sync time
  ✓ service.sync_started       - Service-initiated sync
  ✓ service.crash_recovery     - Recovered from crash
  ✓ service.shutdown           - Service stopped
```

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Components (emit events)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  main.py → Startup/Shutdown events                          │
│  ├─ tally_setup.py → Connection events                      │
│  ├─ orchestrator.py → Sync cycle events                     │
│  │   ├─ extractor/ → Extraction events                      │
│  │   ├─ queue/ → Queue events                               │
│  │   └─ transmitter/ → Transmission events                  │
│  └─ service/windows_service.py → Service events             │
│                                                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ emit(event)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  TelemetryService                                           │
├─────────────────────────────────────────────────────────────┤
│  Central event collector & emitter                          │
│                                                              │
│  • Validates events                                          │
│  • Buffers in-memory (ring buffer)                          │
│  • Persists to SQLite (local queue)                         │
│  • Batches for transmission                                 │
│  • Non-blocking (async/background)                          │
│                                                              │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Dual-path persistence
             ├─────────────────────────┬─────────────────────┐
             ▼                         ▼                     ▼
    ┌──────────────────┐    ┌──────────────────┐   ┌──────────────┐
    │  In-Memory       │    │  SQLite Queue    │   │  Log Files   │
    │  Ring Buffer     │    │  (offline cache) │   │  (disk logs) │
    │  (fast, recent)  │    │  (durable)       │   │  (audit)     │
    └────────┬─────────┘    └────────┬─────────┘   └──────────────┘
             │                       │
             └───────────┬───────────┘
                         │
                         │ Batch transmission
                         ▼
        ┌──────────────────────────────┐
        │  Cloud Telemetry API         │
        │  POST /v1/telemetry/events   │
        │                              │
        │  Async, retries, idempotent  │
        └──────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────┐
        │  Cloud Database              │
        │  telemetry_events table      │
        │  telemetry_metrics table     │
        └──────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────┐
        │  Dashboard & Monitoring      │
        │  • Real-time events          │
        │  • Health metrics            │
        │  • Performance trends        │
        │  • Alerts & anomalies        │
        └──────────────────────────────┘
```

---

## 4. Implementation Strategy

### Phase 1: Core Telemetry Service (This PR)
- ✅ Event model and types
- ✅ TelemetryService class
- ✅ In-memory ring buffer
- ✅ SQLite persistence
- ✅ Event emission from key modules
- ✅ Structured logging

### Phase 2: Cloud Transmission
- ✅ Batch transmission logic
- ✅ Cloud API integration
- ✅ Retry with exponential backoff
- ✅ Idempotent event ingestion

### Phase 3: Dashboard Integration
- ✅ New cloud API endpoints
- ✅ Dashboard widgets
- ✅ Real-time event stream
- ✅ Metrics aggregation

### Phase 4: Advanced Features (Future)
- Anomaly detection
- Alerting rules
- Custom dashboards
- Event filtering/sampling
- Data retention policies

---

## 5. Key Design Decisions

### Decision 1: Dual-path Persistence
**Choice**: In-memory ring buffer + SQLite queue

**Why**:
- **Ring buffer** → Fast, recent events (dashboard)
- **SQLite** → Durable, survives restarts
- **Non-blocking** → Telemetry never blocks sync

**Trade-off**:
- Slightly more memory (~10 MB for 10k events)
- Guaranteed durability + performance

---

### Decision 2: Async Transmission
**Choice**: Background thread for cloud transmission

**Why**:
- Sync operations never blocked by network
- Retries happen silently
- Failed sends don't crash agent

**Trade-off**:
- Slight delay in event delivery (acceptable)
- More complex (background management)

---

### Decision 3: Structured Events
**Choice**: Strongly-typed events with JSON payload

**Why**:
- Query-able and indexable in cloud DB
- Type-safe in Python
- Easy to extend (custom fields)

**Trade-off**:
- More boilerplate than unstructured logging
- Requires schema changes for new event types

---

### Decision 4: Local SQLite Queue
**Choice**: Persist events locally before transmission

**Why**:
- Agent works offline (events buffered)
- Survives agent crashes
- Retransmits on reconnection

**Trade-off**:
- Requires cleanup policy (bounded growth)
- Extra I/O overhead (minimal)

---

## 6. Data Flow

### Example: Extraction Event Flow

```
1. Extractor completes
   │
   ├─ telemetry.emit("extraction.completed", {
   │    ledgers_extracted: 150,
   │    vouchers_extracted: 500,
   │    duration_ms: 2340,
   │    status: "success"
   │  })
   │
2. TelemetryService.emit() called
   │
   ├─ Validate event
   │
   ├─ Add to in-memory ring buffer (recent events)
   │
   ├─ Persist to SQLite (durable queue)
   │
   ├─ Log event (audit trail)
   │
   ├─ Notify subscribers (if any)
   │
   └─ Background: Schedule transmission if batched events ready
       │
       └─ Async thread:
           ├─ Batch 100 events (or 5s timeout)
           ├─ POST to /v1/telemetry/events
           ├─ Retry up to 3 times with backoff
           └─ Mark as transmitted (delete from queue)
```

---

## 7. API Contract

### Client → Cloud

**Endpoint**: `POST /v1/telemetry/events`

**Request**:
```json
{
  "events": [
    {
      "event_id": "uuid-...",
      "event_type": "extraction.completed",
      "timestamp": "2026-06-28T12:34:56Z",
      "agent_id": "SHREYA-MACHINE-001",
      "tenant_id": "test-tenant-001",
      "severity": "info",
      "data": {
        "ledgers_extracted": 150,
        "vouchers_extracted": 500,
        "duration_ms": 2340
      },
      ...
    },
    ...
  ]
}
```

**Response**:
```json
{
  "success": true,
  "ingested": 98,
  "errors": [
    {
      "event_id": "uuid-...",
      "error": "duplicate event"
    }
  ]
}
```

---

## 8. Module Organization

```
agent/telemetry/
├── __init__.py                 (exports)
├── event_types.py              (event enums & schemas)
├── service.py                  (core TelemetryService class)
├── storage.py                  (SQLite persistence)
├── transmitter.py              (cloud transmission)
└── decorators.py               (event emission helpers)

agent/
├── extractor/
│   ├── client.py               (+ telemetry events)
│   └── parser.py               (+ telemetry events)
├── queue/
│   └── manager.py              (+ telemetry events)
├── transmitter/
│   └── client.py               (+ telemetry events)
├── tally_setup.py              (+ telemetry events)
├── orchestrator.py             (+ telemetry events)
├── main.py                     (+ telemetry initialization)
└── service/
    └── windows_service.py      (+ telemetry events)

cloudplatform/
├── api/
│   └── telemetry.py            (new endpoints)
└── db/
    └── models.py               (telemetry tables)
```

---

## 9. Configuration

```bash
# .env.local

# Telemetry settings
TELEMETRY_ENABLED=true
TELEMETRY_BUFFER_SIZE=10000          # Ring buffer max events
TELEMETRY_BATCH_SIZE=100              # Events to batch before sending
TELEMETRY_BATCH_TIMEOUT_SECONDS=5     # Or send after 5s
TELEMETRY_RETENTION_DAYS=7            # Keep local events for 7 days
TELEMETRY_CLOUD_URL=http://15.206.90.21:8000/v1/telemetry
```

---

## 10. Monitoring & Observability

### What to Monitor

```
Agent Health:
  • Startup success rate
  • Sync cycle success rate
  • Average sync duration
  • Tally connectivity %
  • Cloud connectivity %

Performance:
  • Records extracted per cycle
  • Records transmitted per cycle
  • Queue depth (backlog)
  • Latency (extraction, transmission)
  • Error rate by type

Business:
  • Total data synced
  • Uptime %
  • Customer activity
```

### Dashboard Widgets

```
Widget 1: Agent Status
  - Last heartbeat
  - Current queue depth
  - Next sync time
  
Widget 2: Sync Performance
  - Extraction rate (records/cycle)
  - Transmission success %
  - Average cycle duration

Widget 3: Connectivity
  - Tally API uptime %
  - Cloud API uptime %
  - Network errors (last 24h)

Widget 4: Error Trends
  - Error count by type
  - Error timeline
  - Top 5 error types

Widget 5: Data Flow
  - Records extracted (timeline)
  - Records transmitted (timeline)
  - Queue growth/decline
```

---

## 11. Error Handling & Recovery

### What if telemetry fails?

```
Scenario 1: Event emission fails
  → Logged as warning
  → Sync continues normally
  → No impact on data sync

Scenario 2: SQLite write fails
  → Fallback to in-memory only
  → Logged as error
  → Next successful write retries

Scenario 3: Cloud transmission fails
  → Event stays in SQLite queue
  → Auto-retries with exponential backoff
  → No data loss

Scenario 4: Agent crashes
  → Telemetry queue survives (SQLite)
  → Next startup retransmits pending events
  → Full recovery on restart
```

---

## 12. Security & Privacy

### Data Handling

```
Events contain:
  ✓ Technical data (counts, durations, errors)
  ✓ Agent metadata (version, platform)
  ✓ Status information
  
Events DO NOT contain:
  ✗ Sensitive business data
  ✗ Customer data (ledger amounts, names)
  ✗ Credentials or API keys
  ✗ Personally identifiable info
```

### Transmission Security

- HTTPS only (TLS 1.3)
- API key authentication
- Idempotent (deduplication on server)
- Signed timestamps (prevent tampering)

---

## 13. Testing Strategy

### Unit Tests
- Event creation & validation
- Ring buffer operations
- SQLite persistence
- Batch transmission logic

### Integration Tests
- End-to-end event flow
- Cloud transmission
- Retry behavior
- Offline scenarios

### Performance Tests
- Ring buffer throughput
- SQLite I/O overhead
- Memory footprint
- Transmission timing

---

## 14. Success Criteria

✅ **Comprehensive**: All critical operations emit events  
✅ **Non-blocking**: Telemetry never blocks sync  
✅ **Durable**: Events survive agent restarts  
✅ **Real-time**: Events reach cloud within ~5 seconds  
✅ **Queryable**: Events searchable in cloud DB  
✅ **Observable**: Dashboard shows live system state  

---

## 15. Future Enhancements

### Short term
- [ ] Anomaly detection (auto-alerts on errors)
- [ ] Custom dashboards (role-based views)
- [ ] Event filtering (sample high-volume events)

### Medium term
- [ ] Machine learning (predict issues)
- [ ] Automated remediation (auto-restart on failures)
- [ ] Multi-tenant aggregation (fleet-wide views)

### Long term
- [ ] Event streaming (Kafka integration)
- [ ] Real-time processing (stream processors)
- [ ] Advanced analytics (BI integration)

---

## Summary

This telemetry service transforms the agent from a "black box" into a **fully observable system**.

**Benefits**:
- 🔍 See exactly what the agent is doing
- 📊 Performance metrics and trends
- ⚠️ Early warning of issues
- 🔄 Faster debugging and support
- 📈 Usage analytics for product decisions

**Technical Excellence**:
- Non-blocking architecture
- Offline-first design
- Type-safe events
- Production-ready implementation

**Result**: A world-class observability platform! 🎯

---

**Document Version**: 1.0  
**Status**: Architecture approved, ready for implementation  
**Next**: Implement Phase 1 (Core Telemetry Service)
