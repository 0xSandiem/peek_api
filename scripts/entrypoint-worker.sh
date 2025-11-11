#!/bin/bash
set -e

echo "Starting Celery worker..."
exec celery -A tasks.celery_tasks.celery worker --loglevel=info
