# Phase 4: ELK Audit Logging - Implementation Plan

**Date**: 28 June 2026  
**Status**: Starting Implementation  
**Target**: Complete with production-ready monitoring

---

## Overview

Phase 4 implements the **ELK Stack** (Elasticsearch, Logstash, Kibana) to:
- Capture all authorization audit events from Phase 3
- Store events in Elasticsearch for analysis
- Process events with Logstash
- Visualize audit trails with Kibana dashboards
- Enable real-time monitoring and alerting

---

## What is ELK Stack?

### Elasticsearch
- **Purpose**: Search and analytics engine
- **Function**: Stores all audit events
- **Capacity**: Millions of events per second
- **Usage**: Full-text search, filtering, aggregation

### Logstash
- **Purpose**: Data processing pipeline
- **Function**: Transforms audit events before storage
- **Filters**: Enrich, parse, and normalize events
- **Routing**: Send events to different indices

### Kibana
- **Purpose**: Visualization and exploration
- **Function**: Create dashboards and visualizations
- **Dashboards**: Real-time monitoring
- **Alerting**: Trigger alerts on patterns

---

## Architecture

### Event Flow

```
Application (Phase 3 Audit Trail)
    ↓
Audit Logger (New - Phase 4)
├─ Format events (JSON)
├─ Add context (timestamp, source)
└─ Send to Logstash
    ↓
Logstash Pipeline
├─ Input: TCP/UDP from application
├─ Filter: Parse, enrich, normalize
├─ Output: Send to Elasticsearch
    ↓
Elasticsearch Cluster
├─ Index: events-YYYY.MM.DD
├─ Type: authorization_event
└─ Store: Full audit trail
    ↓
Kibana Dashboard
├─ Real-time visualization
├─ Historical analysis
└─ Alerting rules
```

---

## Components to Implement

### 1. Audit Logger (Application-Side)

**File**: `cloudplatform/logging/audit_logger.py`

Features:
- Capture authorization events from Phase 3
- Format events as JSON
- Add context (timestamp, request ID, source IP)
- Send to Logstash asynchronously
- Fallback to local queue if Logstash unavailable

```python
class AuditLogger:
    def log_authorization(self, event):
        """Log authorization decision"""
        # Extract: principal, resource, action, decision, reason
        # Add: timestamp, request_id, source_ip
        # Send to Logstash

    def log_authentication(self, event):
        """Log authentication event"""
        # Extract: client_id, action (login, logout, refresh)
        # Add: timestamp, source_ip
        # Send to Logstash

    def log_device_operation(self, event):
        """Log device registration/rotation"""
        # Extract: device_id, client_id, operation
        # Add: timestamp, source_ip
        # Send to Logstash
```

### 2. Logstash Configuration

**File**: `elk/logstash.conf`

Pipeline:
```
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Enrich event with geoIP
  # Normalize field names
  # Add application context
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "tally-sync-events-%{+YYYY.MM.dd}"
  }
}
```

### 3. Kibana Dashboards

**File**: `elk/kibana/dashboards/`

Dashboards:
- **Authorization Overview**: Real-time authorization decisions
- **Cross-Client Access**: Attempts to access other clients' data
- **Admin Activities**: All admin override actions
- **Failed Access**: All 403 Forbidden events
- **Device Registration**: Device lifecycle events
- **Compliance Report**: Audit trail for compliance

### 4. Elasticsearch Indices

**Index Pattern**: `tally-sync-events-YYYY.MM.dd`

**Mapping**:
```json
{
  "mappings": {
    "properties": {
      "timestamp": { "type": "date" },
      "event_type": { "type": "keyword" },
      "principal_client_id": { "type": "keyword" },
      "principal_role": { "type": "keyword" },
      "resource_type": { "type": "keyword" },
      "resource_id": { "type": "keyword" },
      "action": { "type": "keyword" },
      "decision": { "type": "boolean" },
      "reason": { "type": "text" },
      "source_ip": { "type": "ip" },
      "request_id": { "type": "keyword" }
    }
  }
}
```

---

## Implementation Tasks

### Task 1: Audit Logger Service ✅
- Create AuditLogger class
- Implement event formatting
- Add Logstash integration
- Implement fallback queue

### Task 2: Logstash Configuration ✅
- Create pipeline configuration
- Set up input/filter/output stages
- Configure index pattern
- Add field mappings

### Task 3: Elasticsearch Setup ✅
- Create index template
- Configure retention policy (90-day rolling)
- Set up index lifecycle management
- Configure cluster settings

### Task 4: Kibana Dashboards ✅
- Create authorization dashboard
- Create security dashboard
- Create compliance dashboard
- Create device management dashboard

