# Peek API

Image analysis API with computer vision capabilities. Processes images asynchronously to extract insights including dominant colors, quality metrics, face detection, text extraction (OCR), and scene classification.

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Tesseract OCR

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

**Layered Service Architecture:**
- API Layer: Flask endpoints (app/routes/api.py)
- Service Layer: Business logic (app/services/)
- Analyzer Layer: CV modules (app/analyzers/)
- Task Queue: Celery workers (tasks/celery_tasks.py)

**Data Flow:**
1. Image upload → validation → storage
2. Celery task triggered → CV pipeline processes image
3. Results stored in PostgreSQL → retrievable via API

**Analyzers:**
- ColorAnalyzer: K-means clustering for dominant colors
- QualityAnalyzer: Laplacian variance (sharpness), RMS contrast
- FaceDetector: Haar Cascades face detection
- TextExtractor: Tesseract OCR
- SceneDetector: HSV-based heuristic classification

See CLAUDE.md for detailed architecture documentation.

## Configuration

Environment variables (see .env.example):

```bash
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost:5432/peek_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216
```

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

## Deployment (Railway)

**Required Services:**
- PostgreSQL (database)
- Redis (message broker)
- Web service (Flask API)
- Worker service (Celery)

**Environment Variables:**
```bash
FLASK_ENV=production
SECRET_KEY=<generate-strong-key>
DATABASE_URL=<railway-postgres-url>
REDIS_URL=<railway-redis-url>
CELERY_BROKER_URL=<railway-redis-url>
CELERY_RESULT_BACKEND=<railway-redis-url>
CELERYD_POOL=prefork
CELERYD_CONCURRENCY=4
```

**Web Service Start Command:**
```bash
python3 run.py
```

**Worker Service Start Command:**
```bash
celery -A tasks.celery_tasks.celery worker --loglevel=info
```

See CLAUDE.md for detailed deployment configuration.
