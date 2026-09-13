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

## Phase 5 — Device Details and Monitoring

Phase 5 adds the individual-device monitoring experience at `/devices/:deviceId`.

Implemented:

- Device identity, IP address, type, current status, and monitoring status
- Latest availability/reachability result
- Latest latency and packet-loss measurements
- Latest monitoring timestamp
- Typed monitoring records and monitoring-service boundary
- Historical latency visualization only when historical measurements exist
- Clear separation between current status and historical measurements
- SNMP metric section with explicit unavailable states when the monitoring source does not provide SNMP data
- Monitoring configuration visibility, including monitoring state, interval, SNMP state/version, and reported metric capabilities
- Loading, unavailable-device, API-error, missing-metric, empty-history, and no-data states
- Development-only mock monitoring scenarios: `populated`, `empty`, `partial`, `error`, and `loading`
- Explicit mock-data banner so fixture measurements cannot be mistaken for live network measurements

### Monitoring data boundary

`src/monitoring/types.ts` defines the frontend monitoring contract:

```text
DeviceMonitoringService
└── getSnapshot(deviceId)
    ├── latest MonitoringRecord
    ├── history MonitoringRecord[]
    ├── snmpMetrics SnmpMetric[]
    └── configuration MonitoringConfiguration
```

`src/monitoring/service.ts` is deliberately unconfigured unless `VITE_MONITORING_ADAPTER=mock` is enabled. It does not assume Django/DRF monitoring URLs, HTTP methods, polling APIs, SNMP response shapes, or live measurements.

The mock monitoring adapter contains clearly labelled fixture records for UI testing only. Production monitoring values must come from the eventual backend monitoring service.

Example local testing:

```bash
VITE_AUTH_ADAPTER=mock \
VITE_DEVICES_ADAPTER=mock \
VITE_MONITORING_ADAPTER=mock \
npm run dev
```

Monitoring state testing:

```bash
VITE_MONITORING_SCENARIO=populated
VITE_MONITORING_SCENARIO=empty
VITE_MONITORING_SCENARIO=partial
VITE_MONITORING_SCENARIO=error
VITE_MONITORING_SCENARIO=loading
```

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives, states, badges, and icons
├── dashboard/        # Dashboard data contracts and service boundary
├── devices/          # Device contracts and service boundary
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

Then open `/devices/rtr-01` or another device ID present in the development device adapter.

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 5 acceptance checks:

1. Authenticate with the development auth adapter and open a device details URL such as `/devices/rtr-01`.
2. Verify device identity, IP address, type, current status, and monitoring state.
3. Verify availability/reachability, latency, packet loss, latest result, and timestamp render from the typed monitoring contract.
4. Verify current status and historical measurements are presented as separate concepts.
5. Verify historical latency visualization appears only when historical data exists.
6. Verify SNMP metrics remain explicitly unavailable when the monitoring source does not provide them.
7. Verify monitoring configuration visibility.
8. Test `empty`, `partial`, `error`, and `loading` monitoring scenarios.
9. Verify an unknown device produces a clear unavailable-device error.
10. Verify the default, non-mock monitoring adapter reports not-configured instead of making a guessed API request.
11. Verify fixture measurements are visibly labelled as development data and are never presented as live network measurements.
12. Resize across desktop, tablet, and mobile widths and verify the details experience remains usable.
13. Run `npm run lint` and `npm run build` before merging.
