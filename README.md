# Web-Based Network Device Monitoring and Fault Detection System

A web-based network monitoring platform for continuously monitoring network devices, detecting faults, tracking network health, and providing administrators with real-time visibility into infrastructure status.

## Overview

The **Web-Based Network Device Monitoring and Fault Detection System** is a network management application designed to help administrators monitor the health and availability of network devices from a centralized web interface.

The system periodically collects network and device information, analyzes monitoring results, detects predefined fault conditions, records fault events, and presents network health information through an interactive dashboard.

It is designed to reduce the difficulty of manually checking network devices and to provide faster identification of network failures and performance problems.

## Key Features

* **Device Management**
* **Real-Time Monitoring**
* **Fault Detection**
* **Fault Management**
* **Web Dashboard**
* **Notifications**
* **Historical Analytics**

## System Architecture

```text
Web Dashboard (React / TypeScript)
              │
           REST API
              │
Django + Django REST Framework
              │
     Network monitoring domain
      ┌───────┼────────┐
   Devices  Monitoring Faults
                         │
                   Notifications
```

## Phase 9A — Django REST Backend Contracts

Phase 9A establishes the first real backend contract. The backend is no longer only a Django project skeleton: it now contains a `network` Django application, DRF authentication, domain models, serializers, authenticated API views, URL routing, migrations, notification generation, and API tests.

### Authentication

Token authentication is used for the current REST contract.

```text
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/me/
```

Login accepts:

```json
{
  "username": "admin",
  "password": "..."
}
```

A successful login returns a token and basic user information. Protected API requests use:

```text
Authorization: Token <token>
```

### Device API

```text
GET    /api/devices/
POST   /api/devices/
GET    /api/devices/<id>/
PATCH  /api/devices/<id>/
PUT    /api/devices/<id>/
PATCH  /api/devices/<id>/monitoring/
GET    /api/devices/<id>/monitoring-snapshot/
```

Device responses use the frontend contract naming (`ipAddress`, `monitoring`, `createdAt`, `updatedAt`) while Django model fields remain Pythonic.

### Dashboard API

```text
GET /api/dashboard/
```

Returns:

* device summary counts
* device health information
* active faults

### Monitoring API

```text
GET /api/monitoring-records/
GET /api/monitoring-records/<id>/
GET /api/devices/<id>/monitoring-snapshot/
```

Historical monitoring is available through:

```text
GET /api/monitoring-history/
```

Supported query parameters include `deviceId`, `from`, and `to`.

### Fault API

```text
GET    /api/faults/
POST   /api/faults/
GET    /api/faults/<id>/
PATCH  /api/faults/<id>/
PUT    /api/faults/<id>/
POST   /api/faults/<id>/acknowledge/
POST   /api/faults/<id>/resolve/
PATCH  /api/faults/<id>/status/
```

Fault history is available through:

```text
GET /api/fault-history/
```

### Notification API

```text
GET  /api/notifications/
GET  /api/notifications/<id>/
POST /api/notifications/<id>/read/
```

Creating a fault automatically creates its notification record. Phase 9A does not claim email, SMS, or browser push delivery; those remain future integrations.

## Fault Detection Logic

The monitoring engine evaluates collected measurements against configurable thresholds and fault-detection rules.

Example:

```text
Device does not respond
        │
        ▼
Retry monitoring probe
        │
        ▼
Repeated failure?
     /       \
   No         Yes
   │           │
   ▼           ▼
Continue    Device DOWN
monitoring      │
                ▼
          Create fault event
                │
                ▼
          Create notification
```

## Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* Celery (planned monitoring worker integration)
* Redis (planned monitoring worker integration)

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

* SQLite for the current development backend foundation
* PostgreSQL remains the planned production database

### Infrastructure

* Linux
* Nginx
* Gunicorn / ASGI
* Git & GitHub

## Backend Structure

```text
backend/
├── backend/
│   ├── settings.py
│   └── urls.py
├── network/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── signals.py
│   └── tests.py
└── requirements.txt
```

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
* Phase 9B — Frontend API Integration — next

## Project Status

**🚧 In Development**

This project is being developed as a practical network monitoring and fault-detection platform, with emphasis on reliability, modularity, observability, and maintainable software architecture.

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

---

⭐ If you find this project interesting, consider giving the repository a star.
