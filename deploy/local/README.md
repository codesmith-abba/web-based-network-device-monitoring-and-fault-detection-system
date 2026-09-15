# Local Nginx Deployment — Ubuntu + Windows

This directory contains local presentation-ready deployment templates for NetWatch.

The local architecture matches the production architecture:

```text
Browser
  |
  v
Nginx :80
  |---------------------> React frontend (`frontend/dist`)
  |
  +---- /api/ ----------> Gunicorn :8000 -> Django REST API
  |
  +---- /admin/ --------> Gunicorn :8000 -> Django admin
  |
  +---- /static/ -------> Django collected static files
  |
  +---- /media/ --------> Django media files

Django/Celery -> Redis :6379
Django -> SQLite
```

## Ubuntu

### 1. Install packages

```bash
sudo apt update
sudo apt install -y nginx redis-server python3-venv python3-pip
sudo systemctl enable --now nginx redis-server
```

### 2. Backend

From the repository root:

```bash
cd backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Create the local environment file:

```bash
sudo mkdir -p /etc/netwatch
sudo cp deploy/local/ubuntu/netwatch-local.env.example /etc/netwatch/netwatch.env
sudo nano /etc/netwatch/netwatch.env
```

Set a real `DJANGO_SECRET_KEY` before starting Django.

Create/update the local services from the examples in `deploy/local/ubuntu/systemd/`, replacing `/home/codesmithabba/Desktop/web-based-network-device-monitoring-and-fault-detection-system` if the repository is elsewhere.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now netwatch-gunicorn netwatch-celery-worker netwatch-celery-beat
```

### 3. Frontend

```bash
cd frontend
npm install
npm run build
```

### 4. Nginx

Copy `deploy/local/ubuntu/nginx/netwatch-local.conf.example` to `/etc/nginx/sites-available/netwatch-local` and update the repository path if necessary.

```bash
sudo ln -s /etc/nginx/sites-available/netwatch-local /etc/nginx/sites-enabled/netwatch-local
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Open:

```text
http://localhost
```

Admin:

```text
http://localhost/admin/
```

No HTTPS is required for this local presentation setup.

## Windows

Windows uses Nginx directly and runs Gunicorn/Celery from separate terminals. Windows does not use the Ubuntu systemd files.

For the simplest presentation setup, clone/copy the repository to:

```text
C:\netwatch
```

Then use `deploy/local/windows/nginx.conf.example`. If you use another directory, change the `root`, `alias`, and `WorkingDirectory` paths in the relevant files.

### 1. Install prerequisites

Install:

- Python 3.11 or 3.12
- Node.js LTS
- Redis for Windows through a supported Redis-compatible distribution
- Nginx for Windows

### 2. Backend

PowerShell:

```powershell
cd C:\netwatch\backend
py -3 -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Create `backend\.env` from the production example, but use the local Windows values described in `deploy/local/windows/netwatch-local.env.example`.

### 3. Frontend

```powershell
cd C:\netwatch\frontend
npm install
npm run build
```

### 4. Start Gunicorn

From `C:\netwatch\backend` with the virtual environment active:

```powershell
gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120
```

Keep this terminal open.

### 5. Start Celery worker

In another PowerShell window:

```powershell
cd C:\netwatch\backend
.\env\Scripts\Activate.ps1
celery -A backend worker --loglevel=INFO --concurrency=2
```

### 6. Start Celery Beat

In another PowerShell window:

```powershell
cd C:\netwatch\backend
.\env\Scripts\Activate.ps1
celery -A backend beat --loglevel=INFO
```

### 7. Start Nginx

Copy `deploy/local/windows/nginx.conf.example` to the Nginx `conf` directory as `nginx.conf` or include it from the main Nginx configuration.

Test:

```powershell
cd C:\nginx
.\nginx.exe -t
.\nginx.exe
```

Open:

```text
http://localhost
```

Admin:

```text
http://localhost/admin/
```

Stop Nginx with:

```powershell
.\nginx.exe -s quit
```

## Local smoke test

After Nginx, Gunicorn, Redis, and Celery are running:

1. Open `http://localhost`.
2. Log in with the Django admin/staff account.
3. Open the dashboard.
4. Register or inspect a device.
5. Confirm monitoring/history/fault/notification views load through `/api/`.
6. Open `http://localhost/admin/` to verify Django admin.

The browser should use the Nginx URL, not `http://127.0.0.1:8000` directly. This verifies the same reverse-proxy topology used for the presentation deployment.

## Important

- Do not commit real `.env` files or secrets.
- Local HTTP intentionally disables HTTPS-only settings such as SSL redirect and HSTS.
- The production Nginx template remains under `deploy/nginx/`.
- These files are for local demonstration/presentation deployment; production HTTPS still requires a real domain and TLS certificate.
