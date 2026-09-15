# Production Deployment

This project deploys as a single-origin web application on Linux:

```text
Browser
  │ HTTPS
  ▼
Nginx
  ├── React static files
  ├── /static/ and /media/
  └── /api/ and /admin/
          │ HTTP on localhost
          ▼
      Gunicorn → Django WSGI
          │
          ├── SQLite
          └── Celery → Redis
                    ▲
                    └── Celery Beat
```

The current backend exposes a WSGI application (`backend.wsgi:application`), so this deployment uses Gunicorn WSGI rather than introducing an ASGI server.

## 1. Server layout

The examples use:

```text
/srv/netwatch/
├── backend/
├── frontend/
└── venv/
```

The repository should be checked out at `/srv/netwatch` and the Python virtual environment should be `/srv/netwatch/venv`.

## 2. System packages

Install the Linux packages appropriate for your distribution. On Debian/Ubuntu, the required services are:

```bash
sudo apt update
sudo apt install -y nginx redis-server python3 python3-venv python3-pip git curl
```

Enable Redis and Nginx:

```bash
sudo systemctl enable --now redis-server
sudo systemctl enable --now nginx
```

Redis is intended to remain bound to localhost for this deployment. Do not expose port 6379 publicly.

## 3. Application checkout and Python environment

```bash
sudo mkdir -p /srv/netwatch
sudo chown "$USER":"$USER" /srv/netwatch
cd /srv/netwatch
git clone <repository-url> .
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## 4. Production environment

Create the protected environment file:

```bash
sudo mkdir -p /etc/netwatch
sudo cp backend/.env.example /etc/netwatch/netwatch.env
sudo nano /etc/netwatch/netwatch.env
sudo chmod 600 /etc/netwatch/netwatch.env
```

Set at minimum:

```env
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
SQLITE_DB_PATH=/srv/netwatch/backend/db.sqlite3
DJANGO_STATIC_ROOT=/srv/netwatch/backend/staticfiles
DJANGO_MEDIA_ROOT=/srv/netwatch/backend/media
CORS_ALLOWED_ORIGINS=https://example.com
CSRF_TRUSTED_ORIGINS=https://example.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

Generate the secret without storing it in the repository:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

## 5. Django preparation

