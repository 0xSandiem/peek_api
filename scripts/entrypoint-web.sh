#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! pg_isready -h postgres -U peek_user -d peek_db > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL started"

echo "Running database migrations..."
alembic upgrade head

echo "Starting Flask application..."
exec python3 run.py
