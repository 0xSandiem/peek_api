# Deployment Guide

## Railway Deployment

### Environment Variables

Set these in Railway dashboard for production:

```bash
FLASK_ENV=production
SECRET_KEY=<generate-strong-secret-key>

DATABASE_URL=<railway-postgres-url>
REDIS_URL=<railway-redis-url>

CELERY_BROKER_URL=<railway-redis-url>
CELERY_RESULT_BACKEND=<railway-redis-url>

CELERYD_POOL=prefork
CELERYD_CONCURRENCY=4

UPLOAD_FOLDER=/app/uploads
MAX_FILE_SIZE=16777216
```

### Services Required

1. **PostgreSQL** - Database for images and insights
2. **Redis** - Message broker for Celery tasks
3. **Web Service** - Flask API (run.py)
4. **Worker Service** - Celery worker

### Railway Configuration

#### Web Service (Flask API)
```yaml
Build Command: pip install -r requirements.txt
Start Command: python3 run.py
```

#### Worker Service (Celery)
```yaml
Build Command: pip install -r requirements.txt
Start Command: celery -A tasks.celery_tasks.celery worker --loglevel=info
```

### Notes

- Production uses `prefork` pool for optimal performance on Linux
- Development (macOS) uses `solo` pool to avoid fork safety issues
- Concurrency defaults to 4 workers, adjust via CELERYD_CONCURRENCY
- Ensure uploads directory is persistent or use cloud storage (S3)

### Healthcheck Endpoint

```
GET /api/health
```

Returns `{"status": "ok"}` when API is ready.
