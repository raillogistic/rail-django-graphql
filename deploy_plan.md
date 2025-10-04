# Deployment Plan: Environment-Driven, Docker-Orchestrated GraphQL Stack

This plan defines the technical steps and unchecked to-dos to extract all deployment configuration into environment files, make the Django boilerplate production-ready, and deliver a complete Docker-based setup: Django (ASGI), PostgreSQL, Redis, Nginx, and automated backups for DB and media.

## Architecture Overview

```
+----------------------+        +-------------------+        +------------------+
|      Clients         |  --->  |      Nginx        |  --->  |   Django (ASGI)  |
|  Browser/Apps        |        |  static/media     |        |  daphne (ASGI)   |
|                      |        |  reverse proxy    |        |  /graphql        |
+----------------------+        +-------------------+        +------------------+
                                      |                              |
                                      |                              |
                         +---------------------+          +-------------------+
                         |     PostgreSQL      |          |       Redis       |
                         |   persistent volume |          |   cache/tasks     |
                         +---------------------+          +-------------------+
                                      |
                                      |
                         +---------------------+
                         |  Backup Jobs (cron) |
                         |   pg_dump + media   |
                         +---------------------+
```

## Guiding Principles

- Single source of truth: all config comes from `.env` files (no hardcoded values in `settings.py`).
- Twelve-Factor alignment: environment-driven, logs to stdout, stateless app container.
- Production readiness: secure defaults, idempotent deployments, backups, and observability hooks.

---

## Phase 1 — Environment Consolidation (django-environ)

[x] Install and configure `django-environ` in Django boilerplate
- [x] Add dependency to requirements (base/prod): `django-environ`
- [x] Initialize `environ.Env()` in `config/settings/__init__.py` or equivalent
- [x] Load `.env` via `Env.read_env()` (conditionally for dev)

[x] Refactor `settings.py` to read only from env (no hardcoded values)
- [x] `SECRET_KEY` from env (`DJANGO_SECRET_KEY`)
- [x] `DEBUG` from env (`DJANGO_DEBUG`)
- [x] `ALLOWED_HOSTS` from env (`DJANGO_ALLOWED_HOSTS` comma-separated)
- [x] `DATABASE_URL` via `environ.Env.db()`
- [x] `REDIS_URL` via `environ.Env()` (cache backend / task broker)
- [x] `TIME_ZONE`, `LANGUAGE_CODE` from env
- [x] `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
- [x] `STATIC_URL`, `STATIC_ROOT`, `MEDIA_URL`, `MEDIA_ROOT` from env
- [x] `LOG_LEVEL`, log configuration mapped to env
- [x] Optional email settings (`EMAIL_URL` or SMTP vars)

[x] Create `.env.prod` fully documented and grouped by purpose
- [x] Add all variables in groups: Django, DB, Redis, Storage, Nginx, Security, Backups
- [x] Document each variable with comments and defaults guidance
- [x] Include example values, note sensitive secrets not committed

[x] Create `.env.example` for developers
- [x] Mirror `.env.prod` structure with safe example values
- [x] Comments explaining each variable

---

## Phase 2 — Dockerization and Orchestration

[ ] Create `Dockerfile` for Django app
- [ ] Base image: `python:3.x-slim`
- [ ] Install build deps and system libs (psycopg2, libpq, etc.)
- [ ] Copy project, install Python deps via `pip`
- [ ] Set working directory and `PYTHONUNBUFFERED=1`
- [ ] Entrypoint runs migrations, collectstatic, then ASGI server
- [ ] ASGI server: `daphne -b 0.0.0.0 -p 8000 config.asgi:application` (uvicorn optional for dev)

[ ] Create `docker-compose.yml` (development baseline)
- [ ] Services: `web` (Django), `db` (Postgres), `redis`, `nginx`
- [ ] Volumes: `postgres_data`, `media`, `static`, `nginx_conf`
- [ ] Env files: `.env` (dev) loaded into services
- [ ] Bind mounts for live dev (optional)

[ ] Create `docker-compose.prod.yml` (production overrides)
- [ ] Use `.env.prod` for secret and production values
- [ ] Configure resource limits and restart policies
- [ ] Add `backup` service (cron-based) for DB and media backups
- [ ] Ensure static files served by Nginx from `static` volume

[ ] Nginx configuration
- [ ] Compose a `nginx.conf` with:
  - [ ] `location /static/` and `/media/` served from volumes
  - [ ] `location /` and `/graphql` proxied to `web:8000`
  - [ ] Set headers and timeouts; gzip for text assets
  - [ ] Optional TLS termination (mount certs via volumes)

[ ] Volume management
- [ ] `postgres_data` for DB persistence
- [ ] `media` for file uploads
- [ ] `static` populated by `collectstatic`
- [ ] `backups` for DB and media backups retention

[ ] Environment separation
- [ ] Distinct `.env` and `.env.prod`
- [ ] Compose profiles or separate files to target dev vs prod
- [ ] Different cache TTLs, `DEBUG`, logging, and security settings

---

## Phase 3 — Backups and Maintenance

[ ] Automatic PostgreSQL backups
- [ ] Implement `backup` container with `cron` and `pg_dump` commands
- [ ] Read `DATABASE_URL`, `DB_BACKUPS_DIR`, retention policy from env
- [ ] Timestamped dumps; gzip compression
- [ ] Rotation policy (e.g., keep N daily, M weekly)

[ ] Media files backup
- [ ] Cron job to sync `MEDIA_ROOT` to `MEDIA_BACKUP_TARGET`
- [ ] Use `rsync` (Linux) or `rclone` for remote destinations (S3/NAS)
- [ ] Configurable schedule via env (`MEDIA_BACKUP_CRON`)

[ ] Restore procedures
- [ ] Document restore steps: `psql`/`pg_restore` and media re-sync
- [ ] Provide scripts for restore (`scripts/restore_db.sh`, `scripts/restore_media.sh`)

---

## Phase 4 — Django App Readiness

[ ] Startup scripts and lifecycle
- [ ] `entrypoint.sh` to run: `python manage.py migrate` → `python manage.py collectstatic --noinput` → start ASGI
- [ ] Health endpoints and readiness probe
- [ ] Proper logging to stdout/stderr

[ ] GraphQL functionality
- [ ] Confirm `/graphql` served via ASGI
- [ ] Validate schema loading and mutation/query endpoints
- [ ] Ensure `ALLOWED_HOSTS`/CSRF are correctly configured for reverse proxy

[ ] Static and media handling
- [ ] Verify `STATIC_ROOT` and `MEDIA_ROOT` mounted to Nginx
- [ ] `collectstatic` on deploy populates static volume
- [ ] Media write path persists in `media` volume

---

## Environment Variables — Grouped (to be documented in `.env.prod` and `.env.example`)

### Django Settings
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (true/false)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DJANGO_TIME_ZONE`
- `DJANGO_LANGUAGE_CODE`
- `CSRF_TRUSTED_ORIGINS` (comma-separated)
- `LOG_LEVEL` (INFO/DEBUG/WARN)

