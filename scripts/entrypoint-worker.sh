#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! pg_isready -h postgres -U peek_user -d peek_db > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL started"

echo "Starting Celery worker..."
exec celery -A tasks.celery_tasks.celery worker --loglevel=info
