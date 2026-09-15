# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 9B — Django REST API Integration

The frontend is now connected to the actual Django REST contracts from Phase 9A.

### Connected APIs

- Authentication: `/api/auth/login/`, `/api/auth/me/`, `/api/auth/logout/`
- Dashboard: `/api/dashboard/`
- Devices: `/api/devices/`
- Device monitoring controls: `/api/devices/:id/monitoring/`
- Device monitoring snapshot: `/api/devices/:id/monitoring-snapshot/`
- Faults: `/api/faults/`
- Fault acknowledgement/resolution/status: `/api/faults/:id/...`
- Monitoring history: `/api/monitoring-history/`
- Fault history: `/api/fault-history/`
- Notifications: `/api/notifications/`
- Notification read state: `/api/notifications/:id/read/`

The shared API client is in `src/api/client.ts`. It sends the Django REST Framework token using the `Authorization: Token ...` header, parses API errors, and reports network failures consistently.

### API configuration

By default, the frontend uses `/api` as its API base path. Vite proxies `/api` to `http://127.0.0.1:8000` during development.

Set `VITE_API_BASE_URL` when the frontend and API are served through a different base URL.

```bash
VITE_API_BASE_URL=/api npm run dev
```

### Authentication

Production authentication is the default. The login form calls the real Django login endpoint and stores the returned DRF token in session storage. Session startup validates the token through `/api/auth/me/`; logout calls the backend and clears the token.

The existing mock authentication adapter remains available only for isolated UI testing with `VITE_AUTH_ADAPTER=mock`.

### Backend-driven state

Dashboard, devices, monitoring, faults, history, and notifications now use their real backend service boundaries. Frontend code does not recreate backend monitoring or fault business logic.

The UI still handles loading, empty, error, and unauthorized states. HTTP 401/403 responses are surfaced through the existing service boundaries so the application can require a fresh authentication session.

The backend currently does not implement a live ICMP/SNMP monitoring worker, so the frontend does not claim live monitoring measurements beyond records actually returned by the API. SNMP capability states remain backend-driven.

No email, SMS, browser push, or other external notification delivery is claimed.

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

From `frontend/`:

```bash
npm install
npm run dev
```

Start the Django backend on its normal development port (`127.0.0.1:8000`) so the Vite `/api` proxy can reach it.

For isolated UI testing, the existing mock adapters can still be enabled explicitly; they are no longer the production service path.

## Validation

```bash
npm run lint
npm run build
```

Phase 9B acceptance checks:

1. Sign in through the Django API.
2. Verify `/api/auth/me/` restores an authenticated session.
3. Verify dashboard data comes from `/api/dashboard/`.
4. Verify device list, create, edit, and monitoring state use Django endpoints.
5. Verify device monitoring details use the monitoring snapshot endpoint.
6. Verify fault list, acknowledgement, resolution, and status updates use Django endpoints.
7. Verify monitoring and fault history use the real history endpoints.
8. Verify notifications and mark-as-read use Django endpoints.
9. Verify unauthorized and network failures are surfaced without fabricated data.
10. Run `npm run lint` and `npm run build` before merging.
