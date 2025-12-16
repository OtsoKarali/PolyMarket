.PHONY: install test lint format setup-db help

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make setup-db     - Initialize database"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"

install:
	pip install -e ".[dev]"

setup-db:
	python scripts/setup_db.py

test:
	pytest tests/ -v

lint:
	ruff check src/ cli/ tests/
	mypy src/ cli/

format:
	black src/ cli/ tests/
	ruff check --fix src/ cli/ tests/

