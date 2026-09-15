# Phase 26 — Production Deployment

## Objective

Prepare the Web-Based Network Device Monitoring and Fault Detection System for Linux production deployment using the documented infrastructure direction.

## Actual deployment architecture

```text
Internet
   │ HTTPS
   ▼
 Nginx
   ├── React/Vite static build
   ├── /static/ → Django collected static files
   ├── /media/  → Django media directory
   └── /api/ and /admin/
             │ localhost
             ▼
      Gunicorn / WSGI
             │
           Django
          /     \
      SQLite   Celery
                  │
                Redis
                  ▲
             Celery Beat
```

The backend currently exposes `backend.wsgi:application`, so Gunicorn WSGI is the correct production application server. No ASGI server was introduced because the actual backend does not currently require ASGI-specific functionality.

## Implemented deployment support

### Django

- `DEBUG` remains environment-controlled and defaults to `False`.
- Production requires `DJANGO_SECRET_KEY`.
- `DJANGO_ALLOWED_HOSTS` is environment-controlled.
- SQLite path is environment-controlled.
- `STATIC_ROOT` is configured for `collectstatic`.
- `MEDIA_ROOT` and `MEDIA_URL` are defined for future Django media.
- HTTPS redirect, secure cookies, and HSTS are environment-controlled.

### Gunicorn

Added to `backend/requirements.txt` and configured through:

```text
deploy/systemd/netwatch-gunicorn.service.example
```

Gunicorn binds to `127.0.0.1:8000`; it is not directly exposed to the internet.

### React

Added:

```text
frontend/.env.production.example
```

Production API configuration is:

```env
VITE_API_BASE_URL=/api
```

The frontend is built with Vite and served by Nginx from `frontend/dist`.

### Nginx

Added:

```text
deploy/nginx/netwatch.conf.example
```

It serves the React SPA, Django static/media files, and proxies API/admin requests to Gunicorn.

### Redis

Added:

```text
deploy/redis/redis.conf.example
```

Redis is intended to bind only to localhost with protected mode enabled. Port 6379 must not be publicly exposed.

### Celery

Added systemd examples for:

- Celery worker
- Celery Beat scheduler

The existing five-second Beat schedule remains the source of monitoring dispatch timing.

### Process management

Systemd manages:

```text
netwatch-gunicorn.service
netwatch-celery-worker.service
netwatch-celery-beat.service
```

Nginx and Redis remain managed by their distro systemd services.

### Environment variables

The production environment template is maintained in:

```text
backend/.env.example
```

The real deployment environment belongs outside Git, preferably at:

```text
/etc/netwatch/netwatch.env
```

It must contain a real secret and production host/origin/HTTPS values.

### Smoke testing

Added:

```text
deploy/smoke-test.sh
```

It validates:

1. public Django health endpoint
2. frontend response
3. collected Django static files

Protected API access should additionally be verified with an administrator account through the deployed frontend.

## Production deployment sequence

1. Provision Linux server.
2. Install Nginx, Redis, Python, Node.js/npm, Git, and required build tools.
3. Clone the repository to `/srv/netwatch`.
4. Create `/srv/netwatch/venv` and install backend requirements.
5. Create `/etc/netwatch/netwatch.env` with production values.
6. Run Django migrations.
7. Run `collectstatic`.
8. Install Node dependencies and run frontend lint/build.
9. Install Nginx configuration.
10. Install systemd units.
11. Enable Gunicorn, Celery worker, Celery Beat, Redis, and Nginx.
12. Configure TLS at Nginx.
13. Re-run `python manage.py check --deploy`.
14. Run the deployment smoke test.
15. Verify login, device registration, monitoring, faults, history, notifications, and recovery from the production frontend.

## SQLite deployment requirements

SQLite is intentionally retained for this project deployment context.

The SQLite database requires a writable local filesystem for the service account. Backups must include:

```text
backend/db.sqlite3
backend/media/
```

The database should not be stored on an unsupported network filesystem.

## Production security requirements

Before exposing the system publicly:

- `DJANGO_DEBUG=False`
- real `DJANGO_SECRET_KEY`
- real `DJANGO_ALLOWED_HOSTS`
- HTTPS enabled
- `DJANGO_SECURE_SSL_REDIRECT=True`
- secure session cookie enabled
- secure CSRF cookie enabled
- HSTS configured after HTTPS is verified
- Redis restricted to localhost/private network
- Gunicorn restricted to localhost
- `/etc/netwatch/netwatch.env` permissions restricted
- no secrets committed to Git

## Validation matrix

| Area | Validation |
|---|---|
| Backend | `python manage.py check --deploy` |
| Database | `python manage.py migrate --noinput` |
| Static files | `python manage.py collectstatic --noinput` |
| Frontend | `npm run lint` and `npm run build` |
| Gunicorn | systemd service status + local API health |
| Redis | `systemctl status redis-server` |
| Celery | worker systemd status/logs |
| Beat | Beat systemd status/logs |
| Nginx | `nginx -t` |
| SPA | HTTPS `/` returns the frontend |
| API | HTTPS `/api/health/` succeeds |
| Auth | anonymous protected request returns 401; staff login succeeds |
| Monitoring | controlled monitored device produces records/fault lifecycle |

## Scope boundary

This phase prepares the repository and documents the production deployment path. Actual server provisioning, DNS, TLS certificate issuance, firewall configuration, and physical network-device validation must be performed on the target deployment environment.
