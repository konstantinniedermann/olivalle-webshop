.DEFAULT_GOAL := help

.PHONY: help dev test lint db-setup docs

help: ## Alle verfügbaren Befehle anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Frontend (Next.js) + Backend (FastAPI) starten
	@echo "TODO: next dev & uvicorn backend.main:app --reload"

test: ## Tests ausführen (pytest + Vitest)
	@echo "TODO: pytest && npx vitest"

lint: ## Linting (Ruff + ESLint)
	@echo "TODO: ruff check . && npx eslint ."

db-setup: ## Supabase Migrations ausführen
	@echo "TODO: supabase db push"

docs: ## MkDocs Dokumentation lokal starten
	@echo "TODO: mkdocs serve"
