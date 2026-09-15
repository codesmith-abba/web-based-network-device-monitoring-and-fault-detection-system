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

Phase 6 adds the administrator fault-management experience at `/faults`.

Implemented:

- Fault event list with fault type, severity, affected device, detection time, and current status
- Active/acknowledged versus resolved distinction
- Severity presentation with text and symbols rather than color alone
- Fault details dialog with description and resolution timestamp when supplied
- Acknowledge workflow
- Resolve workflow
- Search by device, fault type, and description
- Severity filtering
- Status filtering
- Fault-type filtering
- Device filtering
- Detection-time sorting, newest first
- Active/acknowledged and resolved summary counts
- Loading, empty, filtered-empty, API-error, and action-error states
- Typed `FaultEvent`, `FaultService`, status/severity/type contracts, and service errors
- Explicit service boundary for future Django/DRF integration
- Development-only fault scenarios: `populated`, `empty`, `partial`, `error`, and `loading`
- Explicit development fixture banner so fault fixtures cannot be mistaken for automatically detected live faults

### Fault data boundary

`src/faults/types.ts` defines the frontend contract:

```text
FaultService
├── list()
├── get(faultId)
├── acknowledge(faultId)
├── updateStatus(faultId, status)
└── resolve(faultId)
```

`src/faults/service.ts` contains the adapter boundary. The default service does not guess Django/DRF URLs, HTTP methods, payloads, authentication behavior, or backend response shapes. Status mutations are only available through the temporary mock adapter until the real backend contract is defined.

### Fault state testing

From `frontend/`:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_FAULTS_ADAPTER=mock \
npm run dev
```

Then open `/faults`.

Use these development scenarios:

```bash
VITE_FAULTS_SCENARIO=populated
VITE_FAULTS_SCENARIO=empty
VITE_FAULTS_SCENARIO=partial
VITE_FAULTS_SCENARIO=error
VITE_FAULTS_SCENARIO=loading
```

The fixture adapter exists only to exercise the frontend states and interaction flows. Production fault events must come from the eventual fault-detection/backend service.

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives, states, badges, and icons
├── dashboard/        # Dashboard data contracts and service boundary
├── devices/          # Device contracts and service boundary
├── faults/           # Fault contracts and service boundary
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

Dashboard state testing:

```bash
VITE_DASHBOARD_ADAPTER=mock VITE_DASHBOARD_SCENARIO=populated npm run dev
```

Device-management state testing:

```bash
VITE_DEVICES_ADAPTER=mock VITE_DEVICES_SCENARIO=populated npm run dev
```

Device-details testing:

```bash
VITE_AUTH_ADAPTER=mock VITE_DEVICES_ADAPTER=mock VITE_MONITORING_ADAPTER=mock npm run dev
```

Fault-management testing:

```bash
VITE_AUTH_ADAPTER=mock VITE_DEVICES_ADAPTER=mock VITE_FAULTS_ADAPTER=mock npm run dev
```

Then open `/faults`.

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 6 acceptance checks:

1. Authenticate with the development auth adapter and open `/faults`.
2. Verify fault type, severity, affected device, detection time, and status are displayed.
3. Verify active/acknowledged and resolved faults are clearly distinguishable.
4. Open fault details and verify all supplied fault information is shown.
5. Verify active faults can be acknowledged through the configured mock adapter.
6. Verify unresolved faults can be resolved through the configured mock adapter.
7. Verify severity, status, fault type, device, and text search filters.
8. Verify newest detection time appears first.
9. Verify loading, empty, filtered-empty, partial, and error states.
10. Verify the default non-mock service reports not-configured/unsupported actions rather than making guessed API requests.
11. Verify fixture events are visibly labelled as development data and are never presented as live detected faults.
12. Resize across desktop, tablet, and mobile widths and verify the fault workflow remains usable.
13. Run `npm run lint` and `npm run build` before merging.
