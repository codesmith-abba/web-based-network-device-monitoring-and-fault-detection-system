# Phase 27 — Requirements Traceability and Validation

## Purpose

This document validates the implemented system against the authoritative academic requirements in Chapter 1 and Chapter 3.

The requirements are derived from:

- Chapter 1, Section 1.3 — Aim and Objectives
- Chapter 1, Section 1.5 — Scope of the Study
- Chapter 3, Section 3.3 — Analysis of the Proposed System
- Chapter 3, Section 3.3.1 — Major Features of the Proposed System
- Chapter 3, Sections 3.4–3.5 — System Design Specifications and Technologies

The validation deliberately does not claim functionality outside the documented scope. Where physical network infrastructure is unavailable, controlled/simulated monitoring conditions are used, consistent with the limitation stated in Chapter 1.

## Requirement Traceability Checklist

| # | Academic requirement | Implementation | Test / validation | Evidence | Status |
|---|---|---|---|---|---|
| 1 | Centralized device management | Django `Device` model, device API/viewset, React administrative dashboard | `NetworkApiTests.test_devices_list_uses_frontend_contract`; device CRUD test; Phase 23 integration test | `backend/network/models.py`, `backend/network/views.py`, `backend/network/tests.py`, `backend/network/test_system_integration.py` | **PASS** |
| 2 | Device registration | `POST /api/devices/`; validated device serializer; automatic monitoring configuration creation | `NetworkApiTests.test_device_create_creates_monitoring_configuration`; Phase 23 registers a device through the API | `backend/network/tests.py`, `backend/network/test_system_integration.py` | **PASS** |
| 3 | Monitoring configuration | `MonitoringConfiguration` stores interval, enablement, SNMP settings, timeout and selected metrics; configuration API | Phase 23 updates `intervalSeconds`; monitoring configuration validation tests | `backend/network/models.py`, `backend/network/serializers.py`, `backend/network/test_system_integration.py`, `backend/network/tests.py` | **PASS** |
| 4 | Periodic monitoring | Celery `dispatch_due_monitoring_tasks` evaluates configured intervals; Celery Beat invokes dispatch every five seconds; immediate monitoring can also be triggered through API | Phase 23 configures a monitoring interval; Celery task/Beat implementation and regression tests validate scheduling infrastructure | `backend/backend/settings.py`, `backend/network/tasks.py`, `backend/network/test_monitoring_validation.py` | **PASS** |
| 5 | ICMP connectivity | Python ICMP/ping monitoring service validates IPv4 and records reachability | `NetworkMonitoringValidationTests.test_01_reachable_device`; `test_02_unreachable_device_creates_fault_and_notification`; ping engine tests | `backend/network/monitoring/services.py`, `backend/network/test_monitoring_validation.py`, `backend/network/tests.py` | **PASS** |
| 6 | Latency measurement | `PingResult.latency_ms` is stored in `MonitoringRecord.latency_ms` and exposed through the API/dashboard | Reachable-device test and Phase 23 integration test verify 20 ms and 650 ms measurements | `backend/network/monitoring/services.py`, `backend/network/models.py`, `backend/network/tests.py`, `backend/network/test_system_integration.py` | **PASS** |
| 7 | Packet-loss monitoring | ICMP result stores `packet_loss_percent`; fault evaluation uses packet-loss thresholds | `NetworkMonitoringValidationTests.test_04_packet_loss_creates_fault`; reachable/unreachable monitoring tests verify 0%/100% loss | `backend/network/models.py`, `backend/network/faults/detection.py`, `backend/network/test_monitoring_validation.py`, `backend/network/tests.py` | **PASS** |
| 8 | SNMP monitoring where supported | SNMP service supports configured SNMPv1/v2c collection of selected metrics and persists `SNMPMetric` records; failures are isolated | `NetworkMonitoringValidationTests.test_05_snmp_supported_device_persists_metrics`; `test_06_snmp_unavailable_device_is_isolated`; Celery partial-result test | `backend/network/snmp/services.py`, `backend/network/models.py`, `backend/network/test_monitoring_validation.py` | **PASS — controlled/simulated validation** |
| 9 | Predefined fault detection | Deterministic fault rules evaluate reachability, latency, packet loss and selected SNMP CPU/memory metrics | Phase 24 validation tests for unreachable, high latency and packet loss; fault detection unit/integration tests | `backend/network/faults/detection.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 10 | Fault severity | Fault rules assign severity levels according to predefined thresholds; fault model stores severity | High-latency and high-packet-loss validation tests assert `HIGH`; fault model/detection tests cover severity handling | `backend/network/faults/detection.py`, `backend/network/models.py`, `backend/network/test_monitoring_validation.py` | **PASS** |
| 11 | Fault event recording | `FaultEvent` records affected device, fault type, severity, detection time, status and related information | Controlled monitoring creates `FaultEvent`; integration test retrieves the created fault | `backend/network/models.py`, `backend/network/faults/detection.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 12 | Active faults | Fault lifecycle stores `ACTIVE` status; dashboard and fault APIs expose active faults | Validation asserts newly detected faults are active; integration dashboard asserts one active fault | `backend/network/models.py`, `backend/network/views.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 13 | Resolved faults | Fault service supports resolution and automatic recovery resolution after healthy monitoring data | `NetworkApiTests.test_fault_can_be_acknowledged_and_resolved`; `NetworkMonitoringValidationTests.test_09_fault_resolves_after_healthy_measurement`; integration workflow | `backend/network/faults/services.py`, `backend/network/test_monitoring_validation.py`, `backend/network/tests.py`, `backend/network/test_system_integration.py` | **PASS** |
| 14 | Monitoring history | Immutable `MonitoringRecord` entries plus monitoring-history and snapshot APIs | `NetworkMonitoringValidationTests.test_10_historical_records_are_exposed`; integration test verifies history count and snapshot history | `backend/network/models.py`, `backend/network/historical_api.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 15 | Fault history | Persisted `FaultEvent` records plus fault-history API with filters and bounded historical queries | `NetworkMonitoringValidationTests.test_10_historical_records_are_exposed`; integration test verifies fault-history response | `backend/network/historical_api.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 16 | Dashboard | React dashboard consumes authenticated Django APIs for device health, monitoring state, active faults and related status information | Phase 23 integration test validates `/api/dashboard/`; Phase 24 dashboard validation verifies total devices, active faults and latency | `frontend/`, `backend/network/views.py`, `backend/network/test_monitoring_validation.py`, `backend/network/test_system_integration.py` | **PASS** |
| 17 | Notifications | `Notification` is linked to selected fault events and exposes unread/read API state | Unreachable/high-latency fault tests verify notification creation; notification read test and Phase 23 integration workflow verify read state | `backend/network/models.py`, `backend/network/views.py`, `backend/network/test_monitoring_validation.py`, `backend/network/tests.py`, `backend/network/test_system_integration.py` | **PASS** |
| 18 | Administrator authentication | Django/DRF token authentication; administrator/staff permission boundary; login, logout and current-user endpoints | Authentication tests cover successful login, invalid credentials, token invalidation, non-admin rejection and protected endpoint permissions | `backend/network/views.py`, `backend/network/tests.py`, `backend/network/test_security.py`, `backend/network/test_system_integration.py` | **PASS** |

## Academic Objective Traceability

| Chapter 1 objective | Implementation evidence | Status |
|---|---|---|
| Examine existing approaches and identify monitoring/fault-detection challenges | Documented in Chapter 1/3 analysis; the implementation addresses the stated centralized monitoring and structured-history problem | **PASS — academic/documentation objective** |
| Design a centralized web system for registering, managing and monitoring devices | React dashboard + Django REST API + device management and monitoring APIs | **PASS** |
| Implement automated monitoring for availability and selected performance information | Celery worker/Beat + monitoring engine + monitoring records | **PASS** |
| Detect predefined conditions such as unavailability, high latency, packet loss and selected performance problems | Deterministic fault detection rules and validation scenarios | **PASS** |
| Evaluate the developed system | Phases 23–24 integration and controlled monitoring validation, plus this requirements traceability review | **PASS** |

## Evidence Boundaries

### Controlled and simulated validation

The Phase 24 validation suite intentionally uses controlled/simulated ICMP and SNMP outcomes. This is not presented as proof that every physical router, switch or SNMP implementation has been tested.

Chapter 1 explicitly states that the final implementation may use a controlled or simulated network environment when physical device access is limited. It also identifies differences in device capabilities and SNMP configuration as study limitations.

Therefore:

- ICMP functionality is validated at the monitoring-engine and API/integration levels.
- SNMP functionality is validated using controlled service results and error conditions.
- Physical-device interoperability across vendors/models is **not** claimed as completed.

### Scope exclusions

The following are not claimed as implemented requirements because Chapter 1 explicitly places them outside the study scope:

- Physical repair of network devices.
- Automatic router/switch configuration or reconfiguration.
- Network intrusion detection or cybersecurity threat analysis.
- ISP infrastructure monitoring.
- Advanced predictive maintenance.
- Full machine-learning-based network prediction.
- Hardware-level physical-component diagnosis.

## Overall Traceability Result

All 18 requested requirements have an implementation path and corresponding validation evidence within the project. The SNMP requirement is specifically qualified as **controlled/simulated validation**, not unrestricted physical-device interoperability.

The traceability result therefore supports the documented academic scope without extending the claim beyond the evidence available.

## Validation Commands

Backend full regression suite:

```bash
cd backend
python manage.py test
```

Phase 24 controlled monitoring validation:

```bash
python manage.py test network.test_monitoring_validation -v 2
```

Django configuration checks:

```bash
python manage.py check
python manage.py check --deploy
```

Frontend validation:

```bash
cd frontend
npm run lint
npm run build
```

## Source of Academic Requirements

The authoritative requirements for this checklist are Chapter 1 and Chapter 3 of the project documentation. This traceability document should be updated if those academic chapters are formally revised.
