#!/bin/sh
set -e

echo "[entrypoint.prod] Applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint.prod] Collecting static..."
python manage.py collectstatic --noinput

WORKERS=${GUNICORN_WORKERS:-3}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
BIND=${GUNICORN_BIND:-0.0.0.0:8000}

echo "[entrypoint.prod] Starting gunicorn on ${BIND} (workers=${WORKERS}, timeout=${TIMEOUT})"
exec gunicorn config.wsgi:application \
  --bind ${BIND} \
  --workers ${WORKERS} \
  --timeout ${TIMEOUT} \
  --access-logfile '-' \
  --error-logfile '-'
