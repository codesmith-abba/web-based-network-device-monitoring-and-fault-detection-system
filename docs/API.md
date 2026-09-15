# Backend API — Device Management

## Authentication

All device-management endpoints require a Django REST Framework token belonging to an active administrator (`is_staff=True`).

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

Status is read-only from the device-management API and is intended to be updated by the monitoring engine.

## Endpoints

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

Both partial and full updates are supported:

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

### Get monitoring snapshot

```http
GET /api/devices/<id>/monitoring-snapshot/
```

Returns the device, latest monitoring record, recent history, SNMP metrics placeholder, and the associated monitoring configuration.

## Validation

Invalid IPv4 addresses and unsupported device types return `400 Bad Request` with field-level serializer errors.

IPv6 addresses are rejected because the documented device model currently uses IPv4 addressing.

## Migration

Phase 13 introduces migration `0002_rename_type_device_device_type.py`, preserving existing device data while aligning the database field name with the documented `device_type` requirement. The API continues exposing `type` to preserve the existing frontend contract.