```bash
cd /srv/netwatch/backend
source /srv/netwatch/venv/bin/activate
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

`check --deploy` should be run after production environment variables are loaded. The deployment values above enable HTTPS redirect and HSTS.

SQLite is the documented deployment database for this project. Back up the database file and media directory regularly. SQLite should stay on local storage; do not place its database file on an unsupported network filesystem.

## 6. Frontend build

The frontend uses Vite and the production API path is same-origin:

```bash
cd /srv/netwatch/frontend
printf 'VITE_API_BASE_URL=/api\n' > .env.production
npm install
npm run lint
npm run build
```

The repository currently does not commit a frontend lockfile, so `npm install` is used rather than `npm ci`. Once a lockfile is intentionally committed, the deployment can switch to `npm ci` for deterministic installs.

The resulting `frontend/dist/` directory is served directly by Nginx.

Do not put secrets in Vite environment variables. Values beginning with `VITE_` are bundled into browser JavaScript.

## 7. Static and media files

Django static assets are collected to:

```text
/srv/netwatch/backend/staticfiles/
```

Nginx serves them directly at `/static/`.

The application currently has no user-upload workflow that requires a media storage service. The deployment nevertheless defines `/media/` and `MEDIA_ROOT` so future Django media can be served from the same controlled location without changing the deployment contract.

## 8. Gunicorn

The backend is WSGI-based. Use:

```bash
/srv/netwatch/venv/bin/gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
```

Install the example unit:

```bash
sudo cp deploy/systemd/netwatch-gunicorn.service.example /etc/systemd/system/netwatch-gunicorn.service
```

## 9. Celery worker and Beat

Install the example units:

```bash
sudo cp deploy/systemd/netwatch-celery-worker.service.example /etc/systemd/system/netwatch-celery-worker.service
sudo cp deploy/systemd/netwatch-celery-beat.service.example /etc/systemd/system/netwatch-celery-beat.service
sudo mkdir -p /var/lib/netwatch
sudo chown www-data:www-data /var/lib/netwatch
```

The worker executes monitoring jobs. Beat dispatches due monitoring work every five seconds, matching the existing Django Celery schedule.

## 10. Application file permissions

Gunicorn and Celery run as `www-data`. Give that user write access only where the application needs it:

```bash
sudo mkdir -p /srv/netwatch/backend/media /srv/netwatch/backend/staticfiles
sudo chown -R www-data:www-data /srv/netwatch/backend/media
sudo chown www-data:www-data /srv/netwatch/backend/db.sqlite3
```

If the database does not exist yet, run migrations first and then apply the ownership command.

Keep source code and environment files non-writable by the service user where practical.

## 11. Nginx

Copy the example configuration:

```bash
sudo cp deploy/nginx/netwatch.conf.example /etc/nginx/sites-available/netwatch
sudo nano /etc/nginx/sites-available/netwatch
sudo ln -s /etc/nginx/sites-available/netwatch /etc/nginx/sites-enabled/netwatch
sudo nginx -t
sudo systemctl reload nginx
```

The Nginx configuration:

- serves React from `frontend/dist`
- serves Django static files from `backend/staticfiles`
- proxies `/api/` to Gunicorn
- proxies `/admin/` to Gunicorn
- supports React client-side routes through `/index.html`
- forwards the original host and protocol to Django

## 12. HTTPS

The example Nginx file starts as an HTTP virtual host so it can be installed before TLS configuration. Before public production traffic:

1. Obtain a trusted TLS certificate for the real domain.
2. Configure Nginx to listen on HTTPS.
3. Redirect HTTP to HTTPS at Nginx.
4. Keep `DJANGO_SECURE_SSL_REDIRECT=True`.
5. Keep secure cookies enabled.
6. Enable HSTS only after HTTPS is confirmed across the intended domain scope.
7. Run `python manage.py check --deploy` again.

The API is then securely communicated over the same HTTPS origin as the React application; the browser calls `/api`, and Nginx proxies that request to localhost.

## 13. Start services

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now netwatch-gunicorn
sudo systemctl enable --now netwatch-celery-worker
sudo systemctl enable --now netwatch-celery-beat
```

Check:

```bash
sudo systemctl status netwatch-gunicorn
sudo systemctl status netwatch-celery-worker
sudo systemctl status netwatch-celery-beat
sudo systemctl status redis-server
sudo systemctl status nginx
```

Logs:

```bash
sudo journalctl -u netwatch-gunicorn -f
sudo journalctl -u netwatch-celery-worker -f
sudo journalctl -u netwatch-celery-beat -f
```

## 14. Deployment smoke test

Make the script executable once:

```bash
chmod +x deploy/smoke-test.sh
```

For a local HTTP verification:

```bash
deploy/smoke-test.sh http://127.0.0.1
```

For the public deployment:

```bash
deploy/smoke-test.sh https://example.com
```

The smoke test verifies the frontend, public Django health endpoint, and a collected Django static asset.

## 15. Manual API smoke tests

Health:

```bash
curl --fail https://example.com/api/health/
```

Protected API should reject anonymous access:

```bash
curl -i https://example.com/api/devices/
```

Expected result: `401 Unauthorized`.

Authentication and device/monitoring workflows should then be verified through the deployed frontend using a staff administrator account.

## 16. Release procedure

For an application update:

```bash
cd /srv/netwatch
git pull --ff-only
source /srv/netwatch/venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
cd ../frontend
npm install
npm run lint
npm run build
sudo systemctl restart netwatch-gunicorn
sudo systemctl restart netwatch-celery-worker
sudo systemctl restart netwatch-celery-beat
```

Then run the smoke test and inspect service logs.

## 17. Backup requirements

At minimum, back up:

```text
/srv/netwatch/backend/db.sqlite3
/srv/netwatch/backend/media/
/etc/netwatch/netwatch.env
```

The environment file contains the Django secret and Redis configuration and must be protected accordingly.
