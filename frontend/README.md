# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 23 — Full System Integration

The frontend is the real integration surface for the Django REST backend. The production service path uses the live API for authentication, dashboard, device management, monitoring, faults, historical records, and notifications.

### Integration architecture

```text
React/Vite
   │
   │ /api
   ▼
Django REST API
   │
   ├── Authentication / administrator access
   ├── Device management
   ├── Monitoring configuration
   ├── Immediate ICMP monitoring
   ├── Historical monitoring records
   ├── Fault evaluation and lifecycle
   ├── Notifications
   └── Dashboard aggregation
          │
          ▼
      Redis / Celery
          │
          └── Background monitoring dispatch
```

### Backend-driven state

Dashboard, devices, monitoring, faults, history, and notifications use their real backend service boundaries. Frontend code does not recreate backend monitoring or fault business logic.

The backend now provides the background monitoring worker path through Celery and Redis. ICMP monitoring results are persisted by Django, evaluated against fault thresholds, and exposed to the dashboard, fault history, and notification APIs. SNMP configuration and collection endpoints are also available through the backend.

The frontend does not claim external email, SMS, browser push, or other notification delivery; the current notification contract is the in-application administrator notification record.

### API configuration

By default, the frontend uses `/api` as its API base path. Vite proxies `/api` to `http://127.0.0.1:8000` during development.

Set `VITE_API_BASE_URL` when the frontend and API are served through a different base URL.

```bash
VITE_API_BASE_URL=/api npm run dev
```

### Authentication

Production authentication is the default. The login form calls the real Django login endpoint and stores the returned DRF token in session storage. Session startup validates the token through `/api/auth/me/`; logout calls the backend and clears the token.

The existing mock authentication adapter remains available only for isolated UI testing with `VITE_AUTH_ADAPTER=mock`.

## Earlier phases

### Phase 1 — Foundation

Responsive administrator shell, mobile navigation, application header, dashboard foundation, Tailwind CSS v4, accessible navigation, typed navigation, and a structure prepared for Django REST integration.

### Phase 2 — Authentication

Administrator login, validation, protected routes, session handling, logout, and typed authentication contracts.

### Phase 3 — Network Monitoring Dashboard

Centralized network overview with device totals, online/offline state, active faults, device health, and monitoring snapshot presentation.

### Phase 4 — Network Device Management

Device registration/editing, validation, monitoring enable/disable, search/filter/sort/pagination, and responsive management UI. Device deletion remains unavailable because the backend contract does not define it.

### Phase 5 — Device Details and Monitoring

Device identity, current status, monitoring status, availability/reachability, latency, packet loss, latest result, historical latency visualization, SNMP capability states, and monitoring configuration.

### Phase 6 — Fault Management

Fault type, severity, affected device, detection time, status, details, acknowledgement, resolution, search, filtering, sorting, and responsive states.

### Phase 7 — Historical Monitoring and Fault History

Monitoring and fault history views with device/domain filters, date/time filters, responsive visualization, resolution information, and loading/empty/error states.

### Phase 8 — Notification Experience

Administrator notification list, header unread indicator, notification details, read/unread state, mark-as-read interaction, and responsive states.

### Phase 9B — Django REST API Integration

Shared API client, real authentication, dashboard/device/monitoring/fault/history/notification API services, DRF token handling, API error handling, and Vite development proxy.

### Phase 10 — Frontend Testing and Hardening

The frontend was audited as the integration surface for the Django REST backend. Validation covers authentication, dashboard, devices, monitoring, faults, history, notifications, navigation, strict TypeScript compilation, ESLint, responsive behavior, accessibility, and production builds.

## Architecture

```text
src/
├── api/              # Shared Django REST API client and token handling
├── auth/             # Authentication contracts, API service, state, route guard
├── components/       # Shared UI primitives and states
├── dashboard/        # Dashboard contracts and API service
├── devices/          # Device contracts and API service
├── faults/           # Fault contracts and API service
├── history/          # Historical API service boundaries
├── monitoring/       # Device monitoring API service
├── notifications/    # Notification API service
├── layouts/          # Application shell
├── pages/            # Page-level views
└── types/            # Shared TypeScript contracts
```

## Technology

- React
- TypeScript
- Vite
- Tailwind CSS v4
- Django REST Framework backend

## Development

Start Redis, Django, Celery worker, and Celery Beat from the backend, then start the frontend.

From `frontend/`:

```bash
npm install
npm run dev
```

The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

## Validation

```bash
npm run lint
npm run build
```

Backend validation from `backend/`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Phase 23 integration smoke checklist

1. Start Redis.
2. Start Django on `127.0.0.1:8000`.
3. Start Celery worker.
4. Start Celery Beat for background monitoring dispatch.
5. Start the Vite frontend.
6. Sign in with a valid Django administrator account.
7. Register a test device with monitoring enabled.
8. Open the device details page and verify monitoring configuration and current state.
9. Verify the background worker creates monitoring records at the configured interval.
10. Verify ICMP monitoring updates device status and persisted monitoring results.
11. Trigger a controlled high-latency or unreachable condition and verify a `FaultEvent` is created.
12. Verify the dashboard reflects the device result and active fault.
13. Verify an in-application notification is created for the fault.
14. Verify monitoring and fault history contain the generated records.
15. Acknowledge and resolve the fault from the frontend.
16. Verify the backend status and dashboard update after resolution.
17. Restore the device condition and verify automatic fault recovery where applicable.
18. Run the complete backend and frontend test/validation suites.

For controlled automated API coverage, `backend/network/test_system_integration.py` verifies the administrator login → device registration → monitoring configuration → ICMP result → fault → notification → dashboard → history → acknowledgement/resolution → monitoring snapshot workflow without requiring a real network device.
