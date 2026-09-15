# Backend Notifications

Phase 20 provides basic in-app notifications for selected detected faults.

## Notification policy

Notifications are created for:

- `critical` faults
- `high` faults

Medium and low faults do not create notifications by default.

The notification is created when fault detection creates or updates a selected active fault. The notification is idempotent: repeated monitoring of the same active fault does not create duplicate notifications.

## Notification data

Each notification is associated with:

- the detected fault
- the fault's device
- fault severity
- fault type
- fault detection timestamp
- notification creation timestamp
- read/unread state
- fault description

The `Notification` model uses a one-to-one relationship with `FaultEvent`, so one active fault has at most one basic notification record.

## API

All notification endpoints require an administrator authentication token.

### List notifications

```text
GET /api/notifications/
```

Optional filters:

```text
GET /api/notifications/?status=unread
GET /api/notifications/?deviceId=<device-id>
GET /api/notifications/?severity=critical
```

### Get one notification

```text
GET /api/notifications/<id>/
```

### Mark a notification as read

```text
POST /api/notifications/<id>/read/
```

No external email, SMS, or push provider is used in this phase.

## Response shape

```json
{
  "id": "notification-id",
  "faultId": "fault-id",
  "deviceId": "device-id",
  "deviceName": "Core Router",
  "faultType": "DEVICE_UNREACHABLE",
  "severity": "critical",
  "detectedAt": "2026-09-15T08:00:00Z",
  "createdAt": "2026-09-15T08:00:01Z",
  "status": "unread",
  "description": "Device is unreachable by ICMP monitoring."
}
```
