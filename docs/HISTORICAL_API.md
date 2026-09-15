# Historical Monitoring and Fault Analytics API

Phase 21 exposes bounded historical data and database-side aggregation for frontend charts and administrator analysis.

All endpoints require an authenticated administrator token:

```http
Authorization: Token <token>
```

## Monitoring history

### Raw measurements

```http
GET /api/monitoring-history/
```

Supported query parameters:

| Parameter | Description |
|---|---|
| `deviceId` | Filter measurements to one device UUID |
| `from` | Inclusive ISO-8601 start datetime |
| `to` | Inclusive ISO-8601 end datetime |
| `reachable` | Filter by `true` or `false` |
| `limit` | Number of raw records, maximum 500; default 500 |

Example:

```http
GET /api/monitoring-history/?deviceId=<device-uuid>&from=2026-09-15T00:00:00Z&to=2026-09-15T23:59:59Z&limit=100
```

Response:

```json
{
  "records": [
    {
      "id": "<record-uuid>",
      "deviceId": "<device-uuid>",
      "timestamp": "2026-09-15T12:30:00Z",
      "reachable": true,
      "latencyMs": 12.4,
      "packetLossPercent": 0.0,
      "deviceName": "Core Router"
    }
  ],
  "meta": {
    "mode": "raw",
    "count": 1,
    "limit": 100
  }
}
```

Records are returned newest-first.

### Aggregated measurements

Use `aggregation` when a chart needs fewer points or a longer date range:

```http
GET /api/monitoring-history/?deviceId=<device-uuid>&from=<iso>&to=<iso>&aggregation=hour
```

Supported values:

- `minute`
- `hour`
- `day`

Aggregation is performed by the database. Each bucket contains:

```json
{
  "timestamp": "2026-09-15T12:00:00Z",
  "records": 60,
  "reachableRecords": 59,
  "unreachableRecords": 1,
  "availabilityPercent": 98.33,
  "averageLatencyMs": 14.251,
  "averagePacketLossPercent": 1.667
}
```

Aggregated responses are capped at 1,000 buckets.

## Fault history

### Raw fault events

```http
GET /api/fault-history/
```

Supported query parameters:

| Parameter | Description |
|---|---|
| `deviceId` | Filter by device UUID |
| `faultType` | Filter by fault type |
| `severity` | Filter by severity (`critical`, `high`, `medium`, `low`) |
| `status` | Filter by status (`active`, `acknowledged`, `resolved`) |
| `from` | Inclusive detected-at datetime |
| `to` | Inclusive detected-at datetime |
| `limit` | Number of raw faults, maximum 500; default 500 |

Response:

```json
{
  "faults": [
    {
      "id": "<fault-uuid>",
      "deviceId": "<device-uuid>",
      "deviceName": "Core Router",
      "faultType": "HIGH_LATENCY",
      "severity": "high",
      "detectedAt": "2026-09-15T12:30:00Z",
      "status": "active",
      "description": "Latency threshold exceeded",
      "resolvedAt": null
    }
  ],
  "meta": {
    "mode": "raw",
    "count": 1,
    "limit": 500
  }
}
```

### Daily fault aggregation

Use:

```http
GET /api/fault-history/?from=<iso>&to=<iso>&aggregation=day
```

The response is suitable for fault-count and severity/status charts:

```json
{
  "buckets": [
    {
      "timestamp": "2026-09-15T00:00:00Z",
      "faults": 8,
      "status": {
        "active": 2,
        "acknowledged": 1,
        "resolved": 5
      },
      "severity": {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 2
      }
    }
  ],
  "meta": {
    "mode": "aggregated",
    "aggregation": "day",
    "count": 1,
    "limit": 1000
  }
}
```

Fault aggregation currently supports `day` only.

## Query safety and performance

- Raw history responses are limited to 500 records per request.
- Aggregated responses are limited to 1,000 buckets.
- A requested `from`/`to` range cannot exceed 366 days.
- Invalid date ranges and query parameters return `400 Bad Request`.
- Monitoring aggregation uses database-side `Count` and `Avg` operations rather than loading every measurement into Python.
- Monitoring records are indexed by device/time and timestamp.
- Fault records are indexed by device/time, status/time, device/status/time, device/type/time, and severity/time.

These limits keep chart requests bounded while still allowing the frontend to request detailed raw data or lower-cardinality aggregated data.

## Existing device-specific APIs

Phase 21 complements the existing endpoints:

```http
GET /api/devices/<id>/monitoring-snapshot/
GET /api/devices/<id>/monitoring-summary/
GET /api/monitoring-records/?deviceId=<device-uuid>
GET /api/faults/?deviceId=<device-uuid>
```

The historical endpoints are intended for cross-device historical views, date-range analysis, and chart-ready datasets.
