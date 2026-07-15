# Port Checker Makefile

.PHONY: all install install-dev test lint format clean build build-cli build-pyapp build-swiftapp run dev help

PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
SRC_DIR := src/portchecker
TEST_DIR := tests

# Default target
all: build

# Help
help:
	@echo "Port Checker - Available targets:"
	@echo ""
	@echo "  Setup:"
	@echo "    make install      - Install production dependencies"
	@echo "    make install-dev  - Install development dependencies"
	@echo ""
	@echo "  Development:"
	@echo "    make test         - Run tests"
	@echo "    make lint         - Run linters"
	@echo "    make format       - Format code"
	@echo "    make run          - Run CLI (default: scan, use ARGS= to pass args)"
	@echo "    make run ARGS=security     - Run security check"
	@echo "    make help-cli     - Show CLI help"
	@echo "    make dev          - Format and run"
	@echo ""
	@echo "  Building:"
	@echo "    make build        - Build everything (CLI + apps)"
	@echo "    make build-cli    - Build standalone CLI binary"
	@echo "    make build-pyapp  - Build Python fallback menu bar app"
	@echo "    make build-swiftapp - Build native macOS menu bar app"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make clean        - Clean build artifacts"
	@echo ""

# Virtual environment
$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip setuptools wheel

# Install production dependencies
install: $(VENV)
	$(VENV_BIN)/pip install -e .

# Install development dependencies
install-dev: $(VENV)
	$(VENV_BIN)/pip install -e ".[dev]"
	$(VENV_BIN)/pip install pyinstaller py2app

# Run tests
test:
	$(VENV_BIN)/pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing

# Run linters
lint:
	$(VENV_BIN)/ruff check $(SRC_DIR)
	$(VENV_BIN)/mypy $(SRC_DIR)

# Format code
format:
	$(VENV_BIN)/black $(SRC_DIR) $(TEST_DIR)
	$(VENV_BIN)/ruff check --fix $(SRC_DIR)

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Run CLI in development mode (defaults to 'scan', use ARGS= to override)
run:
	$(VENV_BIN)/python -m portchecker $(or $(ARGS),scan)

# Show CLI help
help-cli:
	$(VENV_BIN)/python -m portchecker --help

# Quick development cycle (format + run scan)
dev: format
	$(VENV_BIN)/python -m portchecker scan

# Build everything
build:
	./scripts/build.sh

# Build standalone CLI binary
build-cli: install-dev
	mkdir -p dist
	$(VENV_BIN)/pyinstaller \
		--onefile \
		--name portchecker \
		--distpath dist \
		--specpath build \
		--workpath build \
		--paths=src \
		--hidden-import=portchecker \
		--hidden-import=portchecker.cli \
		--hidden-import=portchecker.models \
		--hidden-import=portchecker.scanner \
		--hidden-import=portchecker.security \
		--hidden-import=portchecker.fingerprint \
		--hidden-import=portchecker.process_control \
		--hidden-import=portchecker.config \
		--collect-all=portchecker \
		--clean \
		portchecker_entry.py
	@echo "✓ CLI binary built at: dist/portchecker"

# Build Python menu bar app
build-pyapp: install-dev
	cd PortCheckerMenuBarPy && ../$(VENV_BIN)/python setup.py py2app
	cp -R "PortCheckerMenuBarPy/dist/Port Checker.app" "dist/Port Checker (Python).app"
	@echo "✓ Python menu bar app built at: dist/Port Checker (Python).app"

# Build Swift menu bar app (requires Xcode)
build-swiftapp:
	./script/build_and_run.sh --build
	@echo "✓ Native macOS app built at: dist/Port Checker.app"

# Install locally for testing
install-local: build-cli
	cp dist/portchecker /usr/local/bin/
	@echo "✓ Installed to /usr/local/bin/portchecker"

# Uninstall local installation
uninstall:
	rm -f /usr/local/bin/portchecker
	@echo "✓ Uninstalled from /usr/local/bin"
