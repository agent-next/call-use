.PHONY: test lint format typecheck build check clean

test:
	pytest tests/ -v --tb=short --cov=call_use --cov-report=term-missing --cov-fail-under=100

lint:
	ruff check call_use/ tests/
	ruff format --check call_use/ tests/

format:
	ruff format call_use/ tests/

typecheck:
	mypy call_use/ --ignore-missing-imports

build: clean
	python3 -m build
	python3 -m twine check dist/*

check: lint typecheck test build

clean:
	rm -rf dist/ build/ *.egg-info
