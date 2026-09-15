# Network Monitoring Frontend

React + TypeScript frontend for the Web-Based Network Device Monitoring and Fault Detection System.

## Purpose

The frontend is the administrator-facing integration surface for the Django REST backend. It consumes backend state for authentication, dashboard information, device management, monitoring, faults, history, and in-application notifications.

The frontend does not implement ICMP/SNMP monitoring or fault-detection rules itself.

## Architecture

```text
React / TypeScript / Vite
          │
       Shared API client
          │ /api
          ▼
Django REST Framework
          │
          ├── Authentication
          ├── Devices
          ├── Monitoring
          ├── Faults
          ├── History
          └── Notifications
```

Source structure:

```text
src/
├── api/              # shared API client and error/auth handling
├── auth/             # login, session and route protection
├── components/       # reusable UI components
├── dashboard/        # dashboard API contracts/services
├── devices/          # device API contracts/services
├── faults/           # fault API contracts/services
├── history/          # historical API boundaries
├── monitoring/       # monitoring API services
├── notifications/    # notification API services
├── layouts/          # application shell
├── pages/            # page-level views
└── types/            # shared TypeScript contracts
```

## Technology

- React
- TypeScript
- Vite
- Tailwind CSS v4
- Recharts
- Django REST Framework backend

## API Configuration

The default API base is `/api`.

During development, Vite proxies `/api` to `http://127.0.0.1:8000`.

```bash
VITE_API_BASE_URL=/api npm run dev
```

Do not place secrets in `VITE_*` variables; Vite exposes them to browser code.

## Authentication

The normal application path uses Django REST Framework token authentication:

1. Login calls `/api/auth/login/`.
2. The returned token is stored in session storage.
3. Application startup validates the token through `/api/auth/me/`.
4. Logout calls `/api/auth/logout/` and clears local session state.
5. A `401` API response clears the frontend session and returns the user to authentication.

The mock authentication adapter is retained only for isolated UI testing and is not the production service path.

## Development

Start the backend services first:

```bash
cd ../backend
source env/bin/activate
redis-server
celery -A backend worker -l info
celery -A backend beat -l info
python manage.py runserver
```

Then start the frontend:

```bash
cd ../frontend
npm install
npm run dev
```

## Validation

```bash
npm run lint
npm run build
```

Backend validation:

```bash
cd ../backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Implemented UI Scope

The final frontend supports the documented administrator workflows:

- login/logout and protected navigation
- dashboard overview
- device registration and management
- monitoring configuration
- device monitoring details
- current health and monitoring results
- fault listing/details/filtering
- fault acknowledgement and resolution
- monitoring history
- fault history
- in-application notifications

External email, SMS, browser push, or third-party alert delivery is not claimed by the frontend.

## Integration Smoke Test

1. Start Redis.
2. Start Django.
3. Start Celery worker.
4. Start Celery Beat.
5. Start the Vite frontend.
6. Sign in with a staff administrator.
7. Register a test device.
8. Configure and enable monitoring.
9. Verify monitoring results and device status.
10. Trigger a controlled fault condition.
11. Verify the dashboard and active-fault view.
12. Verify the in-application notification.
13. Verify monitoring and fault history.
14. Acknowledge and resolve the fault.
15. Verify the updated backend state.

Controlled automated end-to-end API coverage is provided by `backend/network/test_system_integration.py`.

## Production Build

The production build uses the same-origin `/api` path:

```bash
printf 'VITE_API_BASE_URL=/api\n' > .env.production
npm install
npm run lint
npm run build
```

The generated `dist/` directory is served by Nginx in the documented Linux deployment.

See [`../deploy/README.md`](../deploy/README.md) for deployment instructions and [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for the complete system architecture.
