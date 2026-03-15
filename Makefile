.PHONY: test test-unit test-bdd test-integration lint format typecheck build check clean security docs docs-build

test:
	pytest tests/ -v --tb=short --cov=call_use --cov-report=term-missing --cov-fail-under=100

test-unit:
	pytest tests/ -v -m unit --tb=short

test-bdd:
	pytest tests/ -v -m bdd --tb=short

test-integration:
	pytest tests/ -v -m integration --tb=short

lint:
	ruff check call_use/ tests/
	ruff format --check call_use/ tests/

format:
	ruff format call_use/ tests/

typecheck:
	mypy call_use/ --ignore-missing-imports

security:
	bandit -r call_use/ -c pyproject.toml || true
	safety check --short-report || true

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
