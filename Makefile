# Tunisia Intelligence RSS Scraper - Development Makefile
# Use this file to run common development tasks

.PHONY: help install test lint format clean setup run check-config

# Default target
help:
	@echo "Tunisia Intelligence RSS Scraper - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup          - Run initial project setup"
	@echo "  install        - Install dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-watch     - Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black"
	@echo "  type-check     - Run type checking with mypy"
	@echo ""
	@echo "Database:"
	@echo "  check-schema   - Check database schema"
	@echo "  check-config   - Validate configuration"
	@echo ""
	@echo "Running:"
	@echo "  run            - Run the RSS loader"
	@echo "  run-single     - Test single extractor (specify URL=...)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean up generated files"
	@echo "  clean-cache    - Clean Python cache files"
	@echo "  clean-logs     - Clean log files"

# Setup and Installation
setup:
	@echo "🚀 Setting up Tunisia Intelligence RSS Scraper..."
	python setup.py

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install black mypy flake8 isort pre-commit

# Testing
test:
	@echo "🧪 Running all tests..."
	pytest

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -m integration

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-watch:
	@echo "🧪 Running tests in watch mode..."
	pytest-watch

# Code Quality
lint:
	@echo "🔍 Running linting checks..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "🎨 Formatting code..."
	black .
	isort .

type-check:
	@echo "🔍 Running type checks..."
	mypy . --ignore-missing-imports

# Database and Configuration
check-schema:
	@echo "🗄️ Checking database schema..."
	python check_schema.py

check-config:
	@echo "⚙️ Validating configuration..."
	python -c "from config.settings import get_settings; settings = get_settings(); print('✅ Configuration is valid')"

health-check:
	@echo "🏥 Running system health check..."
	python health_check.py

integration-test:
	@echo "🧪 Running integration tests..."
	python integration_test.py

# Running
run:
	@echo "🚀 Running RSS loader..."
	python rss_loader.py

run-single:
	@echo "🚀 Testing single extractor..."
	@if [ -z "$(URL)" ]; then \
		echo "❌ Please specify URL=<rss-url>"; \
		echo "Example: make run-single URL=https://nawaat.org/feed/"; \
	else \
		python main.py --url $(URL) --output json; \
	fi

# Maintenance
clean: clean-cache clean-logs
	@echo "🧹 Cleaning up..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

clean-cache:
	@echo "🧹 Cleaning Python cache..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-logs:
	@echo "🧹 Cleaning log files..."
	rm -f *.log
	rm -rf logs/

# Development workflow
dev-setup: setup install-dev
	@echo "🎉 Development environment ready!"
	@echo "Next steps:"
	@echo "1. Edit .env file with your configuration"
	@echo "2. Run: make check-config"
	@echo "3. Run: make test"
	@echo "4. Run: make run"

# CI/CD targets
ci-test: install test lint type-check
	@echo "✅ All CI checks passed!"

# Docker targets (if using Docker)
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t tunisia-intelligence .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run --env-file .env tunisia-intelligence

# Security checks
security-check:
	@echo "🔒 Running security checks..."
	pip install safety bandit
	safety check
	bandit -r . -x tests/

# Documentation
docs:
	@echo "📚 Generating documentation..."
	pip install sphinx sphinx-rtd-theme
	sphinx-build -b html docs/ docs/_build/

# Performance profiling
profile:
	@echo "⚡ Running performance profiling..."
	python performance_profiler.py --mode full

profile-extractor:
	@echo "⚡ Running extractor profiling..."
	@if [ -z "$(URL)" ]; then \
		echo "❌ Please specify URL=<rss-url>"; \
		echo "Example: make profile-extractor URL=https://nawaat.org/feed/"; \
	else \
		python performance_profiler.py --mode extractor --url $(URL); \
	fi
