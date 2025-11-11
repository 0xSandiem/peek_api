# Peek API

Image analysis API with computer vision capabilities. Processes images asynchronously to extract insights including dominant colors, quality metrics, face detection, text extraction (OCR), and scene classification.

## System Architecture

![Peek System Architecture](./diagram.png)

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Tesseract OCR
- Cloudflare R2 account (for production image storage)

### Local Setup

```bash
# Clone repository
git clone https://github.com/0xSandiem/peek_api.git
cd peek_api

# Install dependencies
pip3 install -r requirements.txt

# Install Tesseract (macOS)
brew install tesseract

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Create database
createdb peek_db

# Run database migrations
alembic upgrade head

# Start services
brew services start postgresql@14
brew services start redis
```

### Running Services

**Terminal 1 - Flask API:**
```bash
python3 run.py
```

**Terminal 2 - Celery Worker:**
```bash
celery -A tasks.celery_tasks.celery worker --loglevel=info
```

API runs on `http://localhost:5001`

## API Endpoints

### Health Check
```bash
GET /api/health
```

**Response:**
```json
{"status": "ok"}
```

### Analyze Image
```bash
POST /api/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `image` (file, required): Image file (PNG, JPG, JPEG, GIF, BMP, WEBP)
- Max size: 16MB

**Example:**
```bash
curl -X POST http://localhost:5001/api/analyze \
  -F "image=@/path/to/image.jpg"
```

**Response:**
```json
{
  "id": 1,
  "status": "processing"
}
```

### Get Analysis Results
```bash
GET /api/results/:id
```

**Example:**
```bash
curl http://localhost:5001/api/results/1
```

**Response (processing):**
```json
{
  "id": 1,
  "status": "processing"
}
```

**Response (completed):**
```json
{
  "id": 1,
  "status": "completed",
  "insights": {
    "dominant_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"],
    "brightness": 128,
    "faces_detected": 2,
    "face_locations": [
      {"x": 100, "y": 150, "width": 80, "height": 80},
      {"x": 300, "y": 200, "width": 75, "height": 75}
    ],
    "text_found": true,
    "extracted_text": "Sample text from image",
    "word_count": 4,
    "sharpness_score": 67.23,
    "blur_level": "low",
    "contrast_score": 45.12,
    "quality_score": 58.54,
    "scene_type": "outdoor",
    "scene_confidence": 0.85
  }
}
```

### Get Original Image
```bash
GET /api/image/:id/original
```

**Example:**
```bash
curl http://localhost:5001/api/image/1/original --output image.jpg
```

Returns the original uploaded image.

### Get Annotated Image
```bash
GET /api/image/:id/annotated
```

**Example:**
```bash
curl http://localhost:5001/api/image/1/annotated --output annotated.jpg
```

Returns the image with face detection bounding boxes drawn.

## Architecture

### Layered Service Architecture

- **API Layer** (`app/routes/api.py`): Flask endpoints that handle HTTP requests and responses
- **Service Layer** (`app/services/`): Business logic orchestration
  - `image_service.py`: Coordinates the overall image analysis workflow
  - `cv_service.py`: Manages the computer vision processing pipeline
  - `storage_service.py`: Handles file upload/download and temporary storage
- **Analyzer Layer** (`app/analyzers/`): Specialized CV modules
  - `color_analyzer.py`: K-means clustering for dominant colors
  - `quality_analyzer.py`: Laplacian variance (sharpness), RMS contrast
  - `face_detector.py`: Haar Cascades face detection
  - `text_extractor.py`: Tesseract OCR
  - `scene_detector.py`: HSV-based heuristic classification
- **Task Queue** (`tasks/celery_tasks.py`): Asynchronous job processing with Celery

### Data Flow

1. Image upload → API endpoint validates → Storage service saves file
2. Celery task triggered → CV service orchestrates analysis pipeline
3. Each analyzer processes image independently → Results aggregated
4. Final insights stored in database (SQLAlchemy models in `app/models.py`)
5. Client retrieves results via API

## Configuration

Environment variables (see `.env.example`):

### Core Application
```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### Database & Cache
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/peek_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### File Storage (Local Development)
```bash
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216  # 16MB
```

### Cloudflare R2 Storage (Production)
```bash
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=peek
R2_REGION=auto
R2_PUBLIC_DOMAIN=  # Optional: Custom domain for public URLs
```

To set up Cloudflare R2:
1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Navigate to R2 Object Storage in your dashboard
3. Create a new bucket (e.g., "peek")
4. Generate API tokens with read/write permissions
5. Add credentials to your `.env` file

## Testing

