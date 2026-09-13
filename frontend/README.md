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

## Architecture

```text
src/
├── auth/             # Authentication contracts, service boundary, state, route guard
├── components/       # Shared UI primitives and icons
├── layouts/          # Application-level layouts and shell
├── pages/            # Page-level views
└── types/            # Shared TypeScript contracts
```

Feature-specific API integrations remain separated from page and shell components. The authentication interface can therefore be connected to Django/DRF later without redesigning the login UI or protected-route flow.

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

This mock mode must not be used as production authentication.

## Validation

Run:

```bash
npm run lint
npm run build
```

Manual authentication acceptance checks:

1. Open `/` while signed out → redirected to `/login`.
2. Submit empty fields → required-field errors are shown and no login request is attempted.
3. Submit non-empty credentials in mock mode → loading state appears, then the dashboard opens.
4. Reload while authenticated → the session is restored.
5. Open `/login` while authenticated → redirected to the dashboard.
6. Click **Sign out** → session is cleared and `/login` opens.
7. Let the mock session expire or remove the stored session → protected navigation requires sign in again.
8. Run without the mock adapter → login displays a clear authentication-not-configured error rather than calling a guessed backend endpoint.

## Next phase

Future phases can add the concrete Django/DRF authentication adapter once the backend authentication contract exists.
