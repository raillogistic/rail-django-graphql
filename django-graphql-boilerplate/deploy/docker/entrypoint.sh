#!/usr/bin/env sh
set -e

echo "[entrypoint] Starting container initialization..."

# Ensure settings module is set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}

echo "[entrypoint] Django settings: $DJANGO_SETTINGS_MODULE"

echo "[entrypoint] Applying database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

PORT=${PORT:-8000}
echo "[entrypoint] Launching Daphne on 0.0.0.0:${PORT}..."
exec daphne -b 0.0.0.0 -p "$PORT" config.asgi:application