```bash
# Run all tests
python3 -m pytest

# Run specific test file
python3 -m pytest tests/test_api.py -v

# Run with coverage
python3 -m pytest --cov=app --cov-report=html
```

Current test coverage: 63 tests across models, services, analyzers, validators, and API endpoints.

## Deployment

### Production Deployment (Railway + Cloudflare R2)

This guide covers deploying to Railway with Cloudflare R2 for scalable image storage.

#### Why Cloudflare R2?
- **Zero egress fees** (vs. AWS S3 charges $0.09/GB for data transfer)
- S3-compatible API (works with boto3)
- Global CDN distribution
- Cost-effective: ~$0.015/GB storage

#### Prerequisites
1. [Railway](https://railway.app) account
2. [Cloudflare](https://cloudflare.com) account with R2 enabled
3. GitHub repository connected

---

### Step 1: Set Up Cloudflare R2

1. **Log in to Cloudflare Dashboard**
   - Visit [dash.cloudflare.com](https://dash.cloudflare.com)

2. **Create R2 Bucket**
   - Navigate to **R2 Object Storage** in the sidebar
   - Click **Create bucket**
   - Enter bucket name: `peek` (or your preferred name)
   - Click **Create bucket**

3. **Generate API Tokens**
   - Go to **R2** → **Overview** → **Manage R2 API Tokens**
   - Click **Create API token**
   - Set permissions: **Object Read & Write**
   - Copy and save:
     - Access Key ID
     - Secret Access Key
     - Account ID (visible in the R2 URL)

4. **Optional: Configure Custom Domain**
   - In your bucket settings, go to **Settings** → **Public access**
   - Connect a custom domain for direct image URLs (no presigned URLs needed)
   - Example: `images.yourdomain.com`

---

### Step 2: Deploy to Railway

#### 2.1 Create Railway Project

1. **Sign up/Login** to [railway.app](https://railway.app)

2. **Create New Project**
   - Click **New Project**
   - Select **Deploy from GitHub repo**
   - Authorize Railway to access your repository
   - Select `peek_api` repository

3. **Add Database Services**
   - Click **+ New** → **Database** → **Add PostgreSQL**
   - Click **+ New** → **Database** → **Add Redis**

#### 2.2 Deploy Web Service

1. **Configure Web Service**
   - Railway should auto-detect your Python app
   - Deployment uses `railway.toml` configuration
   - Start command: `./scripts/entrypoint-web.sh`

2. **Set Environment Variables** (Web Service)

Click on your web service → **Variables** → **RAW Editor**:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-with: python -c 'import secrets; print(secrets.token_hex(32))'>
PORT=5000

# Database & Cache (use Railway's internal URLs)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=<your-cloudflare-account-id>
R2_ACCESS_KEY_ID=<your-r2-access-key-id>
R2_SECRET_ACCESS_KEY=<your-r2-secret-access-key>
R2_BUCKET_NAME=peek
R2_REGION=auto
R2_PUBLIC_DOMAIN=<optional-custom-domain>

# Worker Configuration
CELERYD_POOL=prefork
CELERYD_CONCURRENCY=4

# CORS (update with your frontend domain)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

**Note**: Railway automatically provides `${{Postgres.DATABASE_URL}}` and `${{Redis.REDIS_URL}}` variables when services are linked.

3. **Generate Production Secret Key**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

#### 2.3 Deploy Worker Service

1. **Add New Service**
   - Click **+ New** → **GitHub Repo** → Select same repository
   - This creates a second service for the Celery worker

2. **Configure Worker Start Command**
   - Go to service **Settings** → **Start Command**
   - Set to: `./scripts/entrypoint-worker.sh`
   - Or use: `celery -A tasks.celery_tasks.celery worker --loglevel=info`

3. **Set Environment Variables** (Worker Service)

Use the **same environment variables** as the web service. Copy from web service or set:

```bash
FLASK_ENV=production
SECRET_KEY=<same-as-web-service>
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
R2_ACCOUNT_ID=<your-cloudflare-account-id>
R2_ACCESS_KEY_ID=<your-r2-access-key-id>
R2_SECRET_ACCESS_KEY=<your-r2-secret-access-key>
R2_BUCKET_NAME=peek
R2_REGION=auto
CELERYD_POOL=prefork
CELERYD_CONCURRENCY=4
```

---

### Step 3: Verify Deployment

#### 3.1 Check Service Health

Wait for deployments to complete, then verify:

```bash
curl https://your-app-name.railway.app/api/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected"
}
```

#### 3.2 Test Image Upload

```bash
curl -X POST https://your-app-name.railway.app/api/analyze \
  -F "image=@/path/to/test-image.jpg"
```

Expected response:
```json
{
  "id": 1,
  "status": "processing",
  "public_url": "https://..."
}
```

#### 3.3 Monitor Logs

- **Web Service**: Railway Dashboard → Web Service → **Logs**
- **Worker Service**: Railway Dashboard → Worker Service → **Logs**

Look for:
- ✓ `R2 storage configured successfully`
- ✓ `PostgreSQL started`
- ✓ Database migrations completed

---

### Production Configuration Tips

#### Scaling

**Horizontal Scaling (Web Service)**:
- Railway: Settings → **Replicas** → Increase count
- All instances share the same R2 storage (no sync issues!)

**Vertical Scaling (Worker Service)**:
- Increase `CELERYD_CONCURRENCY` for more worker processes
- Monitor CPU/memory usage in Railway dashboard

#### Performance Optimization

1. **Database Connection Pooling**
   - Add to `DATABASE_URL`: `?pool_size=20&max_overflow=10`

2. **Redis Max Connections**
   - Railway's Redis handles this automatically

3. **R2 Caching**
   - Images are served with `Cache-Control: max-age=31536000` (1 year)
   - Use Cloudflare CDN for additional caching

#### Monitoring

**Application Logs**:
- Railway Dashboard provides built-in log aggregation
- Filter by service (web/worker) and severity level

**Celery Monitoring** (Optional):
Add Flower for real-time task monitoring:
```bash
# Add to requirements.txt
flower>=2.0.0

# Create new Railway service with start command:
celery -A tasks.celery_tasks.celery flower --port=5555
```

**Health Checks**:
- Railway automatically pings `/api/health` (configured in `railway.toml`)
- Set up external monitoring with UptimeRobot or Pingdom

#### Security Best Practices

1. **Rotate Secrets Regularly**
   - Generate new `SECRET_KEY` periodically
   - Rotate R2 API tokens every 90 days

2. **CORS Configuration**
   - Update `CORS_ALLOWED_ORIGINS` with your actual frontend domains
   - Never use `*` in production

3. **Database SSL**
   - Railway PostgreSQL includes SSL by default
   - Ensure `DATABASE_URL` uses `postgresql://` (not `postgres://`)

4. **Rate Limiting** (Recommended)
   ```bash
   pip install flask-limiter
   ```
   Add to `app/__init__.py` to prevent abuse

---

### Cost Estimation (Monthly)

**Railway Services**:
- Web Service (2 instances): $20-40
- Worker Service (1 instance): $10-20
- PostgreSQL (1GB): $10-15
- Redis (256MB): $5-10

**Cloudflare R2**:
- Storage (100GB): $1.50
- Class A operations (1M): $4.50
- Class B operations (10M): $0.36
- **Egress: $0** (zero fees!)

**Total Estimate**: $51-90/month

Compare to AWS S3: ~$130-150/month with egress fees

---

### Troubleshooting

#### "R2 credentials not configured" Error
- Verify all R2 environment variables are set in **both** web and worker services
- Check for typos in `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- Confirm bucket name matches `R2_BUCKET_NAME`

#### "Bucket does not exist" Error
- Verify bucket was created in Cloudflare R2 dashboard
- Check account ID matches your Cloudflare account
- Ensure API token has access to the bucket

#### Worker Not Processing Tasks
- Check worker service logs in Railway dashboard
- Verify `CELERY_BROKER_URL` is identical in web and worker services
- Ensure Redis service is running (check `/api/health`)

#### Images Not Uploading
- Check R2 API token permissions (need Object Read & Write)
- Review web service logs for R2 errors
- Test R2 credentials locally with a simple upload test

#### Database Migration Issues
- Web service runs `alembic upgrade head` on startup
- Check logs for migration errors
- Manually run migrations: `railway run alembic upgrade head`

---

### Alternative Deployment Options

#### Option 1: Docker Compose (Self-Hosted)

Use the included `docker-compose.yml` for self-hosted deployment:

```bash
# Set R2 credentials in .env
cp .env.example .env
# Edit .env with production values

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Option 2: AWS/GCP/Azure

Follow similar steps as Railway:
1. Deploy web service (Flask app)
2. Deploy worker service (Celery)
3. Set up managed PostgreSQL and Redis
4. Configure R2 environment variables
5. Set up load balancer/reverse proxy

---

### Support & Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Cloudflare R2 Docs**: [developers.cloudflare.com/r2](https://developers.cloudflare.com/r2)
- **Project Issues**: [github.com/yourusername/peek_api/issues](https://github.com/yourusername/peek_api/issues)
