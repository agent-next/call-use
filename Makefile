# Prefer the project venv for every tool invocation so `make setup`/`make check`
# never touch the host, conda, or user-site Python.
export PATH := $(CURDIR)/.venv/bin:$(PATH)

.PHONY: test test-unit test-bdd test-integration lint format typecheck build check clean security docs docs-build

test:
	pytest tests/ -v --tb=short --cov=call_use --cov-report=term-missing --cov-fail-under=100

test-unit:
	pytest tests/ -v -m unit --tb=short

test-bdd:
	pytest tests/ -v -m bdd --tb=short

test-integration:
	pytest tests/ -v -m integration --tb=short

.PHONY: setup
setup:
	@[ -n "$$VIRTUAL_ENV" ] || [ -d .venv ] || python3 -m venv .venv
	python3 -m pip install -e ".[dev]" ruff build twine

lint:
	ruff check call_use/ tests/
	ruff format --check call_use/ tests/

format:
	ruff format call_use/ tests/

typecheck:
	mypy call_use/ --ignore-missing-imports --check-untyped-defs

security:
	bandit -r call_use/ -c pyproject.toml -ll
	pip-audit --strict

build: clean
	python3 -m build
	python3 -m twine check dist/*

check: lint typecheck test build

clean:
	rm -rf dist/ build/ *.egg-info

docs:
	mkdocs serve

docs-build:
	mkdocs build
