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
              │
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

The backend uses one Django `network` application with explicit domain modules. This preserves the working Phase 9 API contract and persistence models while separating business operations from HTTP handling.

```text
backend/
├── backend/
│   ├── settings.py          # environment, DRF, CORS, SQLite, Celery
│   ├── urls.py              # project-level HTTP routing
│   └── celery.py            # Celery application
└── network/
    ├── api/                 # API boundary and health endpoint
    ├── devices/             # device-domain services
    ├── monitoring/          # monitoring-domain services
    ├── faults/              # fault-domain services
    ├── alerts/              # notification-domain services
    ├── migrations/
    ├── models.py            # current shared persistence models
    ├── serializers.py       # REST representation boundary
    ├── views.py             # REST controllers/viewsets
    ├── urls.py
    ├── signals.py
    └── tests.py
```

This is an incremental architecture. A future phase can split domains into independent Django apps if the implementation grows enough to justify that change.

## Phase 11 — Django Backend Foundation

Phase 11 establishes the backend foundation required by the documented three-tier architecture.

### REST API

Django REST Framework is configured with token authentication and authenticated-by-default API permissions. The existing Phase 9 endpoints remain the canonical frontend contract.

### Health Check

```text
GET /api/health/
```

A successful response confirms both application availability and SQLite connectivity:

```json
{
  "status": "ok",
  "database": "ok"
}
```

### CORS

Development CORS origins default to:

```text
http://localhost:5173
http://127.0.0.1:5173
```

They can be overridden with `CORS_ALLOWED_ORIGINS`.

### Environment Configuration

Backend configuration is environment-driven. `backend/.env.example` documents the supported variables. Provide a real `DJANGO_SECRET_KEY` outside development and keep local secret files uncommitted.

Important settings include:

* `DJANGO_SECRET_KEY`
* `DJANGO_DEBUG`
* `DJANGO_ALLOWED_HOSTS`
* `DJANGO_TIME_ZONE`
* `SQLITE_DB_PATH`
* `CORS_ALLOWED_ORIGINS`
* `CSRF_TRUSTED_ORIGINS`
* `CELERY_BROKER_URL`
* `CELERY_RESULT_BACKEND`

### SQLite

SQLite remains the documented development database. The default database is `backend/db.sqlite3`; `SQLITE_DB_PATH` can override the location without changing application code.

PostgreSQL remains a future production database option.

### Celery and Redis

Celery and Redis are established as the background-processing foundation. The Celery application is configured through Django settings and uses Redis as its default broker/backend.

This phase does **not** claim that live ICMP/SNMP monitoring workers are already running. Actual periodic monitoring, network probing, fault detection, and retry scheduling belong to the monitoring-worker implementation phase.

## Device Management Backend — Phase 13

Phase 13 implements the backend device-management lifecycle against the documented Chapter 3 data requirements.

### Device model

The persistence model contains:

* UUID `id`
* `name`
* IPv4 `ip_address`
* `device_type`
* monitoring `status`
* `monitoring_enabled`
* creation/update timestamps

The API continues exposing `type` and `ipAddress` to preserve the established frontend contract while the database field is now explicitly named `device_type`.

### Device types

Supported values are:

* `router`
* `switch`
* `server`
* `access-point`
* `firewall`
* `other`

### Device management API

```text
GET    /api/devices/
POST   /api/devices/
GET    /api/devices/<id>/
PATCH  /api/devices/<id>/
PUT    /api/devices/<id>/
DELETE /api/devices/<id>/
PATCH  /api/devices/<id>/monitoring/
GET    /api/devices/<id>/monitoring-snapshot/
```

Device management is restricted to authenticated Django staff users (`is_staff=True`). Unauthenticated requests receive `401`; authenticated non-administrators receive `403`.

Registration automatically creates the associated one-to-one `MonitoringConfiguration`. Deleting a device uses the existing cascade relationships, so its monitoring configuration, monitoring records, and fault records are deleted with the device. This is intentionally destructive behavior and should be treated accordingly by clients.

### Validation

The API validates:

* required/non-empty device names
* IPv4 addresses
* supported device types

IPv6 addresses are rejected because the current documented model is IPv4-based.

### API documentation

Detailed device-management API documentation is available in `docs/API.md`.

## Existing API Contract

### Authentication

```text
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/me/
```

Protected requests use `Authorization: Token <token>`.

### Devices

```text
GET    /api/devices/
POST   /api/devices/
GET    /api/devices/<id>/
PATCH  /api/devices/<id>/
PUT    /api/devices/<id>/
DELETE /api/devices/<id>/
PATCH  /api/devices/<id>/monitoring/
GET    /api/devices/<id>/monitoring-snapshot/
```

### Monitoring

```text
GET /api/monitoring-records/
GET /api/monitoring-records/<id>/
GET /api/devices/<id>/monitoring-snapshot/
GET /api/monitoring-history/
```

### Faults

```text
GET    /api/faults/
POST   /api/faults/
GET    /api/faults/<id>/
PATCH  /api/faults/<id>/
PUT    /api/faults/<id>/
POST   /api/faults/<id>/acknowledge/
POST   /api/faults/<id>/resolve/
PATCH  /api/faults/<id>/status/
GET    /api/fault-history/
```

### Notifications

```text
GET  /api/notifications/
GET  /api/notifications/<id>/
POST /api/notifications/<id>/read/
```

Creating a fault automatically creates its notification record. Email, SMS, and browser push delivery are not implemented yet.

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

## Monitoring Workflow

1. Administrator registers a network device.
2. The monitoring engine schedules periodic checks.
3. The system performs connectivity and metric collection.
4. Monitoring data is stored for analysis.
5. The fault detection engine evaluates the collected data.
6. Detected faults are classified by severity.
7. Fault events are recorded.
8. A notification record is created for the detected fault.
9. Administrators can acknowledge or resolve faults.
10. Historical monitoring and fault data can be analyzed later.

## Phase Status

* Phase 1 — Frontend Foundation & Application Shell — completed
* Phase 2 — Frontend Authentication — completed
* Phase 3 — Network Monitoring Dashboard — completed
* Phase 4 — Network Device Management — completed
* Phase 5 — Device Details and Monitoring — completed
* Phase 6 — Fault Management — completed
* Phase 7 — Historical Monitoring and Fault History — completed
* Phase 8 — Notification Experience — completed
* Phase 9A — Django REST Backend Contracts — implemented
* Phase 9B — Frontend API Integration — implemented
* Phase 10 — Frontend Testing and Hardening — in progress
* Phase 11 — Django Backend Foundation — implemented
* Phase 13 — Device Management Backend — implemented

## Validation

From `backend/`:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

Phase 13 adds device lifecycle, validation, administrator-access, monitoring-association, and delete-behavior coverage while preserving the existing API contract.

## Academic Project

This system is developed as an academic project demonstrating the application of:

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
