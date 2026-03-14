.PHONY: test lint format build check clean

test:
	pytest tests/ -v --tb=short

lint:
	ruff check call_use/ tests/
	ruff format --check call_use/ tests/

format:
	ruff format call_use/ tests/

build: clean
	python -m build
	twine check dist/*

check: lint test build

clean:
	rm -rf dist/ build/ *.egg-info
