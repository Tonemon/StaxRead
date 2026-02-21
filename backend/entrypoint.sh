#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Initialising Qdrant collection..."
python manage.py init_qdrant

echo "Starting application..."
exec "$@"
