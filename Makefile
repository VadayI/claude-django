# Root Makefile for the claude-django TEMPLATE repo itself.
# Convenience only — the canonical launcher is `bash scripts/claude.sh`
# (PowerShell: scripts/claude.ps1). See docs/decisions/0023-*.md.
.PHONY: help cc ai-claude ai-codex ai-core-check
AI_PYTHON ?= python
AI_ARGS ?=

help:
	@echo "Targets:"
	@echo "  cc    launch Claude Code with selected .env data (scripts/claude.sh)"
	@echo "  ai-claude / ai-codex   launch via portable family runtime"
	@echo "  ai-core-check         check pinned family runtime drift"

ai-claude:
	@$(AI_PYTHON) scripts/ai/launch.py claude $(AI_ARGS)

ai-codex:
	@$(AI_PYTHON) scripts/ai/launch.py codex $(AI_ARGS)

ai-core-check:
	@$(AI_PYTHON) scripts/ai/core_sync.py --check

cc:
	@bash scripts/claude.sh
