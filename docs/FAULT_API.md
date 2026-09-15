# Fault Management API

Phase 18 exposes generated `FaultEvent` records to the frontend. Fault events are created by the fault-detection engine; the API does not allow clients to create or delete faults.

All fault-management endpoints require an authenticated staff/admin user.

## Base URL

`/api/`

## Fault object

```json
{
  "id": "uuid",
  "deviceId": "uuid",
  "deviceName": "Core Router",
  "faultType": "HIGH_LATENCY",
  "severity": "high",
  "detectedAt": "2026-09-15T06:00:00Z",
  "status": "active",
  "description": "Latency exceeded threshold.",
  "resolvedAt": null
}
```

## List faults

`GET /api/faults/`

Supported query parameters:

- `deviceId=<uuid>` — filter by device
- `severity=critical|high|medium|low`
- `type=<fault type>` or `faultType=<fault type>`
- `status=active|acknowledged|resolved`
- `from=<ISO-8601 timestamp>` — detected at or after this time
- `to=<ISO-8601 timestamp>` — detected at or before this time

Example:

`GET /api/faults/?deviceId=<id>&severity=critical&status=active`

## Active faults

`GET /api/faults/active/`

Returns faults whose status is `active` or `acknowledged`. This is the primary endpoint for an active-fault dashboard view.

## Fault details

`GET /api/faults/<fault-id>/`

Returns one fault object.

## Fault history

`GET /api/fault-history/`

Supports the same filtering dimensions as the fault list:

- `deviceId`
- `severity`
- `type` / `faultType`
- `status`
- `from`
- `to`

The response shape is:

```json
{
  "faults": []
}
```

## Acknowledge

`POST /api/faults/<fault-id>/acknowledge/`

Changes an active fault to `acknowledged`. Resolved faults cannot be acknowledged.

## Resolve

`POST /api/faults/<fault-id>/resolve/`

Marks the fault as resolved and records `resolvedAt`.

## Status update

`PATCH /api/faults/<fault-id>/status/`

Request:

```json
{
  "status": "acknowledged"
}
```

Allowed statuses are `active`, `acknowledged`, and `resolved`. A resolved fault cannot be reactivated through the API. The dedicated acknowledge/resolve actions should be preferred by the frontend when performing those lifecycle operations.

## Protection

The fault list, detail, active-fault, history, acknowledge, resolve, and status endpoints require `IsAdminUser`. Unauthenticated clients receive `401 Unauthorized`.

## Frontend integration

Recommended frontend usage:

- Dashboard: `GET /api/faults/active/`
- Fault list/history: `GET /api/faults/` with filters
- Fault details: `GET /api/faults/<id>/`
- Acknowledge action: `POST /api/faults/<id>/acknowledge/`
- Resolve action: `POST /api/faults/<id>/resolve/`
- General status control: `PATCH /api/faults/<id>/status/`

Fault response field names intentionally use camelCase (`deviceId`, `faultType`, `detectedAt`, `resolvedAt`) to match the existing frontend API contract.
