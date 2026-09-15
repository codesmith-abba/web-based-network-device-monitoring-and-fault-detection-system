# Web-Based Network Device Monitoring and Fault Detection System

A web-based network monitoring platform for continuously monitoring network devices, detecting faults, tracking network health, and providing administrators with real-time visibility into infrastructure status.

## System Architecture

```text
Web Dashboard (React / TypeScript)
              │
           REST API
              │
Django + Django REST Framework
              │
      Application/API boundary
   ┌──────────┼───────────┐
 Devices   Monitoring   Faults
                          │
                    Alerts/Notifications
              │
       Domain service modules
              │
 SQLite (development database)
              │
 Celery ───── Redis (background processing foundation)
```

The backend uses one Django `network` application with explicit domain modules. This preserves the established frontend API contract while separating business operations from HTTP handling.

## Backend Structure

```text
backend/
├── backend/
│   ├── settings.py          # environment, DRF, CORS, SQLite, Celery
│   ├── urls.py              # project-level HTTP routing
│   └── celery.py            # Celery application
└── network/
    ├── api/                 # health endpoint
    ├── alerts/              # notification services
    ├── devices/             # device-domain services
    ├── faults/              # fault detection and lifecycle services
    ├── monitoring/          # ICMP monitoring engine
    ├── snmp/                # SNMP monitoring services
    ├── migrations/
    ├── historical_api.py    # historical monitoring/fault analytics APIs
    ├── models.py            # persistence models
    ├── serializers.py       # REST representation boundary
    ├── tasks.py             # Celery monitoring tasks
    ├── views.py             # REST controllers/viewsets
    └── urls.py              # API routing
```

## Authentication

Protected API endpoints use Django REST Framework token authentication:

```http
Authorization: Token <token>
```

Device management, monitoring, historical analytics, fault management, and notifications require an authenticated staff user (`is_staff=True`).

Authentication endpoints:

```text
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/me/
```

Unauthenticated protected requests return `401 Unauthorized`. Authenticated non-administrators return `403 Forbidden`.

The health endpoint is intentionally public:

```text
GET /api/health/
```

## Device Management

```text
GET    /api/devices/
POST   /api/devices/
GET    /api/devices/<id>/
PATCH  /api/devices/<id>/
PUT    /api/devices/<id>/
DELETE /api/devices/<id>/
PATCH  /api/devices/<id>/monitoring/
GET    /api/devices/<id>/monitoring-config/
PATCH  /api/devices/<id>/monitoring-config/
```

Supported device types:

* `router`
* `switch`
* `server`
* `access-point`
* `firewall`
* `other`

Devices use UUID identifiers and IPv4 addresses. Device registration automatically creates the associated `MonitoringConfiguration`.

## Monitoring

The ICMP monitoring engine validates IPv4 addresses, executes a bounded ping without a shell, stores the measurement, updates device status, and evaluates threshold faults.

Run one immediate check:

```text
POST /api/devices/<id>/monitor/
```

Monitoring records contain:

* timestamp
* device
* reachability
* latency in milliseconds
* packet loss percentage

Monitoring history is immutable: each execution creates a new record.

### Monitoring APIs

```text
GET /api/monitoring-records/
GET /api/monitoring-records/?deviceId=<id>
GET /api/devices/<id>/monitoring-snapshot/
GET /api/devices/<id>/monitoring-summary/
GET /api/monitoring-history/
```

See [`docs/API.md`](docs/API.md) for the established monitoring contract and [`docs/HISTORICAL_API.md`](docs/HISTORICAL_API.md) for historical analytics.

## Automated Monitoring

Celery and Redis provide asynchronous monitoring execution.

The system uses:

* `monitor_device_task` — monitors one device asynchronously.
* `dispatch_due_monitoring_tasks` — finds enabled devices whose configured interval has elapsed.
* Redis distributed locks — prevent overlapping monitoring runs for the same device.
* Celery Beat — dispatches due monitoring checks every five seconds.

Enabling monitoring through the API immediately queues the first asynchronous monitoring task.

Typical local services:

```bash
redis-server
celery -A backend worker -l info
celery -A backend beat -l info
python manage.py runserver
```

## Fault Detection

The monitoring engine evaluates each monitoring record against deterministic thresholds for:

* device unreachable
* high latency
* high packet loss

SNMP metrics can additionally produce:

* high CPU usage
* high memory usage

Active and acknowledged faults are unique per device/fault type. Recovery automatically resolves the corresponding monitoring fault condition.

Fault lifecycle:

```text
active → acknowledged → resolved
active → resolved
```

Fault APIs:

