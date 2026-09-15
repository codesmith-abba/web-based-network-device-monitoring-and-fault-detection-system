# Backend API — Device Management and ICMP Monitoring

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

Returns `204 No Content` on success. Device deletion cascades to its monitoring configuration, monitoring records, and fault records according to the persistence model. This behavior should therefore be treated as destructive.

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

## ICMP monitoring

The monitoring engine performs one bounded IPv4 ICMP echo request per monitoring execution. Ping execution is isolated from API views and uses `subprocess.run` without a shell. Timeouts, missing system ping utilities, and network errors are converted into an unreachable monitoring result rather than being allowed to crash the web application.

### Run an ICMP check

```http
POST /api/devices/<id>/monitor/
```

The endpoint executes one ICMP check, stores a `MonitoringRecord`, updates the device status to `online` or `offline`, and returns the stored result.

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

For a timeout or unreachable device, the result is persisted with `reachable: false`, `latencyMs: null`, and `packetLossPercent: 100.0`. The endpoint still returns `200 OK` because the monitoring operation itself completed successfully and the device's unreachable state is the monitoring result.

Invalid monitoring configuration, disabled monitoring, and unsupported addresses return `400 Bad Request` without creating a monitoring record.

### List monitoring records

```http
GET /api/monitoring-records/
```

Filter by device:

```http
GET /api/monitoring-records/?deviceId=<device-uuid>
```

### Get device monitoring snapshot

```http
GET /api/devices/<id>/monitoring-snapshot/
```

Returns the device, latest monitoring record, recent history, SNMP metrics placeholder, and associated monitoring configuration.

### Monitoring history

```http
GET /api/monitoring-history/
GET /api/monitoring-history/?deviceId=<device-uuid>
GET /api/monitoring-history/?from=<iso-datetime>&to=<iso-datetime>
```

## ICMP engine behavior

- IPv4 addresses are validated before ping execution.
- One ICMP request is sent per monitoring execution.
- The default ping timeout is 2 seconds.
- No shell is invoked for the ping command.
- Successful responses record reachability and parsed latency in milliseconds.
- Timeouts and network failures record the device as unreachable.
- The device status is synchronized with the latest result.
- Monitoring configuration requires an interval of at least 5 seconds.
- Monitoring failures do not propagate as unhandled exceptions from the API.

## Validation

Invalid IPv4 addresses and unsupported device types return `400 Bad Request` with field-level serializer errors.

IPv6 addresses are rejected because the documented device model currently uses IPv4 addressing.

## Migration

Phase 13 uses migration `0003_rename_type_device_device_type.py` after the existing `0002_rename_network_fau_device__f6c5a5_idx_network_fau_device__b8227f_idx_and_more.py`, avoiding a migration graph conflict while preserving existing device data. The API continues exposing `type` to preserve the existing frontend contract.
