---
model: sonnet
description: "[claude-django] /adopt — attach the config to an EXISTING foreign Django project: layout survey, additive-only copy via template-sync adopt mode (existing files never overwritten), lands as a PR."
---

Attach the `claude-django` config to an **existing Django project that was NOT created from this template** (a "foreign" project). Unlike the README Quick start (greenfield seed) and `/bootstrap` (scaffold/resume of a template-derived project), `/adopt` is **additive-only**: it never overwrites an existing file — conflicts are surfaced as `<name>.adopt-proposed` copies + a merge report, and the whole change lands as a **PR** (ADR `0026`).

## Input

Optional `$ARGUMENTS`: an upstream URL or git ref (default: canonical `https://github.com/VadayI/claude-django.git` @ default branch), plus `--dry-run` for a report without any changes.

## Preconditions (verify read-only; STOP if any fails)

- `.git/` exists and the working tree is clean (ask the user to commit/stash first).
- A Django project is present: `manage.py` at the root or under `backend/`, or Django in `pyproject.toml`/`requirements.txt`.
- NOT already template-derived: if `.claude/memory/template-sync.json` exists, OR `.claude/` + `CLAUDE.md` + `templates/` are all present → STOP and point to `/update-from-template` (the upgrade channel) or `/bootstrap` Mode B (an unfinished template scaffold).
- NOT the template repo itself (`docs/decisions/0001-*` + `templates/` + no `backend/`) → STOP.

## Steps

1. **Clone upstream** (read-only) to a temp dir:
   ```bash
   UPSTREAM_URL="${ARG_URL:-https://github.com/VadayI/claude-django.git}"
   rm -rf /tmp/claude-django && git clone --depth 1 "$UPSTREAM_URL" /tmp/claude-django
   git -C /tmp/claude-django rev-parse HEAD   # the SHA being adopted
   ```
2. **Layout survey** (read-only probes; goes into the report and the PR description): `manage.py` location (root vs `backend/`); settings layout (`settings.py` file vs `settings/` package); deps file (`pyproject.toml` vs `requirements.txt`); test runner (pytest vs Django TestCase); existing CI under `.github/workflows/`; existing `CLAUDE.md` / `Makefile` / `docker-compose.yml` / `.gitignore` / `.env.example`. Every mismatch with the template's assumed layout (`backend/config/settings/{base,dev,staging}.py`, `backend/apps/<domain>/`, `apps.common` — see `.claude/rules/architecture.md`) is listed as an **adaptation note**: the config still works, but the merged `CLAUDE.md` must tell agents the real paths.
3. **Feature branch** (skip on `--dry-run`): `git checkout -b chore/adopt-claude-django`.
4. **Dispatch `template-sync`** (`subagent_type: "template-sync"`) with `$UPSTREAM=/tmp/claude-django`, `MODE=adopt`, the layout survey, and the dry-run flag if present. Adopt mode is additive-only (see the agent's *Adopt mode* section): new files copied; existing files NEVER overwritten — upstream versions land as `<name>.adopt-proposed`; `templates/` is NOT copied wholesale; finishes by writing `.claude/memory/template-sync.json` (`mode: adopt`) so all future upgrades go through `/update-from-template`.
5. **Relay** the report: what was added; every `*.adopt-proposed` awaiting manual merge (`CLAUDE.md`, `settings.json`, CI workflows, `Makefile`, `docker-compose.yml`); the adaptation notes; and the manual follow-ups — fill `.env`, decide on `apps.common` (error envelope / `HasScope` / health — `.claude/rules/serializers-permissions.md`), set the contract pin if the project consumes `claude-api-contract` (`.claude/rules/api-docs.md`), run `/doctor`, paste plugin installs via `/plugins`.
6. **Open a PR** (skip on `--dry-run`): hand off to `/create-pr` with the layout survey + merge list in the description. **Never push to `main`.**

## Hard limits

- **Additive-only**: never overwrite, delete, or rewrite an existing project file — proposals (`*.adopt-proposed`) only.
- PR-only; never commit to `main`; never print secret values. `--dry-run` = full report, zero changes.
- If preconditions point to `/update-from-template` or `/bootstrap` — STOP and say so; never "half-adopt".

> Pairs with `/doctor` (detects the `foreign-django` scenario and recommends this command), `/update-from-template` (upgrades AFTER adoption), and `/bootstrap` (greenfield/resume — never for foreign projects). Decision record: ADR `0026`.
<!-- Last reviewed/updated: 2026-07-07 (created — audit v2 batch K) -->