```text
GET    /api/faults/
POST   /api/faults/
GET    /api/faults/<id>/
GET    /api/faults/active/
POST   /api/faults/<id>/acknowledge/
POST   /api/faults/<id>/resolve/
PATCH  /api/faults/<id>/status/
```

High and critical faults can create an unread notification record.

## Historical Monitoring and Analytics — Phase 21

Historical APIs are bounded and database-oriented so large monitoring histories are not unnecessarily loaded into application memory.

### Monitoring history

```text
GET /api/monitoring-history/
```

Supported filters:

```text
?deviceId=<uuid>
?from=<iso-datetime>
?to=<iso-datetime>
?reachable=true|false
?limit=<1-500>
```

Database-side aggregation:

```text
?aggregation=minute
?aggregation=hour
?aggregation=day
```

Aggregated results provide record count, availability, average latency, and average packet loss.

### Fault history

```text
GET /api/fault-history/
```

Supported filters:

```text
?deviceId=<uuid>
?faultType=<type>
?severity=<severity>
?status=<status>
?from=<iso-datetime>
?to=<iso-datetime>
?limit=<1-500>
```

Daily aggregation is available with:

```text
?aggregation=day
```

Historical queries enforce bounded date ranges and response sizes. Monitoring and fault tables have indexes supporting device/time, status/time, severity/time, and fault-type/time queries.

Full response documentation is available in [`docs/HISTORICAL_API.md`](docs/HISTORICAL_API.md).

## SNMP

The backend supports SNMPv1 and SNMPv2c through PySNMP.

Current supported metrics include:

* `sysDescr`
* `sysName`
* `sysUpTime`
* `ifNumber`

SNMP failures are isolated from ICMP monitoring and are returned as monitoring outcomes rather than unhandled application exceptions.

## Notifications

```text
GET  /api/notifications/
GET  /api/notifications/<id>/
POST /api/notifications/<id>/read/
```

Notification records are linked one-to-one with faults and can be filtered by device, severity, and notification status.

## Security and Deployment Configuration

The backend defaults to `DEBUG=False` and keeps development HTTP compatibility while exposing environment variables for production HTTPS hardening.

Important environment variables:

* `DJANGO_SECRET_KEY`
* `DJANGO_DEBUG`
* `DJANGO_ALLOWED_HOSTS`
* `DJANGO_TIME_ZONE`
* `SQLITE_DB_PATH`
* `CORS_ALLOWED_ORIGINS`
* `CSRF_TRUSTED_ORIGINS`
* `DJANGO_SECURE_SSL_REDIRECT`
* `DJANGO_SESSION_COOKIE_SECURE`
* `DJANGO_CSRF_COOKIE_SECURE`
* `DJANGO_SECURE_HSTS_SECONDS`
* `CELERY_BROKER_URL`
* `CELERY_RESULT_BACKEND`

The development secret fallback is not suitable for deployment; production configuration must provide a real `DJANGO_SECRET_KEY`.

## Validation

From `backend/`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py test
```

For a clean database validation:

```bash
rm -f db.sqlite3
python manage.py migrate --noinput
python manage.py test
```

The GitHub Actions backend workflow performs Django checks, verifies migrations, creates a clean SQLite database, applies all migrations, and runs the complete test suite.

## Phase 22 — Backend Completion and Hardening

Phase 22 audits and hardens the backend for complete frontend integration.

Completed areas:

* model relationships, constraints, indexes, and cascading behavior audited
* serializers aligned with the frontend API contract
* duplicate legacy history/monitoring controllers removed
* monitoring snapshot/summary/SNMP APIs return proper `404` and validation responses
* token authentication and administrator-only API access tested
* ICMP monitoring workflow tested from API request through persistence and fault evaluation
* fault creation, notification, acknowledgement, recovery, and resolution tested
* Celery monitoring task and Redis lock behavior tested
* API validation/error handling tested
* secure Django defaults strengthened
* clean-database migration validation added to CI
* unused monitoring export removed
* backend documentation updated

## Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* Celery
* Redis

### Network Monitoring

* ICMP / Ping
* SNMP
* PySNMP

### Frontend

* React
* TypeScript
* Tailwind CSS
* Recharts

### Database

* SQLite for development
* PostgreSQL planned for production

### Infrastructure

* Linux
* Nginx
* Gunicorn / ASGI
* Git & GitHub

## Academic Project

This system demonstrates the application of:

* Computer networking
* Network management
* Web application development
* Database systems
* Distributed/background processing
* Fault detection
* Network performance monitoring

## Author

**Abdulmumin Abubakar**

AI Engineer | Software Engineer | Founder, Echowavs
