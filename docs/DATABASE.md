# Final Database and ERD Reference

The finalized Django persistence model contains six entities.

## ERD

```text
┌──────────────────────┐
│       Device         │
├──────────────────────┤
│ PK id UUID           │
│ name                 │
│ ip_address IPv4      │
│ device_type          │
│ status               │
│ monitoring_enabled   │
│ created_at           │
│ updated_at           │
└──────────┬───────────┘
           │ 1
           │
           │ 1
┌──────────▼───────────┐
│ MonitoringConfig     │
├──────────────────────┤
│ PK/FK device         │
│ interval_seconds     │
│ snmp_enabled         │
│ snmp_version         │
│ snmp_community       │
│ snmp_port            │
│ snmp_timeout_seconds │
│ available_metrics    │
└──────────────────────┘

Device 1 ───────────< MonitoringRecord
Device 1 ───────────< SNMPMetric
Device 1 ───────────< FaultEvent
FaultEvent 1 ─────── 1 Notification
```

## Entities

### Device

Represents a monitored network device.

- UUID primary key
- name
- IPv4 address
- device type
- monitoring status
- current health status
- creation/update timestamps

Registering a new device automatically creates its one-to-one monitoring configuration.

### MonitoringConfiguration

Stores monitoring behavior for one device.

- interval in seconds
- monitoring enablement through the related device
- SNMP enablement
- SNMP version
- SNMP community
- SNMP port
- SNMP timeout
- selected metrics

The SNMP community is sensitive configuration and is not returned by the configuration API.

### MonitoringRecord

Immutable result of an ICMP monitoring execution.

- UUID
- device foreign key
- timestamp
- reachable
- latency in milliseconds
- packet-loss percentage

Indexes support device/time, timestamp, and device/reachability/time access.

### SNMPMetric

Persisted selected SNMP measurement.

- UUID
- device foreign key
- timestamp
- metric name
- OID
- value
- value type

Indexes support device/time and device/metric/time access.

### FaultEvent

Represents a detected network fault.

- UUID
- device foreign key
- fault type
- severity
- detected time
- status
- description
- resolved time

Supported fault types in the model:

- `DEVICE_UNREACHABLE`
- `HIGH_LATENCY`
- `HIGH_PACKET_LOSS`
- `HIGH_CPU_USAGE`
- `HIGH_MEMORY_USAGE`
- `INTERFACE_FAILURE`
- `CONNECTIVITY_FAILURE`

The active/acknowledged state has a conditional uniqueness constraint so one device cannot have duplicate active/acknowledged faults of the same type.

### Notification

One-to-one record attached to a `FaultEvent`.

- UUID
- fault foreign key
- read/unread status
- creation time

The current system provides in-application notification state. It does not claim external email, SMS, or push delivery.

## Deletion behavior

`Device` uses cascading deletion for its monitoring configuration, monitoring records, SNMP metrics, and fault records. A fault deletion cascades to its notification.

Because device deletion is destructive, the API should be treated accordingly.

## Database technology

The finalized project uses SQLite for the documented deployment context. The schema is managed through Django migrations.

Useful commands:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
```

## Source of truth

The authoritative implementation is `backend/network/models.py` and its migrations. This document is a human-readable ERD/reference and should be updated whenever the Django schema changes.