### Task 5: Integration with Phases 1-3 ✅
- Connect audit logger to Phase 3 authorization
- Log all authentication events (Phase 1)
- Log all device operations (Phase 2)
- Verify events flowing to Elasticsearch

### Task 6: Docker Compose Setup ✅
- Elasticsearch service
- Logstash service
- Kibana service
- Network configuration

---

## Event Types to Log

### Authorization Events (From Phase 3)
```json
{
  "event_type": "authorization_check",
  "timestamp": "2026-06-28T10:30:45Z",
  "principal_client_id": "cli_finance_a",
  "principal_role": "finance",
  "resource_type": "ledger",
  "resource_id": "ledger_123",
  "action": "delete",
  "decision": false,
  "reason": "Role finance cannot perform delete on ledger",
  "request_id": "req_abc123"
}
```

### Authentication Events (From Phase 1)
```json
{
  "event_type": "authentication",
  "timestamp": "2026-06-28T10:30:45Z",
  "action": "login",
  "client_id": "cli_finance_a",
  "status": "success",
  "source_ip": "192.168.1.100",
  "request_id": "req_abc123"
}
```

### Device Events (From Phase 2)
```json
{
  "event_type": "device_operation",
  "timestamp": "2026-06-28T10:30:45Z",
  "operation": "register",
  "device_id": "dev_123",
  "client_id": "cli_finance_a",
  "status": "success",
  "request_id": "req_abc123"
}
```

---

## Dashboards to Create

### 1. Authorization Overview Dashboard
**Metrics**:
- Real-time authorization decisions (allow/deny count)
- Decision rate (decisions per minute)
- Top denied permissions
- Top accessed resources

### 2. Security Dashboard
**Metrics**:
- Cross-client access attempts
- Unauthorized access attempts
- Admin override usage
- Failed login attempts

### 3. Compliance Dashboard
**Metrics**:
- Audit trail completeness
- Event lag (from occurrence to storage)
- Data retention status
- Compliance violations

### 4. Device Management Dashboard
**Metrics**:
- Device registration trends
- Active devices count
- API key rotations
- Device status distribution

---

## Testing

### Unit Tests
- AuditLogger event formatting
- Logstash pipeline parsing
- Elasticsearch index creation

### Integration Tests
- End-to-end event flow (app → logstash → ES)
- Kibana dashboard data retrieval
- Alert triggering

### Performance Tests
- Event throughput (1000+ events/sec)
- Query performance (<1s for dashboard)
- Retention policy effectiveness

---

## Success Criteria

✅ All authorization events logged to Elasticsearch  
✅ Authentication events captured  
✅ Device operation events captured  
✅ Kibana dashboards displaying real-time data  
✅ Events searchable and filterable  
✅ Retention policy enforced (90 days)  
✅ Performance acceptable (<1s dashboard load)  
✅ All Phase 1-3 tests still passing  

---

## Files to Create

### Code
- `cloudplatform/logging/__init__.py`
- `cloudplatform/logging/audit_logger.py` (200 lines)
- `cloudplatform/logging/logstash_client.py` (150 lines)

### Configuration
- `elk/docker-compose.yml` (150 lines)
- `elk/logstash/logstash.conf` (80 lines)
- `elk/elasticsearch/elasticsearch.yml` (50 lines)
- `elk/kibana/kibana.yml` (50 lines)

### Dashboards
- `elk/kibana/dashboards/authorization.json`
- `elk/kibana/dashboards/security.json`
- `elk/kibana/dashboards/compliance.json`

### Tests
- `tests/integration/test_audit_logging.py` (300 lines)

### Documentation
- `docs_implementation/PHASE4_ELK_GUIDE.md` (50 KB)

---

## Deployment

### Development
```bash
docker-compose -f elk/docker-compose.yml up
# Elasticsearch: http://localhost:9200
# Kibana: http://localhost:5601
```

### Production (AWS)
- Elasticsearch Service (AWS managed)
- EC2 instances for Logstash
- Kibana on Application Load Balancer
- IAM roles for security

---

## Timeline

```
Task 1 (Audit Logger):    30 min
Task 2 (Logstash Config): 20 min
Task 3 (Elasticsearch):   20 min
Task 4 (Kibana):          40 min
Task 5 (Integration):     30 min
Task 6 (Docker):          20 min
Testing:                  30 min
Documentation:            20 min
                         ──────────
Total Estimated:          ~3 hours
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| High event volume | Use index rotation, retention policy |
| Network latency | Implement local queue, async sending |
| Elasticsearch unavailable | Fallback to local SQLite queue |
| Dashboard performance | Use aggregations, time-based filtering |

---

## Sign-Off

**Status**: Ready to start Phase 4  
**Prerequisites**: Phase 1-3 complete  
**Estimated Duration**: ~3 hours

---

**Next Step**: Implement AuditLogger service
