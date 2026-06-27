.PHONY: help venv install install-dev test test-unit test-integration test-e2e lint format clean docs build phase0-verify

# Default target
help:
	@echo "Tally Sync Agent — Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Environment:"
	@echo "  make venv              Create virtual environment"
	@echo "  make install           Install runtime dependencies"
	@echo "  make install-dev       Install dev + runtime dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run all tests (unit + integration)"
	@echo "  make test-unit         Run unit tests only (fast, no Tally)"
	@echo "  make test-integration  Run integration tests (requires Tally)"
	@echo "  make test-e2e          Run e2e tests (requires deployed platform)"
	@echo "  make coverage          Run tests with coverage report"
	@echo "  make phase0-verify     Verify Phase 0 setup"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Run ruff + mypy"
	@echo "  make format            Format code with black"
	@echo "  make format-check      Check formatting without changes"
	@echo ""
	@echo "Build:"
	@echo "  make build-agent       Build agent executable with PyInstaller"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean             Remove build artifacts and cache"

# Environment setup
venv:
	python -m venv .venv
	@echo "✓ Virtual environment created. Activate with: .venv\Scripts\activate"

install:
	pip install -e ".[agent,platform]"

install-dev:
	pip install -e ".[agent,platform,dev]"

# Testing targets
test: test-unit test-integration
	@echo "✓ All tests passed"

test-unit:
	python -m pytest tests/unit -v --tb=short -m unit

test-integration:
	python -m pytest tests/integration -v --tb=short -m integration

test-e2e:
	python -m pytest tests/e2e -v --tb=short -m e2e

coverage:
	python -m pytest tests/unit tests/integration --cov=agent --cov=platform --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated in htmlcov/index.html"

phase0-verify:
	python phase0_verify.py

# Code quality
lint:
	ruff check agent platform tests
	mypy agent --ignore-missing-imports

format:
	black agent platform tests

format-check:
	black --check agent platform tests

# Build
build-agent:
	pyinstaller agent/main.py \
		--name TallySyncAgent \
		--onefile \
		--add-data "agent/extractor/tdml_templates;agent/extractor/tdml_templates" \
		--hidden-import win32api \
		--hidden-import win32con \
		--noconsole \
		--icon installer/icon.ico
	@echo "✓ Built: dist\TallySyncAgent.exe"

# Cleanup
clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .coverage htmlcov .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned build artifacts"
