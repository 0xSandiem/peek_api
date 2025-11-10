# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Image Insights API** built with Flask that provides computer vision analysis capabilities for images. The API processes images asynchronously using Celery and returns various insights including color analysis, face detection, text extraction (OCR), quality metrics, and scene classification.

## Architecture

The application follows a **layered service architecture**:

1. **API Layer** (`app/routes/api.py`): Flask endpoints that handle HTTP requests and responses
2. **Service Layer** (`app/services/`): Business logic orchestration
   - `image_service.py`: Coordinates the overall image analysis workflow
   - `cv_service.py`: Manages the computer vision processing pipeline
   - `storage_service.py`: Handles file upload/download and temporary storage
3. **Analyzer Layer** (`app/analyzers/`): Specialized CV modules that perform specific analyses
   - Each analyzer is independent and can be composed into the CV pipeline
   - Analyzers: color, face detection, OCR, quality metrics, scene classification
4. **Task Queue** (`tasks/celery_tasks.py`): Asynchronous job processing with Celery
   - Image processing is handled asynchronously to avoid blocking API requests
   - Results are stored and can be retrieved via polling or webhooks

## Key Design Patterns

- **Service Pattern**: Business logic is separated from API routes into service modules
- **Strategy Pattern**: Different analyzers implement specific analysis strategies
- **Async Processing**: Long-running CV operations are handled by Celery workers
- **Factory Pattern**: Flask app is created via application factory in `app/__init__.py`

## Data Flow

1. Image upload → API endpoint validates → Storage service saves file
2. Celery task triggered → CV service orchestrates analysis pipeline
3. Each analyzer processes image independently → Results aggregated
4. Final insights stored in database (SQLAlchemy models in `app/models.py`)
5. Client retrieves results via API

## Configuration

- `config.py`: Central configuration management
- `.env.example`: Template for environment variables (database URL, Redis, storage paths, API keys for external CV services)
- Configuration should be environment-aware (dev/staging/prod)

## Deployment Configuration

**Environment-Specific Celery Pool:**
- Development (macOS): Uses `solo` pool to avoid fork safety issues with OpenCV/Tesseract
- Production (Linux/Railway): Uses `prefork` pool with 4 workers for optimal performance

**Railway Environment Variables:**
```
FLASK_ENV=production
DATABASE_URL=<postgres-url>
REDIS_URL=<redis-url>
CELERY_BROKER_URL=<redis-url>
CELERY_RESULT_BACKEND=<redis-url>
CELERYD_POOL=prefork
CELERYD_CONCURRENCY=4
```

**Services:** PostgreSQL (database), Redis (broker), Flask API (web), Celery worker (background processing)

## Development Workflow

Since this is a new project structure with placeholder files, implementation will require:

1. Setting up Flask app factory in `app/__init__.py`
2. Defining database models in `app/models.py` for storing analysis results
3. Implementing each analyzer independently before integrating into the pipeline
4. Configuring Celery broker (Redis/RabbitMQ) in `config.py`
5. Creating Docker multi-stage build for API server + Celery workers

## File Organization

- `uploads/`: Temporary local storage for development (use cloud storage in production)
- `app/utils/validators.py`: Input validation for image formats, file sizes, etc.
- `app/utils/helpers.py`: Common utilities shared across services/analyzers
- `tests/test_api.py`: API integration tests (will need unit tests for analyzers too)

## Code Style Standards

**No emojis** - Never use emojis in code, documentation, commit messages, or PR descriptions

**No AI comments** - Do not add typical AI-style comments (e.g., method descriptions, process explanations)

**Logging** - Ask for permission before adding logging statements (e.g., `print()`, `logger.debug()`)

**Documentation** - Do not create unnecessary `.md` files (DEPLOYMENT.md, CONTRIBUTING.md, etc.). Always ask before creating any documentation files. Keep all deployment, setup, and contribution info in README.md or CLAUDE.md only

## Git Workflow

**Branching**: This project uses **Gitflow**
- `main` branch for production releases
- `develop` branch for integration
- Feature branches: `feature/feature-name`
- Release branches: `release/x.y.z`
- Hotfix branches: `hotfix/issue-description`

## Commit Message Format

Format: `type(scope): message`

- **Single line**, imperative tone
- **Never reference AI tools** (e.g., "with Claude Code", "AI-generated")
- Keep messages short and descriptive

Examples:
```
feat(auth): add device code flow for CLI authentication
fix(billing): handle subscription cancellation edge case
docs(claude): update project overview with SaaS features
test(auth): add tests for password strength validation
refactor(api): consolidate error handling in auth routes
chore(deps): update Prisma to latest version
perf(analyzer): optimize image processing performance
style(api): adjust response formatting
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `style`
