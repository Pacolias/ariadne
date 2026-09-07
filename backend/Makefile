.PHONY: install seed dev test test-integration lint typecheck

VENV := .venv/bin

install:
	python3 -m venv .venv
	$(VENV)/pip install -e ".[dev]"

seed:
	$(VENV)/python scripts/seed_topology.py

dev:
	$(VENV)/uvicorn ariadne.api.main:app --reload

test:
	$(VENV)/pytest -m "not integration"

test-integration:
	$(VENV)/pytest -m integration

lint:
	$(VENV)/ruff check src tests scripts

typecheck:
	$(VENV)/mypy src
