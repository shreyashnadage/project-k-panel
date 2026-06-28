# 🎯 Telemetry Architecture — Final Recommendation

## The Question

**How should we implement telemetry for the Windows Agent?**

Options explored:
1. OpenTelemetry (full-stack, enterprise-grade)
2. Structlog (lightweight logging)
3. Prometheus (metrics only)
4. Custom Event Bus (built from scratch)
5. Hybrid approach (combines best of multiple)

---

## The Recommendation: 🏆 **Structlog + Custom Event Bus (Hybrid)**

### Why This Approach?

| Criterion | Score | Notes |
|-----------|-------|-------|
| **Time to MVP** | ⭐⭐⭐⭐⭐ | Can implement in 2-3 days |
| **Production Ready** | ⭐⭐⭐⭐☆ | Durable, tested, battle-ready |
| **Future-Proof** | ⭐⭐⭐⭐⭐ | Easy to migrate to OTEL later |
| **Learning Curve** | ⭐⭐⭐⭐⭐ | Pure Python, no new concepts |
| **Operational Overhead** | ⭐⭐⭐⭐⭐ | Zero external dependencies Phase 1 |
| **Code Quality** | ⭐⭐⭐⭐☆ | Clean, maintainable, testable |
| **Team Velocity** | ⭐⭐⭐⭐⭐ | Solo developer can own entire system |

### What This Looks Like

```
Agent Modules (emit events)
        ↓
    Structlog (JSON formatted logs)
        ↓
    Custom EventBus (pub-sub + persistence)
        ↓
    SQLite Queue (durable local storage)
        ↓
    Cloud API (batch transmission)
        ↓
    Dashboard (real-time visualization)
```

---

## Why NOT Other Approaches?

### ❌ Pure OpenTelemetry
- ✓ Industry standard
- ✓ Excellent long-term
- ✗ **Overkill for MVP** (too much boilerplate)
- ✗ **Steep learning curve** (complex API)
- ✗ **Slows velocity** (5x more code)
- ✓ BUT: Easy to add later (Phase 2/3)

