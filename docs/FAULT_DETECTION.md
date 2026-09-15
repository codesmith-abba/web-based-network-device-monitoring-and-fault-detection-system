# Fault Detection

Phase 17 implements deterministic, threshold-based fault detection from monitoring results. It does not perform machine-learning prediction or cybersecurity threat detection.

## Monitoring thresholds

The default policy is defined by `FaultThresholds` in `backend/network/faults/detection.py`.

| Condition | Medium | High/Critical |
|---|---:|---:|
| ICMP latency | >= 200 ms | >= 500 ms (high) |
| Packet loss | >= 20% | >= 50% (high) |
| CPU usage | >= 80% | >= 90% (critical) |
| Memory usage | >= 80% | >= 90% (critical) |
| Device unreachable | — | Critical |

The evaluator accepts a custom `FaultThresholds` instance, so the threshold policy is configurable at the service boundary without changing the fault model.

## Fault types

- `DEVICE_UNREACHABLE` — ICMP monitoring reports the device as unreachable; severity is critical.
- `HIGH_LATENCY` — latency reaches the medium or high threshold.
- `HIGH_PACKET_LOSS` — packet loss reaches the medium or high threshold.
- `HIGH_CPU_USAGE` — a stored supported CPU SNMP metric reaches the configured CPU threshold.
- `HIGH_MEMORY_USAGE` — a stored supported memory SNMP metric reaches the configured memory threshold.

CPU and memory detection accepts normalized metric names such as `cpu`, `cpuUsage`, `cpu_usage`, `cpu_utilization`, `memory`, `memory_usage`, and `memory_utilization`. Unsupported or non-numeric SNMP metrics are ignored by the resource evaluator.

## Fault lifecycle

Fault evaluation runs after an ICMP monitoring measurement is persisted. SNMP resource metrics are evaluated when they are successfully stored by the SNMP collector.

An active fault is reused instead of creating another event for the same device and fault type. The database also enforces one active/acknowledged event per device and fault type.

When a later measurement no longer meets a fault condition, the active or acknowledged event is automatically marked `resolved` and receives `resolved_at`. A resolved fault remains in history and a later recurrence creates a new event.

## API

Faults remain available through the existing fault endpoints, including:

- `GET /api/faults/`
- `GET /api/faults/<id>/`
- `POST /api/faults/<id>/acknowledge/`
- `POST /api/faults/<id>/resolve/`
- `PATCH /api/faults/<id>/status/`
- `GET /api/fault-history/`

There is no separate prediction endpoint. Fault creation is tied to the monitoring data pipeline.
