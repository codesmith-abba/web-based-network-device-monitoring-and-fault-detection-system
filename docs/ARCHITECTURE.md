# Final System Architecture

## 1. Deployment architecture

```text
                         ┌──────────────────┐
                         │      Browser     │
                         │ React + TypeScript│
                         └────────┬─────────┘
                                  │ HTTPS / /api
                                  ▼
                         ┌──────────────────┐
                         │      Nginx       │
                         │ static + reverse │
                         │      proxy       │
                         └────────┬─────────┘
                                  │ localhost HTTP
                                  ▼
                         ┌──────────────────┐
                         │     Gunicorn     │
                         │   Django WSGI   │
                         └────────┬─────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │    Device    │  │  Monitoring  │  │    Fault     │
        │  Management  │  │ ICMP / SNMP  │  │  Detection   │
        └──────────────┘  └──────┬───────┘  └──────┬───────┘
                                  │                 │
                                  └────────┬────────┘
                                           ▼
                                    ┌────────────┐
                                    │   SQLite   │
                                    └────────────┘

             Background monitoring path

             Celery Beat
                  │
                  ▼
             Redis broker
                  │
                  ▼
             Celery worker
                  │
                  └──────→ monitoring services
```

## 2. Runtime responsibilities

### Frontend

The React application presents administrator workflows and consumes the REST API. It does not perform network-device monitoring itself.

### Django API

Django REST Framework validates requests, enforces administrator permissions, exposes resources, and coordinates domain services.

### Monitoring services

The monitoring layer performs bounded ICMP checks and configured SNMP collection. Each monitoring execution persists historical data and evaluates relevant fault rules.

### Fault services

Fault detection uses deterministic thresholds and the `FaultEvent` lifecycle. Notifications are linked to selected generated faults.

### Celery and Redis

Celery executes background monitoring. Celery Beat periodically dispatches due checks. Redis provides the Celery broker/result backend and distributed monitoring locks.

## 3. Request flow

```text
Administrator
    │
    ▼
React page
    │
    ▼
API client
    │
    ▼
Django authentication/permission
    │
    ▼
Serializer validation
    │
    ▼
View/service layer
    │
    ├── Device operation
    ├── Monitoring operation
    ├── Fault operation
    └── Historical query
    │
    ▼
Database / monitoring service
    │
    ▼
JSON response
    │
    ▼
React state/UI
```

## 4. Automated monitoring flow

```text
Celery Beat
    │ every 5 seconds
    ▼
dispatch_due_monitoring_tasks
    │
    ▼
Check enabled devices + configured interval
    │
    ▼
Acquire Redis device lock
    │
    ▼
ICMP monitoring
    │
    ├── reachability
    ├── latency
    └── packet loss
    │
    ├───────────────┐
    │               │
    ▼               ▼
Persist record   Evaluate faults
                    │
                    ├── create/update fault
                    ├── create notification where applicable
                    └── resolve recovered condition
    │
    ▼
Release Redis lock
```

If SNMP is enabled, configured SNMP metrics are collected as a separate stage. SNMP failure is isolated and does not invalidate the ICMP monitoring record.

## 5. Security boundary

```text
Public
  └── /api/health/

Authenticated staff administrator
  ├── authentication session/token operations
  ├── devices
  ├── monitoring
  ├── faults
  ├── history
  └── notifications
```

The API does not expose SNMP community values through monitoring configuration responses.

## 6. Production boundary

The public deployment is intended to expose Nginx, not Django/Gunicorn or Redis directly. Redis remains bound to localhost in the documented deployment configuration. HTTPS is required before public production traffic.
