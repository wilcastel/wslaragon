# WSLaragon Makefile
# Common development tasks

.PHONY: help install install-dev test lint format clean run-tests check

# Colors
GREEN := $(shell tput setaf 2 2>/dev/null || echo "")
YELLOW := $(shell tput setaf 3 2>/dev/null || echo "")
BLUE := $(shell tput setaf 4 2>/dev/null || echo "")
RESET := $(shell tput sgr0 2>/dev/null || echo "")

help:
	@echo "$(BLUE)WSLaragon Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Installation:"
	@echo "  make install          Install package in development mode"
	@echo "  make install-dev      Install with dev dependencies"
	@echo ""
	@echo "$(GREEN)Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-cov        Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Code Quality:"
	@echo "  make lint            Run linters (ruff, black, isort)"
	@echo "  make format          Format code automatically"
	@echo "  make type-check      Run type checking (mypy)"
	@echo ""
	@echo "$(GREEN)Development:"
	@echo "  make clean           Remove cache and build files"
	@echo "  make check           Run all checks (lint + type + test)"
	@echo "  make pre-commit      Run pre-commit hooks"
	@echo ""
	@echo "$(GREEN)Running:"
	@echo "  make run             Run WSLaragon CLI"
	@echo "  make doctor          Run WSLaragon doctor command"

install:
	@echo "$(GREEN)Installing WSLaragon in development mode...$(RESET)"
	pip install -e .

install-dev:
	@echo "$(GREEN)Installing WSLaragon with dev dependencies...$(RESET)"
	pip install -e ".[dev]"

test:
	@echo "$(GREEN)Running tests...$(RESET)"
	pytest -v

test-unit:
	@echo "$(GREEN)Running unit tests...$(RESET)"
	pytest -v tests/unit/

test-cov:
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	pytest --cov=src --cov-report=html --cov-report=term-missing

lint:
	@echo "$(GREEN)Running linters...$(RESET)"
	@echo "Running ruff..."
	@ruff check src/ || true
	@echo "Running black check..."
	@black --check src/ || true
	@echo "Running isort check..."
	@isort --check-only src/ || true

format:
	@echo "$(GREEN)Formatting code...$(RESET)"
	ruff check src/ --fix
	black src/
	isort src/

type-check:
	@echo "$(GREEN)Running type checks...$(RESET)"
	mypy src/ || true

check: lint type-check test

clean:
	@echo "$(GREEN)Cleaning up...$(RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	rm -rf .coverage.coverage.xml

pre-commit:
	@echo "$(GREEN)Running pre-commit hooks...$(RESET)"
	pre-commit run --all-files

run:
	@echo "$(GREEN)Running WSLaragon CLI...$(RESET)"
	wslaragon --help

doctor:
	@echo "$(GREEN)Running WSLaragon doctor...$(RESET)"
	wslaragon doctor