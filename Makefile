.PHONY: help install dev worker test test-watch lint format migrate migrate-create clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make dev            - Run Flask development server"
	@echo "  make worker         - Run Celery worker"
	@echo "  make test           - Run tests with coverage"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make lint           - Run all linters"
	@echo "  make format         - Auto-format all code"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make clean          - Remove caches and build artifacts"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"

install:
	pip install -r requirements.txt

dev:
	python run.py

worker:
	celery -A tasks.celery worker --loglevel=info

test:
	pytest --cov=app --cov-report=term-missing --cov-report=html -v

test-watch:
	pytest-watch -- --cov=app -v

lint:
	black --check app/ tests/ tasks/
	flake8 app/ tests/ tasks/ --max-line-length=88 --extend-ignore=E203,E266,E501,W503
	isort --check-only --profile black app/ tests/ tasks/

format:
	black app/ tests/ tasks/
	isort --profile black app/ tests/ tasks/

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf coverage.xml
	rm -rf .mypy_cache
	rm -rf uploads/*
	touch uploads/.gitkeep

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
