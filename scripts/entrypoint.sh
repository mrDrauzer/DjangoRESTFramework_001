#!/bin/sh
set -e

echo "[entrypoint] Applying migrations..."
python manage.py migrate --noinput

# Optional: collect static (not strictly needed for DEBUG run)
# echo "[entrypoint] Collecting static..."
# python manage.py collectstatic --noinput

echo "[entrypoint] Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
