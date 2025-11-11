#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Flask application..."
exec python3 run.py
