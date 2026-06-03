# Makefile — convenience wrappers for the claude-django dev loop.
#
# Identical on native Debian and WSL2 Ubuntu (both are bash + docker compose).
# These are SHORTCUTS around the Docker commands in
# .claude/rules/docker-commands.md — NOT a replacement for the agent pipeline
# or the slash-commands (/doctor, /bootstrap, /preflight, ...).
#
# Override the runner:  make test DC="docker compose -f docker-compose.staging.yml"
# Pass extra args:      make test ARGS="-k auth -x"

DC ?= docker compose
BACKEND ?= $(DC) exec backend
ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help setup up dev down ps logs build test cov lint fmt migrate makemigrations superuser shell schema gates doctor-deps check-deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "} {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## One-shot host toolchain install (python/node/claude/gh) — WSL2/Debian
	bash scripts/setup-wsl.sh

up: ## Start db + backend (detached)
	$(DC) up -d

dev: up ## Alias for `up`

down: ## Stop services
	$(DC) down

ps: ## Service status
	$(DC) ps

logs: ## Tail backend logs
	$(DC) logs -f backend

build: ## Build/rebuild images (install deps)
	$(DC) build

test: ## Run pytest (filter: make test ARGS="-k name")
	$(BACKEND) pytest $(ARGS)

cov: ## pytest with coverage report
	$(BACKEND) pytest --cov=apps --cov-report=term-missing $(ARGS)

lint: ## ruff check
	$(BACKEND) ruff check . $(ARGS)

fmt: ## ruff format
	$(BACKEND) ruff format .

migrate: ## Apply migrations
	$(BACKEND) python manage.py migrate $(ARGS)

makemigrations: ## Create migrations
	$(BACKEND) python manage.py makemigrations $(ARGS)

superuser: ## Create a Django superuser
	$(BACKEND) python manage.py createsuperuser

shell: ## Django shell
	$(BACKEND) python manage.py shell

schema: ## Regenerate docs/api/openapi.yml from live code (host; see api-docs.md)
	cd backend && python manage.py spectacular --file ../docs/api/openapi.yml --format openapi-yaml

gates: ## Run CI gate scripts locally (stubs, openapi drift, app readmes)
	bash scripts/check_stubs.sh
	bash scripts/check_openapi_drift.sh
	bash scripts/check_app_readmes.sh

check-deploy: ## Django deployment-readiness check against staging settings
	$(DC) -f docker-compose.staging.yml run --rm backend python manage.py check --deploy

doctor-deps: ## Quick host tool check (versions only; not the /doctor command)
	@for t in python node claude gh docker; do \
	  if command -v $$t >/dev/null 2>&1; then printf '  ok  %-8s %s\n' "$$t" "$$(command -v $$t)"; \
	  else printf '  --  %-8s missing\n' "$$t"; fi; \
	done
