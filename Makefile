.DEFAULT_GOAL := help

.PHONY: help dev test lint lint-all shellcheck format migrate docs css-build css-watch

help: ## Alle verfügbaren Befehle anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

css-build: ## Tailwind-CSS einmalig bauen (minifiziert)
	npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify

css-watch: ## Tailwind-CSS im Watch-Mode (für lokale Entwicklung)
	npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --watch

dev: ## FastAPI-Server mit Auto-Reload starten
	uv run uvicorn app.main:app --reload --port 8000

test: ## Tests ausführen (pytest)
	uv run pytest -v

lint: ## Linting (Ruff)
	uv run ruff check .

format: ## Code formatieren (Ruff)
	uv run ruff format .

lint-all: ## Ruff-Check + Format-Check + shellcheck (gleich wie CI)
	uv run ruff check app tests
	uv run ruff format --check app tests
	shellcheck entrypoint.sh

shellcheck: ## Shell-Skripte statisch prüfen
	shellcheck entrypoint.sh

migrate: ## Datenbank-Migration ausführen
	uv run python -c "from app.database import init_db; init_db()"

docs: ## MkDocs Dokumentation lokal starten
	uv run mkdocs serve
