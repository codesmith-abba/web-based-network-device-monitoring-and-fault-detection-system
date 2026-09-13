# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Phase 1 — Foundation

Phase 1 replaces the Vite starter screen with the application's responsive administrator shell and establishes the visual foundation for the monitoring system.

Implemented:

- Responsive sidebar navigation
- Responsive mobile navigation drawer
- Application header
- Dashboard landing page foundation
- Network-monitoring visual language and reusable icon primitives
- Tailwind CSS v4 with Vite integration
- Accessible focus states and semantic navigation
- Typed navigation model
- No fake monitoring metrics, device counts, or fault events
- Frontend structure prepared for later Django REST API integration

Navigation items for features that are not yet implemented are intentionally disabled rather than presenting fake functionality.

## Phase 2 — Authentication

Phase 2 adds the administrator authentication experience without inventing a Django/DRF endpoint or response contract.

Implemented:

- Administrator login at `/login`
- Username-or-email identifier and password fields
- Client-side required-field validation
- Accessible field error associations and submission alerts
- Loading and disabled submission states
- Authentication state provider with session persistence
- Protected application routes
- Redirect back to the requested path after sign in
- Logout from the application shell
- Local session expiration handling
- A typed `AuthService` boundary for future Django/DRF integration
- Development-only mock adapter for frontend flow testing

### Authentication boundary

`src/auth/types.ts` defines the frontend contract:

```text
AuthCredentials → AuthService.login() → AuthSession
```

`src/auth/service.ts` currently exposes two explicit modes:

- `VITE_AUTH_ADAPTER=mock` — development-only adapter for exercising the UI. Any non-empty identifier/password is accepted; this is not a production authentication mechanism.
- Default — unconfigured adapter that fails clearly instead of guessing an API URL, endpoint, request body, token format, or response shape.

When Django/DRF authentication is implemented, add a production `AuthService` adapter behind the existing interface. The backend contract should define the actual endpoint, credential payload, session/token mechanism, user representation, and authentication error mapping before that adapter is added.

No backend authentication was added in Phase 2. The current Django project exposes only the admin URL, so the frontend deliberately does not call an invented authentication endpoint.

## Phase 3 — Network Monitoring Dashboard

Phase 3 implements the complete dashboard experience required for centralized network visibility while keeping monitoring data separate from presentation.

Implemented:

- Summary cards for total devices, online devices, offline devices, and active faults
- Device health/status overview with explicit text and symbols, not color alone
- Active fault summary with severity labels
- Monitoring snapshot visualization for returned historical availability data
- Reusable `StatCard`, `StatusBadge`, `FaultSeverityBadge`, `EmptyState`, `LoadingState`, and `ErrorState` components
- Responsive desktop, tablet, and mobile dashboard layouts
- Typed dashboard contracts for summary, device health, faults, and historical monitoring data
- Explicit loading, populated, empty, error, and partial-data states

### Dashboard data boundary

`src/dashboard/types.ts` defines the frontend monitoring contract:

```text
DashboardService → DashboardData → Dashboard UI
```

`src/dashboard/service.ts` intentionally has no invented Django/DRF endpoint. Until the backend contract exists, the default adapter reports the dashboard as not configured rather than fabricating live monitoring results.

For frontend-only state testing, the temporary development adapter can be enabled with:

```bash
VITE_DASHBOARD_ADAPTER=mock VITE_DASHBOARD_SCENARIO=populated npm run dev
```

Supported scenarios are `populated`, `empty`, `partial`, `error`, and `loading`. The mock data is explicitly development-only and must not be treated as live monitoring data.

When the backend monitoring API is available, replace the service implementation behind the existing typed contract. The dashboard UI should not need to know the API transport, authentication details, or backend response shape.

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives, dashboard states, badges, and icons
├── dashboard/        # Dashboard data contracts and service boundary
├── layouts/          # Application-level layouts and shell
├── pages/            # Page-level views
└── types/            # Shared TypeScript contracts
```

Feature-specific data integrations remain separated from page and shell components. This keeps the dashboard ready for real device status, monitoring metrics, active faults, and historical analytics without inventing backend behavior prematurely.

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

For frontend-only authentication flow testing, start Vite with the development adapter enabled:

```bash
VITE_AUTH_ADAPTER=mock npm run dev
```

For dashboard state testing:

```bash
VITE_DASHBOARD_ADAPTER=mock VITE_DASHBOARD_SCENARIO=populated npm run dev
```

This mock mode must not be used as production authentication or monitoring data.

## Validation

Run:

```bash
npm run lint
npm run build
```

Phase 3 dashboard acceptance checks:

1. Run without `VITE_DASHBOARD_ADAPTER=mock` → a clear not-configured dashboard error is shown; no fake live metrics appear.
2. Run with `VITE_DASHBOARD_ADAPTER=mock VITE_DASHBOARD_SCENARIO=populated` → summary cards, device health, active faults, and monitoring snapshot appear.
3. Use `VITE_DASHBOARD_SCENARIO=empty` → zero summary values and appropriate empty states appear.
4. Use `VITE_DASHBOARD_SCENARIO=partial` → returned data is shown with a partial-data warning.
5. Use `VITE_DASHBOARD_SCENARIO=error` → the dashboard error state is shown.
6. Use `VITE_DASHBOARD_SCENARIO=loading` → the loading state remains visible.
7. Resize across desktop, tablet, and mobile widths → dashboard sections remain readable and usable.
8. Device and fault states remain understandable from text/symbol labels even without color perception.
