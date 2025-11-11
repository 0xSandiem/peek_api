#!/bin/bash
set -e

echo "Starting Flask application..."
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "REDIS_URL: ${REDIS_URL:0:30}..."
echo "R2_ACCOUNT_ID: ${R2_ACCOUNT_ID:0:10}..."

echo "Running database migrations..."
alembic upgrade head || echo "Migration failed, continuing..."

echo "Starting Flask app on port $PORT with gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - run:app
