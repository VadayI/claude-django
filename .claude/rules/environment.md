# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` reads `.claude/memory/env-detect.json` (written by the `SessionStart` hook) to pick shell-appropriate checks, never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

The Check column gives bash (Linux / macOS / WSL2) and PowerShell (Windows native) equivalents. The shell is auto-detected by `scripts/detect-env.py` on every session start and stored in `.claude/memory/env-detect.json`; `/doctor` consults that file to pick the right check.

| Requirement | Expected | Check (bash / PowerShell) |
|---|---|---|
| **Python (HARD REQUIREMENT)** | 3.10+ on PATH as `python` | `python --version` (both shells). On Ubuntu, if only `python3` is installed: `sudo apt install -y python-is-python3`. Without Python the SessionStart hook (`scripts/detect-env.py`) cannot run. |
| OS shell | **WSL2 (Ubuntu) recommended**, native PowerShell/cmd works for everything except a small performance penalty on bind-mounts | bash: `uname -a` / PS: `$PSVersionTable` |
| Working dir | If WSL2: in the WSL2 fs (`~/projects/<p>`), NOT under `/mnt/c\|/mnt/d`. If PowerShell: any local path is fine (Docker Desktop handles the volume internally). | bash: `pwd` / PS: `Get-Location` |
| Docker Desktop | running, with WSL2 integration enabled if WSL2 is used | `docker info` (both shells) |
| docker compose | v2 available | `docker compose version` (both shells) |
| Python in container | 3.13.x (separate from the host Python above) | `docker compose exec -T backend python --version` (both shells) |
| Node.js | 18+ — optional for backend-only repos, needed only for `npx`-based skills (e.g. Context7 MCP runs via `npx`) | bash: `node --version` / PS: `node --version` |
| git | present | `git --version` (both shells) |
| GitHub CLI | present **in the active shell** (a Windows `gh.exe` from `winget` is NOT visible inside WSL2; install separately) | `gh --version` (both shells) |

## Scope 2 — Claude config & access

| Requirement | Expected | Check |
|---|---|---|
| Plugins | `superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`, `claude-hud` installed | `/plugin` list; compare with `.claude/settings.json` `enabledPlugins` |
| MCP servers enabled | `github`, `context7` | `.claude/settings.json` `enabledMcpjsonServers` |
| `github` MCP env | `GITHUB_PERSONAL_ACCESS_TOKEN` set | bash: `[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]` / PS: `[bool]$env:GITHUB_PERSONAL_ACCESS_TOKEN` (never print the value) |
| `context7` MCP env | `CONTEXT7_API_KEY` set | bash: `[ -n "$CONTEXT7_API_KEY" ]` / PS: `[bool]$env:CONTEXT7_API_KEY` (never print the value) |
| GitHub auth | `gh` authenticated (via env token OR stored creds — either is fine; if `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` is set, `gh auth login` will refuse to store separate creds and that is EXPECTED) | `gh auth status` (both shells) |

## Scope 3 — Project state

| Requirement | Expected | Check |
|---|---|---|
| Skeleton | `backend/`, `docs/api/`, `docs/decisions/`, `docs/plans/`, `.claude/memory/` exist | bash: `test -d <dir>` / PS: `Test-Path <dir>` |
| Config files | `CLAUDE.md`, `.claude/`, `docker-compose.yml`, `.env` present | bash: `test -f <file>` / PS: `Test-Path <file>` |
| `.env` | exists (copied from `.env.example`); secrets filled | bash: `test -f .env` / PS: `Test-Path .env` (never print contents) |
| Services | `postgres` + `backend` up and healthy | `docker compose ps` (both shells) |
| Migrations | applied (no unapplied) | `docker compose exec -T backend python manage.py showmigrations --plan` — output should not contain `[ ]` |
| Tests | pytest green | `docker compose exec -T backend pytest -q` (both shells) |
| Lint | ruff clean | `docker compose exec -T backend ruff check .` (both shells) |

> Skeleton/`.env`/services may legitimately be absent in a brand-new repo before Step 3 of the README. `/doctor` reports these as "not set up yet" (info), not as failures, when no Django project exists yet.

## Scope 4 — Git hygiene

| Requirement | Expected | Check |
|---|---|---|
| Current branch | a feature branch, **not** `main` (for active work) | `git branch --show-current` (both shells) |
| Branch protection | `main` protected on GitHub (PR + status checks) | `gh api repos/{owner}/{repo}/branches/main/protection` (both shells) — 404 = not protected |
| Working tree | clean or only intended changes | `git status -sb` (both shells) |
| Sync | up to date with `origin` | `git fetch --dry-run` then `git status -sb` (both shells) |
| No secrets tracked | `.env` ignored, not committed | bash: `git ls-files \| grep -E '(^\|/)\.env$'` / PS: `git ls-files \| Select-String '\.env$'` (empty = good) |

## Remediation policy

- **Safe to propose-then-apply (after confirmation):** `docker compose up -d`, `python manage.py migrate`, create missing skeleton dirs, `cp .env.example .env`, `/plugin install ...`, `nvm install`, create a feature branch off fresh `main`.
- **Ask explicitly, never silently:** anything that writes secrets, force operations, deleting files, enabling branch protection (account-level), pushing.
- **Forbidden in `/doctor`:** committing, `git push`, pushing to `main`, printing secret values, editing application source code.

<!-- Last reviewed/updated: 2026-05-27 -->
