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

## Architecture

```text
src/
├── components/       # Shared UI primitives and icons
├── layouts/          # Application-level layouts and shell
├── pages/            # Page-level views
└── types/            # Shared TypeScript contracts
```

Feature-specific folders, API services, hooks, and domain types will be introduced when their corresponding phases are implemented. This keeps Phase 1 small and avoids creating unused architecture prematurely.

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

## Validation

Run:

```bash
npm run lint
npm run build
```

The repository's existing `package-lock.json` predates the Phase 1 Tailwind dependency additions. Run `npm install` before validation so npm regenerates the lockfile with the newly declared dependencies; the lockfile should then be committed as part of the Phase 1 dependency update.

## Next phase

Phase 2 will implement the frontend authentication experience. Backend authentication and API integration are intentionally outside Phase 1.
