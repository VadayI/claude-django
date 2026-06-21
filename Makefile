# Root Makefile for the claude-django TEMPLATE repo itself.
# Convenience only — the canonical launcher is `bash scripts/claude.sh`
# (PowerShell: scripts/claude.ps1). See docs/decisions/0023-*.md.
.PHONY: help cc

help:
	@echo "Targets:"
	@echo "  cc    launch Claude Code with .env sourced (scripts/claude.sh)"

cc:
	@bash scripts/claude.sh
