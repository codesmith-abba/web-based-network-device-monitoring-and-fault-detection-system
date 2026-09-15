# Phase 15 — SNMP Monitoring

The system supports optional SNMP monitoring for devices that expose an SNMP agent. SNMP is an additional monitoring channel and is not required for every device.

## Supported scope

Phase 15 supports:

- SNMPv1
- SNMPv2c
- IPv4/UDP SNMP agents
- Community-string authentication
- UDP port configuration (default `161`)
- Configurable request timeout
- Selected scalar metrics only

SNMPv3 credentials and vendor-specific MIBs are outside the current documented scope.

## Supported metrics

The initial portable metric set is:

| Metric | OID | Purpose |
|---|---|---|
| `sysDescr` | `1.3.6.1.2.1.1.1.0` | Device/system description |
| `sysName` | `1.3.6.1.2.1.1.5.0` | Device/system name |
| `sysUpTime` | `1.3.6.1.2.1.1.3.0` | Agent uptime |
| `ifNumber` | `1.3.6.1.2.1.2.1.0` | Number of network interfaces |

The configured `availableMetrics` list selects which supported metrics are queried. If it is empty, the engine uses the default supported metric set.

Unsupported or unavailable vendor-specific metrics are not required for successful monitoring.

## Configuration

SNMP settings are stored in the device's `MonitoringConfiguration`:

- `snmp_enabled`
- `snmp_version`
- `snmp_community`
- `snmp_port`
- `snmp_timeout_seconds`
- `available_metrics`

The API does not return `snmpCommunity` in read responses because it is a credential. It can be supplied when creating or updating SNMP configuration.

Example:

```http
PATCH /api/devices/<id>/snmp/
Content-Type: application/json
```

```json
{
  "snmpEnabled": true,
  "snmpVersion": "2c",
  "snmpCommunity": "public",
  "snmpPort": 161,
  "snmpTimeoutSeconds": 2,
  "availableMetrics": ["sysName", "sysUpTime"]
}
```

## API

### Inspect SNMP configuration and recent results

```http
GET /api/devices/<id>/snmp/
```

Returns the sanitized configuration, supported metrics, and recent stored SNMP metrics.

### Poll SNMP

```http
POST /api/devices/<id>/snmp/
```

The poll operation queries each selected metric independently. This is intentional: if a device exposes only some metrics, successful values are stored while unsupported metrics are reported as individual errors.

Example successful response:

```json
{
  "status": "success",
  "metrics": [
    {
      "metricName": "sysName",
      "oid": "1.3.6.1.2.1.1.5.0",
      "value": "edge-router",
      "valueType": "OctetString"
    }
  ],
  "errors": []
}
```

Possible result statuses:

- `success` — all selected metrics returned values.
- `partial` — some selected metrics succeeded and some failed.
- `error` — no selected metric could be collected.
- `disabled` — SNMP is disabled for the device.
- `configuration_error` — SNMP is enabled but the configuration is invalid.

SNMP failures return a normal API result and do not crash the web application.

### Monitoring snapshot

```http
GET /api/devices/<id>/monitoring-snapshot/
```

The snapshot now includes recent `snmpMetrics` alongside the ICMP monitoring history.

## Failure handling

The SNMP engine treats the following as isolated monitoring outcomes:

- Device does not support SNMP.
- SNMP agent is disabled.
- Community string is missing or rejected.
- SNMP request times out.
- Agent rejects an OID.
- Device exposes only a subset of the requested metrics.
- Network/transport errors occur.
- A metric is outside the supported metric set.

Successful metrics are persisted even when other selected metrics fail.

## Persistence

Successful values are stored in `SNMPMetric` with:

- device
- timestamp
- metric name
- returned OID
- value
- SNMP value type

This allows SNMP history to remain independent from ICMP reachability records.

## Testing

Physical network devices are not required for automated tests. The test suite mocks the SNMP polling boundary and covers:

- successful metric collection and persistence
- partial metric availability
- disabled SNMP
- missing credentials
- agent/credential/timeout-style failures
- API configuration and result exposure
- administrator access control

## Architecture

SNMP protocol logic lives under:

```text
backend/network/snmp/
├── __init__.py
└── services.py
```

API views call the service layer and do not contain PySNMP protocol logic. The service isolates expected SNMP failures and returns structured monitoring outcomes.

The SNMP engine currently uses PySNMP's asynchronous high-level API internally while exposing a synchronous domain-service boundary to Django. This keeps the existing REST application architecture simple while allowing SNMP transport operations to remain bounded and isolated.