### Database
- `DATABASE_URL` (e.g., `postgres://user:pass@db:5432/app_db`)
- `DB_BACKUPS_DIR` (e.g., `/backups/db`)
- `DB_BACKUP_CRON` (e.g., `0 2 * * *`)
- `DB_BACKUP_RETENTION_DAYS` (e.g., `7`)

### Cache / Tasks
- `REDIS_URL` (e.g., `redis://redis:6379/0`)
- `CACHE_TIMEOUT_SECONDS`

### Storage
- `STATIC_URL`, `STATIC_ROOT`
- `MEDIA_URL`, `MEDIA_ROOT`
- `MEDIA_BACKUP_TARGET` (e.g., `rsync://backup-server/share/media`)
- `MEDIA_BACKUP_CRON` (e.g., `0 3 * * *`)

### Nginx / Networking
- `SERVER_NAME` (e.g., `example.com`)
- `USE_TLS` (true/false)
- `TLS_CERT_PATH`, `TLS_KEY_PATH`

### Optional Email
- `EMAIL_URL` (or `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_USE_TLS`)

---

## Deliverables Checklist (Expected Output)

[x] `.env.prod` fully documented and grouped by purpose
[x] Updated `settings.py` using `django-environ` (env-only)
[ ] `Dockerfile` for Django ASGI app
[ ] `docker-compose.yml` for dev (Django + Postgres + Redis + Nginx)
[ ] `docker-compose.prod.yml` with backup jobs and prod overrides
[ ] `cron`/bash scripts for automated DB and media backups to network backup server
[ ] `deployment instructions.md` with build/run/backup/restore steps
[ ] One script to run the whole system (e.g., `scripts/deploy.sh`)

---

## High-Level Implementation Steps

[x] Create `.env.example` and `.env.prod` with documented variables
[x] Integrate `django-environ` and refactor settings to read env only
[ ] Implement Django `entrypoint.sh` (migrate, collectstatic, run ASGI)
[ ] Write `Dockerfile` for Django app
[ ] Compose base stack in `docker-compose.yml`
[ ] Add production overrides `docker-compose.prod.yml`
[ ] Author `nginx.conf` and volumes for static/media
[ ] Implement `backup` service with cron jobs (DB + media)
[ ] Provide `scripts/deploy.sh` and `deployment instructions.md`
[ ] Smoke test: migrations, static collection, and `/graphql` availability

---

## Risks and Mitigations

- Secret management: `.env` files must be protected; consider Docker secrets/host-level perms.
- Backup integrity: verify restore paths regularly; automate retention and checksum validation.
- Volume persistence: ensure correct mounts and host paths; avoid accidental deletion.
- TLS termination: if Nginx handles TLS, confirm cert renewal procedure (e.g., certbot container).
- Resource contention: size Postgres and Redis appropriately; set CPU/memory limits in prod compose.
- Observability: add minimal logging and optional metrics endpoints; plan for error alerts.

---

## Acceptance Criteria

- All configuration values read from `.env` files only.
- Compose stack runs end-to-end in dev and prod with documented steps.
- Backups run on schedule and restore successfully.
- Static files served by Nginx; media persisted and backed up.
- GraphQL endpoints (`/graphql`) reachable and functional.