### ❌ Structlog Only
- ✓ Simple and fast
- ✓ Good for logging
- ✗ **No structured metrics** (counts, durations)
- ✗ **No durability** (events lost if agent crashes)
- ✗ **No pub-sub** (can't decouple event emission from transmission)

### ❌ Prometheus Only
- ✓ Great for metrics
- ✓ Standard format
- ✗ **Not for events** (designed for time-series metrics)
- ✗ **No log/trace support**
- ✗ **Requires Prometheus server** (external dependency)

### ❌ Custom from Scratch
- ✓ Full control
- ✗ **Reinventing the wheel**
- ✗ **No battle-tested patterns**
- ✗ **More bugs, slower delivery**

---

## The Hybrid Sweet Spot

### Phase 1: Structlog + Custom Bus (Weeks 1-2)
**Goal**: Get full telemetry working, cloud integration live

```python
# Simple, Pythonic event emission
import structlog
logger = structlog.get_logger()
logger.info("extraction_complete", ledgers=150, vouchers=500, duration_ms=2340)

# Custom EventBus adds durability + pub-sub
bus = EventBus()
bus.emit("extraction.complete", ledgers=150)
# Automatically: persists to SQLite, queues for cloud transmission
```

**Stack**:
- ✅ Structlog (10 lines of setup)
- ✅ Custom EventBus class (100 lines)
- ✅ SQLite storage (standard library)
- ✅ Cloud API transmission (already exists)
- ✅ No external dependencies beyond what you have

**Deliverables**:
- Events flowing from all modules
- Events persisted locally (durable)
- Events transmitted to cloud
- Dashboard shows real-time data

**Timeline**: 2-3 days

---

### Phase 2: OpenTelemetry Wrapper (Weeks 3-4)
**Goal**: Standardize on industry format, open door to advanced tooling

```python
# Wrap events in OTEL metrics
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
extracted_counter = meter.create_counter("records_extracted")
extracted_counter.add(150)  # Same data, OTEL format

# Same event, now also visible to Prometheus, Datadog, etc.
```

**What changes**:
- ✅ Add OpenTelemetry SDK (~30 lines)
- ✅ Wrap key metrics
- ✅ Expose `/metrics` endpoint
- ✅ Keep all existing code working

**Timeline**: 1 day (mostly integration, not rewriting)

---

### Phase 3+: Full OTEL Stack (Later, if needed)
- Add Jaeger for distributed tracing
- Export to Prometheus
- Custom Grafana dashboards
- Advanced analytics

**Key point**: NO BREAKING CHANGES from Phase 1 → Phase 2 → Phase 3

---

## Architecture Diagram

```
┌──────────────────────────────────────────────┐
│ Agent Modules                                │
│ ├─ main.py                                   │
│ ├─ tally_setup.py                            │
│ ├─ orchestrator.py                           │
│ │  ├─ extractor/                             │
│ │  ├─ queue/                                 │
│ │  └─ transmitter/                           │
│ └─ service/windows_service.py                │
└───────────────┬──────────────────────────────┘
                │ logger.info(...) / bus.emit(...)
                ▼
        ┌───────────────────┐
        │  Structlog        │  Phase 1
        │  (JSON logging)   │  ✅ NOW
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  Custom EventBus  │  Phase 1
        │  (pub-sub + state)│  ✅ NOW
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────────────────┐
        │  Dual Persistence             │  Phase 1
        ├─────────────────────────────┤  ✅ NOW
        │ In-Memory Ring Buffer + SQLite
        └─────────┬─────────────────────┘
                  │
        ┌─────────▼──────────────────────┐
        │  Cloud Telemetry API           │  Phase 1
        │  POST /v1/telemetry/events     │  ✅ NOW
        └─────────┬──────────────────────┘
                  │
        ┌─────────▼──────────────────────┐
        │  Cloud Database                │  Phase 1
        │  telemetry_events table        │  ✅ NOW
        └─────────┬──────────────────────┘
                  │
        ┌─────────▼──────────────────────┐
        │  Dashboard Widgets             │  Phase 1+
        │  Real-time status, metrics     │  ✅ SOON
        └────────────────────────────────┘

        Optional: OpenTelemetry Wrapper (Phase 2)
        ─────────────────────────────────
        Sits on top, zero breaking changes
        Enables Prometheus, Jaeger, etc.
```

---

## Implementation Roadmap

### Phase 1A: Structlog Setup (Day 1)
- [ ] Add structlog to `pyproject.toml`
- [ ] Configure logging in `agent/main.py`
- [ ] Test: `logger.info("test")`

### Phase 1B: Custom EventBus (Day 1-2)
- [ ] Create `agent/telemetry/event_bus.py` (~150 lines)
- [ ] Create `agent/telemetry/storage.py` (SQLite) (~100 lines)
- [ ] Integration tests

### Phase 1C: Event Emission (Day 2)
- [ ] Add `bus.emit()` calls to:
  - [ ] `agent/main.py` (startup/shutdown)
  - [ ] `agent/tally_setup.py` (connection events)
  - [ ] `agent/orchestrator.py` (sync cycle)
  - [ ] `agent/extractor/` (extraction events)
  - [ ] `agent/queue/` (queue events)
  - [ ] `agent/transmitter/` (transmission events)
  - [ ] `agent/service/` (service events)

### Phase 1D: Cloud Integration (Day 2-3)
- [ ] Extend `cloudplatform/api/telemetry.py`
- [ ] Add `POST /v1/telemetry/events` endpoint
- [ ] Create `telemetry_events` table in PostgreSQL
- [ ] Test end-to-end flow

### Phase 1E: Dashboard (Day 3)
- [ ] Add dashboard widgets
- [ ] Display event metrics
- [ ] Real-time event stream

---

## Code Examples

### Example 1: Emit Event
```python
# In any agent module
from agent.telemetry import get_event_bus

bus = get_event_bus()
bus.emit("extraction.completed", {
    "ledgers_extracted": 150,
    "vouchers_extracted": 500,
    "duration_ms": 2340,
})

# Automatically:
# 1. Logged to console (via Structlog)
# 2. Persisted to SQLite
# 3. Queued for cloud transmission
# 4. Notifies any subscribers
```

### Example 2: Subscribe to Events
```python
# In dashboard or monitoring component
bus.subscribe("extraction.completed", on_extraction_done)

def on_extraction_done(event):
    print(f"Extraction done: {event['data']['ledgers_extracted']} records")
```

### Example 3: Query Local Events
```python
# For debugging or local metrics
events = bus.get_recent_events("extraction.completed", limit=100)
for event in events:
    print(f"{event['timestamp']}: {event['data']}")
```

---

## Success Metrics

After Phase 1, we should have:

✅ **Completeness**
- All critical operations emit events
- Event types cover full agent lifecycle

✅ **Reliability**
- Events survive agent crashes (SQLite)
- Events reach cloud within 5 seconds
- No data loss on failure

✅ **Performance**
- Telemetry < 1% CPU overhead
- Telemetry < 50MB memory
- Sync operations not blocked

✅ **Usability**
- Dashboard shows real-time events
- Easy to troubleshoot via dashboard
- Clear event timestamps and severity levels

✅ **Code Quality**
- 90%+ test coverage
- Type hints throughout
- Clear documentation

---

## Dependencies

### Phase 1 Dependencies
```
structlog>=23.1.0        # JSON logging
python>=3.10             # We have 3.12 ✓
sqlite3                  # Built-in ✓
(existing) requests      # Already in pyproject.toml ✓
```

### Phase 2 Dependencies (Optional)
```
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
prometheus-client>=0.17.0
```

**Total new dependencies for Phase 1**: Just `structlog` (~50KB)

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Events block sync | Medium | High | Use async queue, benchmark overhead |
| SQLite fills up | Low | Medium | Implement retention policy (7 days) |
| Cloud API down | Low | Medium | Events persist locally, retry on reconnect |
| Performance degradation | Medium | Medium | Continuous monitoring, tuneable batch size |

---

## Comparison: Before vs After

### Before (Current State)
```
Sync runs...
Logs go to console
No historical data
Hard to debug issues
No metrics/KPIs
No real-time monitoring
```

### After Phase 1 (Recommended)
```
Sync runs...
Logs are structured JSON (queryable)
Events persisted (7 days)
Easy to replay and debug
Rich metrics (extracted, transmitted, errors)
Real-time dashboard
Cloud integration ready
```

### After Phase 2 (Optional)
```
Same as Phase 1 +
Industry-standard format (OTEL)
Can export to Prometheus/Datadog/etc.
Advanced analytics ready
Distributed tracing support
```

---

## Decision Checklist

Before we proceed, confirm:

- [ ] ✅ Agree: Structlog + Custom Bus for Phase 1
- [ ] ✅ Agree: Path to OpenTelemetry in Phase 2 (no breaking changes)
- [ ] ✅ Understand: This is MVP-focused, not over-engineered
- [ ] ✅ Understand: We're NOT locked into this (easy to change)
- [ ] ✅ Ready: To start implementation immediately after approval

---

## Next: What Do You Think?

**Questions to answer**:

1. **Does this approach feel right to you?**
   - Too simple? Too complex? Just right?

2. **Timeline realistic?**
   - 2-3 days for Phase 1?

3. **Dashboard priorities?**
   - What metrics matter most?

4. **Event types complete?**
   - Missing any events?

5. **Any concerns?**
   - Performance? Complexity? Something else?

---

## TL;DR

**Use**: Structlog + Custom Event Bus  
**Why**: Fast MVP, future-proof, no external dependencies  
**Timeline**: 2-3 days  
**Next**: You approve → I implement Phase 1 completely  

---

**Decision requested**: Approve approach → Proceed with implementation

