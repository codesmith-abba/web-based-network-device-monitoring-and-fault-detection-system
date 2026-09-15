# Phase 24 — Network Monitoring Validation

## Objective

Validate the monitoring subsystem against controlled network conditions and document expected versus observed behavior.

This phase uses **controlled/simulated conditions** in automated tests. The test suite mocks ICMP and SNMP outcomes so validation is deterministic and does not require a physical router, switch, server, or SNMP agent.

> **Evidence boundary:** Passing these tests demonstrates application behavior under the simulated conditions. It does **not** prove that physical network-device or SNMP-agent communication was successfully tested.

## Validation Environment

- Backend: Django + Django REST Framework
- Monitoring engine: ICMP monitoring service
- SNMP: SNMPv1/v2c service
- Queue: Celery
- Broker/lock: Redis
- API: Django REST API
- Test module: `backend/network/test_monitoring_validation.py`
- Simulated device address: `192.0.2.20` (documentation/test address)

## Test Matrix

| # | Scenario | Controlled condition | Expected result | Automated evidence | Result |
|---|---|---|---|---|---|
| 1 | Reachable device | ICMP reachable, 20 ms, 0% loss | Record is reachable; device becomes online; no fault | `test_01_reachable_device` | PASS when test passes |
| 2 | Unreachable device | ICMP unreachable, 100% loss | Offline device; `DEVICE_UNREACHABLE` fault; notification | `test_02_unreachable_device_creates_fault_and_notification` | PASS when test passes |
| 3 | High latency | ICMP reachable, 650 ms | `HIGH_LATENCY` high-severity fault | `test_03_high_latency_creates_fault` | PASS when test passes |
| 4 | Packet loss | ICMP reachable, 60% loss | `HIGH_PACKET_LOSS` high-severity fault | `test_04_packet_loss_creates_fault` | PASS when test passes |
| 5 | SNMP-supported device | Mocked successful SNMPv2c responses | Metrics are collected and persisted as `SNMPMetric` records | `test_05_snmp_supported_device_persists_metrics` | PASS when test passes |
| 6 | SNMP-unavailable device | Mocked SNMP timeout | SNMP failure is isolated and returned as an error; no invalid metric is stored | `test_06_snmp_unavailable_device_is_isolated` | PASS when test passes |
| 7 | Repeated monitoring failures | Two consecutive unreachable results | Monitoring records accumulate, but only one active fault remains for the same device/type | `test_07_repeated_monitoring_failure_persists_single_active_fault` | PASS when test passes |
| 8 | Fault persistence | Consecutive high-latency results | Existing active fault remains active; no duplicate active fault | `test_08_fault_persists_until_condition_recovers` | PASS when test passes |
| 9 | Fault resolution | High latency followed by 20 ms healthy result | Existing fault becomes resolved and receives `resolved_at` | `test_09_fault_resolves_after_healthy_measurement` | PASS when test passes |
| 10 | Historical records | Healthy and faulty monitoring runs | Monitoring and fault history APIs expose the generated records | `test_10_historical_records_are_exposed` | PASS when test passes |
| 11 | Dashboard visibility | High-latency monitoring result | Dashboard exposes device count, active fault count, and latest latency | `test_11_dashboard_exposes_monitoring_fault_and_health_state` | PASS when test passes |
| 12 | Repeated worker execution with SNMP failure | Successful ICMP + failed SNMP in Celery task | Task completes as partial; ICMP result remains available and SNMP error is isolated | `test_12_celery_task_handles_unavailable_snmp_as_partial_result` | PASS when test passes |

## Run the Validation

From the backend directory:

```bash
python manage.py test network.test_monitoring_validation -v 2
```

Then run the complete backend suite:

```bash
python manage.py test
```

Expected successful validation is a zero exit status with all tests passing.

## Evidence to Record

For the project report/demo, retain:

1. Terminal output showing `network.test_monitoring_validation` passing.
2. Terminal output showing the complete backend test suite passing.
3. Screenshots or API responses for dashboard, monitoring history, fault history, and notifications if a manual UI demonstration is performed.
4. If physical-device validation is later performed, record the device type, test condition, timestamp, measured result, and supporting screenshot/log separately from these simulated tests.

## Physical Device Testing

Physical testing is optional for this automated validation phase and must be reported separately if performed.

Do not describe a simulated `PingResult` or mocked SNMP response as a real network-device test. A real-device result requires an actual reachable/unreachable device or SNMP agent and evidence from the running environment.

## Acceptance Criteria

Phase 24 is considered technically validated when:

- Reachability and failure states are persisted correctly.
- High latency and packet loss produce the documented faults.
- Repeated failures do not create duplicate active faults for the same device/fault type.
- Faults remain active while the condition persists.
- Healthy measurements resolve applicable active faults.
- SNMP success persists metrics.
- SNMP failure does not crash the monitoring task or corrupt ICMP results.
- Historical APIs expose monitoring/fault evidence.
- Dashboard APIs expose the current monitoring/fault state.
- The dedicated Phase 24 test suite passes.
- The complete backend test suite remains green.

## Scope Limitation

This phase validates the software's response to controlled monitoring inputs. It does not certify ICMP behavior across operating systems, network topologies, firewalls, NAT, routers, switches, or vendor-specific SNMP implementations. Those require environment-specific integration tests with real equipment or dedicated network simulation infrastructure.
