.PHONY: setup lint test format

setup:
python -m pip install -U pip
python -m pip install ruff pytest

lint:
ruff check .

test:
pytest -q

format:
ruff format .
