#!/usr/bin/env bash
set -euo pipefail

# Default to ecommerce.settings if not provided
: "${DJANGO_SETTINGS_MODULE:=ecommerce.settings}"
export DJANGO_SETTINGS_MODULE

echo "[entrypoint] Applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout ${GUNICORN_TIMEOUT:-120}

