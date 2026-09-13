# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 1 — Foundation

Responsive administrator shell, mobile navigation, application header, dashboard foundation, Tailwind CSS v4, accessible navigation, typed navigation, and a structure prepared for Django REST integration. Unimplemented features remain disabled rather than presenting fake functionality.

## Phase 2 — Authentication

Administrator login at `/login`, validation, accessible errors, loading states, protected routes, session persistence/expiration, logout, and a typed `AuthService` boundary. The development-only mock adapter is enabled with `VITE_AUTH_ADAPTER=mock`; no backend authentication endpoint was invented.

Authentication boundary:

```text
AuthCredentials → AuthService.login() → AuthSession
```

## Phase 3 — Network Monitoring Dashboard

Implemented the centralized network overview with Total Devices, Online, Offline, and Active Faults summary cards; device health; active faults; monitoring snapshot; reusable dashboard states/badges; responsive layouts; and typed monitoring contracts.

The dashboard service does not invent a Django/DRF endpoint. Without `VITE_DASHBOARD_ADAPTER=mock`, it reports that monitoring is not configured. Mock scenarios are `populated`, `empty`, `partial`, `error`, and `loading`.

## Phase 4 — Network Device Management

Phase 4 implements the administrator device-management workflow required to register and manage network devices.

Implemented:

- `/devices` protected application route
- Device list/table with name, IP address, type, status, and monitoring state
- Device registration form
- Device editing form
- Required-field validation
- IPv4 validation
- Device-type validation
- Monitoring-configuration validation
- Monitoring enable/disable control
- Search by device name, IP address, or type
- Status filtering
- Monitoring-state filtering
- Name, status, and type sorting
- Pagination for the device list
- Loading, empty, filtered-empty, and error states
- Responsive registration/edit dialog and responsive device table
- Accessible labels, validation messages, dialog semantics, and action labels
- Device status labels using text/symbols rather than color alone
- Explicitly no deletion action because the current backend contract does not define a device-delete endpoint

### Device data boundary

`src/devices/types.ts` defines the frontend contract:

```text
DeviceService
├── list()
├── create(DeviceRegistrationInput)
├── update(id, DeviceRegistrationInput)
└── setMonitoring(id, MonitoringState)
```

`src/devices/service.ts` contains the adapter boundary. The default service is deliberately unconfigured and does not guess Django/DRF URLs, HTTP methods, payloads, or response shapes. The temporary development adapter is enabled with:

```bash
VITE_DEVICES_ADAPTER=mock npm run dev
```

The mock adapter supports `VITE_DEVICES_SCENARIO=populated|empty|partial|error|loading` for UI-state testing. Mock device records are development data only and are not live monitoring results.

When the Django/DRF device-management contract is available, replace the service implementation behind the existing typed interface. The page and forms should not need to know the eventual API transport or backend response shape.

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives, states, badges, and icons
├── dashboard/        # Dashboard data contracts and service boundary
├── devices/          # Device contracts and service boundary
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

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 4 acceptance checks:

1. Open `/devices` while authenticated and verify the device list is rendered in mock mode.
2. Open `/devices` without the mock adapter and verify a clear not-configured error is shown rather than a guessed API request.
3. Submit the registration form empty and verify required-field validation.
4. Enter invalid IPv4 values and verify validation errors.
5. Register a valid device in mock mode and verify it appears in the list.
6. Edit a device and verify the updated values appear.
7. Toggle monitoring and verify the monitoring state changes.
8. Search by name, IP, and device type.
9. Filter by status and monitoring state; sort by name, status, and type.
10. Test pagination when more records are available.
11. Test `empty`, `partial`, `error`, and `loading` scenarios.
12. Verify deletion is not exposed until the backend contract explicitly supports it.
13. Resize across desktop, tablet, and mobile widths and verify forms/table remain usable.
14. Verify status and monitoring states remain understandable without relying on color alone.
