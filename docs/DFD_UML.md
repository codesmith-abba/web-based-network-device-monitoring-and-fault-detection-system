# Final DFD and UML Workflow Reference

These diagrams describe the implemented workflow, not future functionality.

## 1. Context-level DFD

```text
                 ┌─────────────────────┐
                 │ Administrator       │
                 └──────────┬──────────┘
                            │
                  login / management / review
                            │
                            ▼
              ┌──────────────────────────┐
              │ Network Monitoring Web   │
              │ Application              │
              └──────────┬───────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Device data   Monitoring data   Fault state
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    SQLite database
                         │
                         ▼
                 Dashboard/history/
                   notifications
```

## 2. Level-1 DFD

```text
Administrator
    │
    ├──────────────→ (1.0 Authentication)
    │                       │
    │                       ▼
    │                 authenticated session
    │
    ├──────────────→ (2.0 Device Management)
    │                       │
    │                       ▼
    │                  Device records
    │
    ├──────────────→ (3.0 Monitoring Configuration)
    │                       │
    │                       ▼
    │               MonitoringConfiguration
    │
    │                 (4.0 Monitoring Engine)
    │                       │
    │              ┌────────┴────────┐
    │              ▼                 ▼
    │            ICMP               SNMP
    │              │                 │
    │              ▼                 ▼
    │        MonitoringRecord     SNMPMetric
    │              │
    │              ▼
    │        (5.0 Fault Detection)
    │              │
    │              ▼
    │          FaultEvent
    │              │
    │              ▼
    │         Notification
    │
    └──────────────← (6.0 Dashboard / History)
```

## 3. Monitoring sequence UML

```text
Administrator   React   Django API   Celery/Redis   Monitor   Database
     │            │         │             │            │         │
     │ configure  │         │             │            │         │
     ├───────────→│────────→│             │            │         │
     │            │         │ save config │            │────────→│
     │            │         │             │            │         │
     │            │         │             │ dispatch   │         │
     │            │         │             │───────────→│         │
     │            │         │             │ acquire lock         │
     │            │         │             │───────────→│         │
     │            │         │             │            │ ICMP    │
     │            │         │             │            │ / SNMP  │
     │            │         │             │            │────────→ │
     │            │         │             │            │ result  │
     │            │         │             │            │────────→ │
     │            │         │             │            │ evaluate│
     │            │         │             │            │ fault   │
     │            │         │             │            │────────→ │
     │            │         │             │ release    │         │
     │            │         │             │───────────→│         │
     │            │ request dashboard      │            │         │
     │───────────→│────────→│─────────────┼────────────┼────────→│
     │            │←────────│ JSON state  │            │         │
     │←───────────│         │             │            │         │
```

## 4. Fault lifecycle UML/state model

```text
                 condition detected
                        │
                        ▼
                    ┌────────┐
                    │ ACTIVE │
                    └───┬────┘
                        │ acknowledge
                        ▼
                 ┌──────────────┐
                 │ ACKNOWLEDGED │
                 └──────┬───────┘
                        │ resolve / recovery
                        ▼
                   ┌──────────┐
                   │ RESOLVED │
                   └──────────┘

ACTIVE ───── resolve / recovery ─────→ RESOLVED
```

## 5. Authentication workflow

```text
User
 │ credentials
 ▼
POST /api/auth/login/
 │
 ├── invalid → 401
 │
 └── valid staff user
          │
          ▼
      DRF token
          │
          ▼
     React session
          │
          ▼
Protected API requests
          │
          ├── no/invalid token → 401
          ├── authenticated non-staff → 403
          └── staff → endpoint access
```

## 6. Scope boundary

The diagrams intentionally stop at monitoring, fault detection, history, and administrator notification. They do not show physical repair, automatic network-device reconfiguration, intrusion detection, ISP monitoring, predictive maintenance, or ML-based network prediction because those are outside the documented implemented scope.
