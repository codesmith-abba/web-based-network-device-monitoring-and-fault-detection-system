# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 1 — Foundation

Responsive administrator shell, mobile navigation, application header, dashboard foundation, Tailwind CSS v4, accessible navigation, typed navigation, and a structure prepared for Django REST integration. Unimplemented features remain disabled rather than presenting fake functionality.

## Phase 2 — Authentication

Administrator login at `/login`, validation, accessible errors, loading states, protected routes, session persistence/expiration, logout, and a typed `AuthService` boundary. The development-only mock adapter is enabled with `VITE_AUTH_ADAPTER=mock`; no backend authentication endpoint was invented.

## Phase 3 — Network Monitoring Dashboard

Implemented the centralized network overview with Total Devices, Online, Offline, and Active Faults summary cards; device health; active faults; monitoring snapshot; reusable dashboard states/badges; responsive layouts; and typed monitoring contracts.

## Phase 4 — Network Device Management

Implemented `/devices`, device registration/editing, validation, monitoring enable/disable, search/filter/sort/pagination, responsive states, and a typed `DeviceService`. Device deletion remains unavailable because the current backend contract does not define a delete operation.

## Phase 5 — Device Details and Monitoring

Implemented `/devices/:deviceId` with device identity, current status, monitoring status, availability/reachability, latency, packet loss, latest result/timestamp, historical latency visualization, SNMP capability states, monitoring configuration, and loading/error/empty/partial states.

## Phase 6 — Fault Management

Implemented `/faults` with fault type, severity, affected device, detection time, status, details, acknowledgement, resolution, search, filters, sorting, loading/empty/error states, typed `FaultService`, and a deliberately unconfigured default backend adapter.

## Phase 7 — Historical Monitoring and Fault History

Implemented `/monitoring-history` and `/fault-history` with typed historical service boundaries, date/time and domain filters, responsive visualization, resolution information, and complete loading/empty/error states. Historical mock data reuses existing Phase 5 monitoring records and Phase 6 fault events; it does not fabricate new historical records.

## Phase 8 — Notification Experience

Implemented the administrator notification experience at `/notifications` and added a notification indicator to the application header.

The notification experience provides:

- Fault type
- Affected device
- Severity
- Detection time
- Read/unread state
- Notification details
- Mark-as-read interaction where the adapter supports it
- Header unread-count indicator
- Recent notification preview
- Empty, loading, action-error, and unavailable states
- Responsive notification list and details dialog

### Notification architecture

Phase 8 introduces `src/notifications/` with a typed service boundary:

```text
NotificationService
├── list()
└── markAsRead(notificationId)
```

The default service deliberately remains unconfigured until the Django/DRF notification API contract exists. The development adapter derives notifications from the existing fault service so the frontend can be exercised without inventing a backend endpoint or notification channel.

No email, SMS, browser push, or other external notification delivery is claimed by this frontend phase. Those channels require explicit backend implementation and contracts.

### Notification development testing

From `frontend/`:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_MONITORING_ADAPTER=mock \
VITE_FAULTS_ADAPTER=mock \
VITE_NOTIFICATIONS_ADAPTER=mock \
npm run dev
```

Open:

```text
/notifications
```

Notification scenarios:

```bash
VITE_NOTIFICATIONS_SCENARIO=populated
VITE_NOTIFICATIONS_SCENARIO=empty
VITE_NOTIFICATIONS_SCENARIO=partial
VITE_NOTIFICATIONS_SCENARIO=error
VITE_NOTIFICATIONS_SCENARIO=loading
```

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives, states, badges, and icons
├── dashboard/        # Dashboard data contracts and service boundary
├── devices/          # Device contracts and service boundary
├── faults/           # Fault contracts and service boundary
├── history/          # Historical monitoring/fault contracts and service boundaries
├── monitoring/       # Device monitoring contracts and service boundary
├── notifications/    # Notification contracts and service boundary
├── layouts/          # Application-level layouts and shell
├── pages/            # Page-level views
└── types/            # Shared TypeScript contracts
```

## Technology

- React
- TypeScript
- Vite
- Tailwind CSS v4

## Development

From `frontend/`:

```bash
npm install
npm run dev
```

For the full frontend mock environment:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_MONITORING_ADAPTER=mock \
VITE_FAULTS_ADAPTER=mock \
VITE_NOTIFICATIONS_ADAPTER=mock \
npm run dev
```

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 8 acceptance checks:

1. Authenticate with the development auth adapter.
2. Verify the header notification indicator is visible and keyboard accessible.
3. Verify unread notifications produce an explicit unread count.
4. Open `/notifications` and verify fault type, device, severity, and detection time.
5. Open notification details and verify the complete notification information.
6. Mark an unread notification as read and verify the list and header state update.
7. Verify empty, loading, error, and action-error states.
8. Verify the development adapter reuses existing fault fixtures rather than fabricating live backend notifications.
9. Verify the default non-mock notification service reports a not-configured state rather than guessing an API endpoint.
10. Verify no email, SMS, push, or other external delivery is presented as implemented.
11. Resize across desktop, tablet, and mobile widths.
12. Run `npm run lint` and `npm run build` before merging.
