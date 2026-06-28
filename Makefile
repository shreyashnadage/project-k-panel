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
	@echo "  make build-agent       Build agent exe with PyInstaller"
	@echo "  make build-service     Build Windows service exe"
	@echo "  make build-wizard      Build registration wizard exe"
	@echo "  make build-all         Build all three exes"
	@echo "  make build-installer   Build Inno Setup installer (requires build-all first)"
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
test: test-pipeline test-registration
	@echo "All active tests passed"

test-pipeline:
	python tests/test_full_pipeline.py

test-multicompany:
	python tests/test_multi_company.py

test-queue:
	python tests/test_offline_queue.py

test-registration:
	python tests/test_registration_service.py

test-all: test-pipeline test-multicompany test-queue test-registration
	@echo "Full test suite passed"

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
	pyinstaller TallySyncAgent.spec --clean --noconfirm
	@echo "Built: dist\TallySyncAgent.exe"

build-service:
	pyinstaller TallySyncService.spec --clean --noconfirm
	@echo "Built: dist\TallySyncService.exe"

build-wizard:
	pyinstaller RegistrationWizard.spec --clean --noconfirm
	@echo "Built: dist\registration_wizard.exe"

build-all: build-agent build-service build-wizard
	@echo "All executables built in dist/"

build-installer: build-all
	"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\TallySyncAgent.iss
	@echo "Installer built: installer\dist\installer\TallySyncAgent-Setup-0.5.0.exe"

# Cleanup
clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache .coverage htmlcov .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned build artifacts"
