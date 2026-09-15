# Backend API — Device Management and Monitoring

## Authentication

All device-management and monitoring endpoints require a Django REST Framework token belonging to an active administrator (`is_staff=True`).

```http
Authorization: Token <token>
```

Non-authenticated requests receive `401 Unauthorized`. Authenticated non-administrators receive `403 Forbidden`.

## Device resource

### Fields

| API field | Backend field | Notes |
|---|---|---|
| `id` | `id` | UUID, read-only |
| `name` | `name` | Required, trimmed, max 120 characters |
| `ipAddress` | `ip_address` | Required IPv4 address |
| `type` | `device_type` | Required device type choice |
| `status` | `status` | Server-controlled monitoring state |
| `monitoring` | `monitoring_enabled` | Enables/disables monitoring |
| `createdAt` | `created_at` | Read-only timestamp |
| `updatedAt` | `updated_at` | Read-only timestamp |

Supported device types:

- `router`
- `switch`
- `server`
- `access-point`
- `firewall`
- `other`

Supported status values:

- `online`
- `offline`
- `unknown`

Status is read-only from the device-management API and is updated by the monitoring engine.

## Device endpoints

### List devices

```http
GET /api/devices/
```

### Register a device

```http
POST /api/devices/
Content-Type: application/json
```

Example:

```json
{
  "name": "Core Router",
  "ipAddress": "192.168.1.1",
  "type": "router",
  "monitoring": true
}
```

A successful registration returns `201 Created` and automatically creates the device's one-to-one `MonitoringConfiguration` record with the default monitoring settings.

### Retrieve a device

```http
GET /api/devices/<id>/
```

### Update a device

```http
PATCH /api/devices/<id>/
PUT /api/devices/<id>/
```

The API validates the IPv4 address and device type on every write.

### Delete a device

```http
DELETE /api/devices/<id>/
```

Returns `204 No Content` on success. Device deletion cascades to its monitoring configuration, monitoring records, SNMP metrics, and fault records according to the persistence model. This behavior should therefore be treated as destructive.

### Update monitoring state

```http
PATCH /api/devices/<id>/monitoring/
```

Example:

```json
{
  "monitoring": false
}
```

The monitoring configuration association is preserved when monitoring is disabled.

## MonitoringRecord

Each monitoring execution creates a new immutable historical `MonitoringRecord`. Existing records are never updated or replaced by later measurements.

The record contains:

| Field | Description |
|---|---|
| `id` | UUID identifier |
| `deviceId` | Device associated with the measurement |
| `timestamp` | Time the measurement was recorded |
| `reachable` | Whether the device responded to ICMP |
| `latencyMs` | Measured response latency, when available |
| `packetLossPercent` | Packet-loss result, when available |

The database indexes records by device/time, timestamp, and device/reachability/time to support latest-result, history, and status-oriented queries efficiently.

## ICMP monitoring

The monitoring engine performs one bounded IPv4 ICMP echo request per monitoring execution. Ping execution is isolated from API views and uses `subprocess.run` without a shell. Timeouts, missing system ping utilities, and network errors are converted into an unreachable monitoring result rather than being allowed to crash the web application.

### Run an ICMP check

```http
POST /api/devices/<id>/monitor/
```

The endpoint executes one ICMP check, stores a new `MonitoringRecord`, updates the device status to `online` or `offline`, and returns the stored result.

Successful response example:

```json
{
  "id": "<record-uuid>",
  "deviceId": "<device-uuid>",
  "timestamp": "2026-09-15T06:30:00Z",
  "reachable": true,
  "latencyMs": 4.32,
  "packetLossPercent": 0.0
}
```

For an unreachable device, the result is persisted with `reachable: false`, no latency, and packet loss of `100.0` when the failed ICMP operation provides that measurement. Supported ping output is parsed for latency; packet loss is represented as the result of the ICMP execution.

Invalid monitoring configuration, disabled monitoring, and unsupported addresses return `400 Bad Request` without creating a monitoring record.

## Monitoring APIs

### List monitoring records

```http
GET /api/monitoring-records/
```

Filter by device:

```http
GET /api/monitoring-records/?deviceId=<device-uuid>
```

The endpoint returns records in newest-first order. Historical records remain available after subsequent monitoring executions.

### Get device monitoring snapshot

```http
GET /api/devices/<id>/monitoring-snapshot/
```

Returns the device, latest monitoring record, recent historical records, SNMP metrics, and associated monitoring configuration.

### Get device monitoring summary

```http
GET /api/devices/<id>/monitoring-summary/
```

Returns aggregated monitoring health without changing historical data:

```json
{
  "deviceId": "<device-uuid>",
  "deviceName": "Core Router",
  "status": "online",
  "monitoringEnabled": true,
  "totalRecords": 120,
  "reachableRecords": 116,
  "unreachableRecords": 4,
  "availabilityPercent": 96.67,
  "averageLatencyMs": 12.45,
  "averagePacketLossPercent": 3.33,
  "lastCheckedAt": "2026-09-15T06:30:00Z",
  "latest": {}
}
```

If no monitoring records exist, aggregate values that cannot be calculated are returned as `null`.

### Monitoring history

```http
GET /api/monitoring-history/
GET /api/monitoring-history/?deviceId=<device-uuid>
GET /api/monitoring-history/?from=<iso-datetime>&to=<iso-datetime>
```

The history endpoint supports device and time-range filtering and returns up to 500 records per request.

## ICMP engine behavior

- IPv4 addresses are validated before ping execution.
- One bounded ICMP request is sent per monitoring execution.
- The default ping timeout is 2 seconds.
- No shell is invoked for the ping command.
- Successful responses record reachability and parsed latency in milliseconds.
- Failed requests record unreachable status and packet loss when the execution can determine it.
- The device status is synchronized with the latest monitoring result.
- Monitoring configuration requires an interval of at least 5 seconds.
- Monitoring failures do not propagate as unhandled exceptions from the API.

## Validation

Invalid IPv4 addresses and unsupported device types return `400 Bad Request` with field-level serializer errors.

IPv6 addresses are rejected because the documented device model currently uses IPv4 addressing.

## Migration

Phase 16 adds migration `0006_monitoringrecord_indexes.py`, which strengthens indexes for monitoring-record retrieval and aggregation without modifying or deleting existing monitoring data.
