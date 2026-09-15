# Release Notes — v1.0.0 Academic Release Candidate

## Overview

This release candidate represents the completed implementation and documentation milestone for the Web-Based Network Device Monitoring and Fault Detection System.

## Included

### Administrator and device management

- Token-based administrator authentication
- Protected administrator API access
- Device registration and management
- IPv4 validation
- Monitoring configuration

### Monitoring

- Immediate ICMP monitoring
- Periodic background monitoring
- Reachability status
- Latency measurement
- Packet-loss recording
- Configured SNMP v1/v2c collection
- Historical monitoring records

### Fault detection

- Device-unreachable detection
- High-latency detection
- High-packet-loss detection
- Supported SNMP CPU/memory threshold detection
- Fault severity
- Active/acknowledged/resolved lifecycle
- Automatic recovery resolution for supported monitoring conditions

### Notifications and history

- In-application fault notifications
- Read/unread notification state
- Monitoring history API
- Fault history API
- Bounded historical queries and aggregation

### Frontend

- React/TypeScript administrator dashboard
- Device management UI
- Monitoring configuration UI
- Monitoring details/history
- Fault management UI
- Notification experience
- Authenticated backend integration
- Production build configuration

### Reliability and security

- Django production security defaults
- Token rotation on login
- Login throttling
- Input validation
- Protected fault creation path
- Redis lock failure handling
- Frontend expired-auth handling
- Database constraints and indexes
- Comprehensive backend regression coverage

### Deployment

- Linux deployment documentation
- Nginx configuration
- Gunicorn/Django WSGI service
- Celery worker service
- Celery Beat service
- Redis service configuration guidance
- Static/media handling
- HTTPS and HSTS production guidance
- Deployment smoke test

## Validation status

The project includes:

- Phase 23 full-system integration coverage
- Phase 24 controlled network-monitoring validation
- Phase 25 security/reliability regression tests
- Phase 27 academic requirements traceability
- Phase 28 final documentation and release preparation

The academic traceability matrix reports all 18 requested requirements as satisfied, with SNMP explicitly qualified as controlled/simulated validation.

## Scope limitations

This release does not claim:

- universal physical router/switch/vendor interoperability;
- physical device repair;
- automatic network-device reconfiguration;
- intrusion detection or cybersecurity threat analysis;
- ISP infrastructure monitoring;
- advanced predictive maintenance;
- full machine-learning network prediction;
- hardware-level physical diagnosis;
- external email/SMS/browser-push notification delivery.

## Release procedure

After final local validation and repository-hygiene review:

```bash
git status --short
git diff --check

git tag -a v1.0.0 -m "v1.0.0 — academic final release"
git push origin v1.0.0
```

## Documentation

Start with [`README.md`](README.md), then:

- `backend/README.md`
- `frontend/README.md`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE.md`
- `docs/DFD_UML.md`
- `docs/API.md`
- `docs/FAULT_API.md`
- `docs/HISTORICAL_API.md`
- `docs/PHASE_27_REQUIREMENTS_TRACEABILITY.md`
- `docs/PHASE_28_FINAL_RELEASE.md`
- `deploy/README.md`
