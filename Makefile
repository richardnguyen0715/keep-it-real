.PHONY: setup lint test format

setup:
	./scripts/setup.sh

lint:
	ruff check .

test:
	pytest -q

format:
	ruff format .
