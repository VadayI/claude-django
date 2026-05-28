# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

| Requirement | Expected | Check |
|---|---|---|
| OS shell | WSL2 (Ubuntu) | `uname -a` (must be Linux, not Git-Bash) |
| Working dir | code in the WSL2 fs (e.g. `~/projects/<p>`), **NOT** under `/mnt/c` | `pwd` |
| Docker Desktop | running, with WSL2 integration | `docker info` returns server info |
| docker compose | v2 available | `docker compose version` |
| Python | 3.13.x (inside the `backend` container) | `docker compose exec -T backend python --version` |
| Node.js | 18+ (host, via `nvm`, for the frontend) | `node --version` |
| git | present | `git --version` |
| GitHub CLI | present | `gh --version` |

## Scope 2 — Claude config & access

| Requirement | Expected | Check |
|---|---|---|
| Plugins | `superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`, `claude-hud` installed | `/plugin` list; compare with `.claude/settings.json` `enabledPlugins` |
| MCP servers enabled | `github`, `context7` | `.claude/settings.json` `enabledMcpjsonServers` |
| `github` MCP env | `GITHUB_PERSONAL_ACCESS_TOKEN` set | `[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]` (never print the value) |
| `context7` MCP env | `CONTEXT7_API_KEY` set | `[ -n "$CONTEXT7_API_KEY" ]` (never print the value) |
| GitHub auth | `gh` authenticated | `gh auth status` |

## Scope 3 — Project state

| Requirement | Expected | Check |
|---|---|---|
| Skeleton | `backend/`, `frontend/`, `docs/api/`, `docs/decisions/`, `docs/plans/`, `.claude/memory/` exist | `ls` / `test -d` |
| Config files | `CLAUDE.md`, `.claude/`, `docker-compose.yml`, `.env` present | `test -f` |
| `.env` | exists (copied from `.env.example`); secrets filled | `test -f .env` (never print contents) |
| Services | `postgres` + `backend` up and healthy | `docker compose ps` |
| Migrations | applied (no unapplied) | `docker compose exec -T backend python manage.py showmigrations --plan \| grep '\[ \]'` (empty = good) |
| Tests | pytest green | `docker compose exec -T backend pytest -q` |
| Lint | ruff clean | `docker compose exec -T backend ruff check .` |

> Skeleton/`.env`/services may legitimately be absent in a brand-new repo before Step 3 of the README. `/doctor` reports these as "not set up yet" (info), not as failures, when no Django project exists yet.

## Scope 4 — Git hygiene

| Requirement | Expected | Check |
|---|---|---|
| Current branch | a feature branch, **not** `main` (for active work) | `git branch --show-current` |
| Branch protection | `main` protected on GitHub (PR + status checks) | `gh api repos/{owner}/{repo}/branches/main/protection` (404 = not protected) |
| Working tree | clean or only intended changes | `git status -sb` |
| Sync | up to date with `origin` | `git fetch --dry-run` / `git status -sb` ahead/behind |
| No secrets tracked | `.env` ignored, not committed | `git ls-files \| grep -E '(^\|/)\.env$'` (empty = good) |

## Remediation policy

- **Safe to propose-then-apply (after confirmation):** `docker compose up -d`, `python manage.py migrate`, create missing skeleton dirs, `cp .env.example .env`, `/plugin install ...`, `nvm install`, create a feature branch off fresh `main`.
- **Ask explicitly, never silently:** anything that writes secrets, force operations, deleting files, enabling branch protection (account-level), pushing.
- **Forbidden in `/doctor`:** committing, `git push`, pushing to `main`, printing secret values, editing application source code.

<!-- Last reviewed/updated: 2026-05-27 -->
