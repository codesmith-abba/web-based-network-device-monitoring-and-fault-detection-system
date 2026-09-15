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

`src/monitoring/service.ts` remains deliberately unconfigured unless `VITE_MONITORING_ADAPTER=mock` is enabled. Mock measurements are clearly labelled fixture data and are not live network measurements.

## Phase 6 — Fault Management

Implemented `/faults` with fault type, severity, affected device, detection time, status, details, acknowledgement, resolution, search, filters, sorting, loading/empty/error states, typed `FaultService`, and a deliberately unconfigured default backend adapter.

## Phase 7 — Historical Monitoring and Fault History

Implemented separate historical views:

- `/monitoring-history` — historical monitoring measurements
- `/fault-history` — historical fault events

Historical monitoring provides:

- Device filtering
- Date/time range filtering
- Timestamp
- Device
- Latency
- Packet loss
- Reachability
- Responsive latency trend chart
- Historical measurement table
- Loading, empty, filtered-empty, and error states
- Clear separation from current device status

Historical fault visibility provides:

- Device filtering
- Date/time range filtering
- Fault-type filtering
- Severity filtering
- Status filtering
- Device
- Fault type
- Severity
- Detection time
- Current status
- Resolution timestamp when supplied
- Loading, empty, filtered-empty, and error states

### Historical data boundary

Phase 7 introduces dedicated typed service boundaries in `src/history/`:

```text
MonitoringHistoryService
└── list()

FaultHistoryService
└── list()
```

The default services remain unconfigured until the Django/DRF historical API contracts exist. The mock historical monitoring view reuses the monitoring records already defined by the Phase 5 mock adapter; the fault history view reuses the existing Phase 6 fault fixtures. No new historical measurements or fault events are fabricated by Phase 7.

### Historical state testing

From `frontend/`:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_MONITORING_ADAPTER=mock \
VITE_FAULTS_ADAPTER=mock \
npm run dev
```

Open:

```text
/monitoring-history
/fault-history
```

Use the development history scenarios:

```bash
VITE_HISTORY_SCENARIO=populated
VITE_HISTORY_SCENARIO=empty
VITE_HISTORY_SCENARIO=partial
VITE_HISTORY_SCENARIO=error
VITE_HISTORY_SCENARIO=loading
```

The development banners explicitly identify reused fixture data. Production historical records must come from the eventual backend monitoring and fault-history services.

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

Authentication testing:

```bash
VITE_AUTH_ADAPTER=mock npm run dev
```

For Phase 7 historical views:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_MONITORING_ADAPTER=mock \
VITE_FAULTS_ADAPTER=mock \
npm run dev
```

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 7 acceptance checks:

1. Authenticate with the development auth adapter.
2. Open `/monitoring-history` and verify historical measurements are distinct from current device status.
3. Filter monitoring history by device and date/time range.
4. Verify latency and packet-loss values, timestamps, and reachability are displayed.
5. Verify the latency chart remains readable on mobile through horizontal scrolling when required.
6. Open `/fault-history` and verify device, fault type, severity, detection time, status, and supplied resolution information.
7. Filter fault history by device, date/time, fault type, severity, and status.
8. Verify loading, empty, filtered-empty, partial, and error states.
9. Verify mock historical monitoring reuses existing monitoring records rather than creating fabricated history.
10. Verify mock fault history reuses existing fault events rather than creating fabricated live faults.
11. Verify the default non-mock services report not-configured errors rather than guessing backend endpoints.
12. Resize across desktop, tablet, and mobile widths.
13. Run `npm run lint` and `npm run build` before merging.
