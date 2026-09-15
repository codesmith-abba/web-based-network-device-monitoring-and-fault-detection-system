# Automated Background Monitoring

Phase 19 moves periodic device monitoring out of HTTP requests and into Celery workers using Redis as the broker.

## Architecture

```text
Celery Beat
    |
    | every 5 seconds
    v
Dispatch due monitoring tasks
    |
    | checks each device's MonitoringConfiguration.interval_seconds
    v
Celery Worker
    |
    +--> ICMP monitoring
    |      +--> MonitoringRecord
    |      +--> device status
    |      +--> fault evaluation
    |
    +--> SNMP monitoring when enabled
           +--> SNMPMetric
           +--> fault evaluation
```

The scheduler runs frequently so each device can keep its own configured interval. It does not create a separate beat schedule for every device.

## Redis configuration

The backend uses Redis as the Celery broker and result backend by default:

```text
redis://127.0.0.1:6379/0
```

Override it with environment variables when Redis runs elsewhere:

```bash
export CELERY_BROKER_URL=redis://127.0.0.1:6379/0
export CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

Redis is also used for the distributed per-device monitoring lock, which prevents overlapping monitoring runs across workers.

## Run locally

Open four terminals from `backend/`.

### 1. Django

```bash
python manage.py runserver
```

### 2. Redis

With Redis installed locally:

```bash
redis-server
```

Verify it is available:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

### 3. Celery worker

```bash
celery -A backend worker --loglevel=INFO
```

### 4. Celery scheduler

```bash
celery -A backend beat --loglevel=INFO
```

The scheduler dispatches `network.tasks.dispatch_due_monitoring_tasks` every 5 seconds.

## Device scheduling

Each device has a `MonitoringConfiguration` with `interval_seconds`.

The dispatcher considers a device due when:

- monitoring is enabled;
- no monitoring record exists yet; or
- the latest monitoring record is at least `interval_seconds` old.

The minimum interval enforced by the monitoring service is 5 seconds.

## Task failure behavior

- One device failure does not stop the dispatcher.
- ICMP failures are logged and returned as a partial task result.
- SNMP failures are isolated from ICMP results.
- Unsupported or invalid SNMP configuration is reported without crashing the worker.
- Unknown/deleted devices are skipped safely.
- Per-device Redis locks prevent concurrent monitoring runs for the same device.
- Monitoring records and fault evaluation continue to use the existing Phase 14/15/17 services.

## Testing

Run the complete backend suite:

```bash
python manage.py test
```

Run only automated monitoring tests:

```bash
python manage.py test network.test_tasks
```

The task tests mock Redis and network operations, so a live Redis server is not required for the unit test suite.
