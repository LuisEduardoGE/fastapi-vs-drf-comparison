PYTHON ?= python
FASTAPI_PORT ?= 8000
DRF_PORT ?= 8001

.DEFAULT_GOAL := help
.PHONY: help install run-fastapi migrate-drf run-drf test test-fastapi test-drf lint clean

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

install: ## Install both sub-projects plus pytest, httpx and ruff
	$(PYTHON) -m pip install -r requirements-dev.txt

run-fastapi: ## Start the FastAPI app (FASTAPI_PORT=8000 by default)
	cd fastapi_project && $(PYTHON) -m uvicorn app.main:app --reload --port $(FASTAPI_PORT)

migrate-drf: ## Apply the Django migrations (creates drf_project/db.sqlite3)
	cd drf_project && $(PYTHON) manage.py migrate

run-drf: migrate-drf ## Start the DRF app (DRF_PORT=8001 by default)
	cd drf_project && $(PYTHON) manage.py runserver $(DRF_PORT)

test: test-fastapi test-drf ## Run both test suites

test-fastapi: ## pytest for the FastAPI project (in-memory SQLite)
	cd fastapi_project && $(PYTHON) -m pytest -q

test-drf: ## Django test runner for the DRF project (throwaway SQLite test DB)
	cd drf_project && $(PYTHON) manage.py test

lint: ## Ruff over both projects
	$(PYTHON) -m ruff check .

clean: ## Remove caches (keeps the local SQLite databases)
	rm -rf .pytest_cache .ruff_cache fastapi_project/.pytest_cache
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +
