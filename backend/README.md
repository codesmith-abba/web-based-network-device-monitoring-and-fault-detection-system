# Network Monitoring Backend

Django REST backend for the Web-Based Network Device Monitoring and Fault Detection System.

## Responsibilities

The backend owns:

- administrator authentication and authorization
- device registration and validation
- monitoring configuration
- ICMP monitoring
- SNMP v1/v2c metric collection
- monitoring persistence
- deterministic fault detection
- fault lifecycle management
- in-application notifications
- historical monitoring/fault APIs
- Celery background monitoring
- Redis locking and task coordination

## Stack

- Python
- Django
- Django REST Framework
- Celery
- Redis
- SQLite
- PySNMP

## Structure

```text
backend/
├── backend/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── network/
│   ├── api/
│   ├── alerts/
│   ├── devices/
│   ├── faults/
│   ├── monitoring/
│   ├── snmp/
│   ├── migrations/
│   ├── historical_api.py
│   ├── models.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── views.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure a real `DJANGO_SECRET_KEY` for any deployment with `DEBUG=False`. Never commit the real environment file.

Initialize the database:

```bash
python manage.py migrate --noinput
python manage.py createsuperuser
```

Run Django:

```bash
python manage.py runserver
```

## Redis and Celery

Start Redis:

```bash
redis-server
```

Worker:

```bash
celery -A backend worker -l info
```

Scheduler:

```bash
celery -A backend beat -l info
```

Celery Beat dispatches due monitoring every five seconds. Each device's configured interval controls whether a new monitoring execution is due. Redis locks prevent overlapping monitoring jobs for one device.

## Database

The finalized project uses SQLite as its documented deployment database.

The main Django models are:

- `Device`
- `MonitoringConfiguration`
- `MonitoringRecord`
- `SNMPMetric`
- `FaultEvent`
- `Notification`

See [`../docs/DATABASE.md`](../docs/DATABASE.md) for the finalized model/relationship reference.

## Authentication

Django REST Framework token authentication is used:

```http
Authorization: Token <token>
```

Protected application APIs require an authenticated staff administrator. Login, logout, and current-user endpoints are available under `/api/auth/`.

## Monitoring

A new `Device` automatically receives a one-to-one `MonitoringConfiguration`.

ICMP monitoring records:

- reachability
- latency
- packet loss
- timestamp

SNMP configuration supports SNMPv1/v2c and the currently implemented selected metrics. SNMP failures are isolated from ICMP monitoring.

## Fault Detection

The monitoring engine evaluates deterministic thresholds for reachability, latency, packet loss, and supported SNMP CPU/memory metrics.

Faults are persisted as `FaultEvent` records and can be acknowledged or resolved. Recovery monitoring can automatically resolve applicable active/acknowledged monitoring faults.

Fault creation is server-controlled; clients do not create arbitrary fault events.

## API Documentation

- [`../docs/API.md`](../docs/API.md) — device and monitoring API
- [`../docs/FAULT_API.md`](../docs/FAULT_API.md) — fault lifecycle API
- [`../docs/HISTORICAL_API.md`](../docs/HISTORICAL_API.md) — historical APIs
- [`../docs/NOTIFICATIONS.md`](../docs/NOTIFICATIONS.md) — notification API
- [`../docs/AUTOMATED_MONITORING.md`](../docs/AUTOMATED_MONITORING.md) — Celery/Redis monitoring

## Testing

Full backend suite:

```bash
python manage.py test
```

Configuration:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

Deployment configuration:

```bash
python manage.py check --deploy
```

Controlled monitoring validation:

```bash
python manage.py test network.test_monitoring_validation -v 2
```

The monitoring validation suite uses controlled/simulated network outcomes where physical devices are unavailable. It does not claim universal physical-device interoperability.

## Production

The current production path is:

```text
Nginx → Gunicorn → Django WSGI → SQLite
                         └→ Celery → Redis
```

See [`../deploy/README.md`](../deploy/README.md) for Linux deployment, systemd services, Nginx, HTTPS, environment variables, backups, and smoke tests.
