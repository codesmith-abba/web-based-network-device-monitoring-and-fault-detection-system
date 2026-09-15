# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 10 — Frontend Testing and Hardening

The frontend has been audited as the integration surface for the Django REST backend. Phase 10 focuses on correctness, predictable failure states, responsive behavior, accessibility, strict typing, and production validation without redesigning the existing feature set.

### Coverage audit

| Area | Verified focus |
| --- | --- |
| Authentication | validation, loading, backend failures, protected navigation, session restoration, logout, safe redirect handling |
| Dashboard | backend loading/error/empty data, responsive summary and fault presentation |
| Devices | form validation, list/filter/sort/pagination, create/update/monitoring actions, API failures |
| Device details | invalid/missing device state, monitoring loading/error/empty/partial data |
| Monitoring | current vs historical separation, chart/table readability, empty/error states |
| Faults | filtering, acknowledgement, resolution, status updates, API failures, accessible severity/status text |
| History | monitoring/fault filters, empty/error/loading states, responsive tables and chart overflow |
| Notifications | unread/read state, details, refresh, backend failures, header indicator |
| Navigation | protected routes, login redirect, device-detail route matching, responsive shell |

### Hardening completed

- Production service path remains the real Django REST API; no fabricated live data was introduced.
- Shared API client centralizes token headers, JSON parsing, API errors, and network failures.
- Authentication uses session storage for the DRF token and validates the session through `/api/auth/me/`.
- Existing loading, empty, and error UI states remain part of the page-level contracts.
- User input validation remains explicit on authentication and device management flows.
- TypeScript application compilation now uses `strict: true` together with unused-code checks.
- ESLint remains enabled with TypeScript and React Hooks rules.
- No additional runtime dependency was added; the existing dependency set is intentionally small and is used by the application/toolchain.
- Vite production builds remain the deployment validation target.
- A GitHub Actions frontend validation workflow runs `npm ci`, `npm run lint`, and `npm run build` for frontend changes.

### Accessibility baseline

The existing UI uses semantic headings, labels, form associations, `aria-invalid`/`aria-describedby` validation feedback, live status messaging where appropriate, keyboard-operable buttons and dialogs, and text/symbol combinations for status information rather than color alone. Responsive tables and charts provide horizontal scrolling where dense data cannot safely collapse.

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

Dashboard, devices, monitoring, faults, history, and notifications use their real backend service boundaries. Frontend code does not recreate backend monitoring or fault business logic.

The backend currently does not implement a live ICMP/SNMP monitoring worker, so the frontend does not claim live monitoring measurements beyond records actually returned by the API. No email, SMS, browser push, or other external notification delivery is claimed.

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

Start the Django backend on `127.0.0.1:8000` so the Vite `/api` proxy can reach it.

For isolated UI testing, the existing mock adapters can still be enabled explicitly; they are no longer the production service path.

## Validation

```bash
npm run lint
npm run build
```

The same commands run in GitHub Actions for frontend changes.

### Integration smoke checklist

1. Sign in with a valid Django administrator account.
2. Verify invalid credentials and blank fields produce clear errors.
3. Verify a protected route redirects unauthenticated users to login.
4. Verify dashboard, devices, device details, faults, history, and notifications render backend responses.
5. Verify empty API responses render empty states rather than fabricated records.
6. Verify network/API failures render actionable error states.
7. Verify device validation rejects invalid IP addresses and missing required fields.
8. Verify fault acknowledgement/resolution and notification read actions update backend state.
9. Verify the application remains usable at narrow/mobile widths.
10. Run `npm run lint` and `npm run build` before deployment.
