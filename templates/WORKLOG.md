# WORKLOG — {SLUG}

> Append-only chronicle of work sessions. Each entry: date, what we did, what we decided, what is unfinished. Committed to git so the history travels between machines.
>
> Maintained by `/wrap-up` at the end of every session; agents (`docs-writer`) also add entries when shipping a feature or making a non-trivial decision.

---

## {DATE_ISO} — Bootstrap from claude-django

Initial scaffold via `/bootstrap` Mode A from the [`claude-django`](https://github.com/VadayI/claude-django) template config.

**Created:**

- `backend/` skeleton (Django 6, DRF, drf-spectacular wired) with `config/settings/{base,dev,staging}.py` and `DATABASE_URL` via `django-environ`.
- `docs/` scaffolding: `PROJECT.md` (brief skeleton), `api/INDEX.md`, `api/openapi.yml`, `WORKLOG.md` (this file), `STUBS.md`, `lessons.md`, `decisions/`, `plans/`.
- `scripts/`: `detect-env.py`, `check_stubs.sh`, `check_openapi_drift.sh`, `check_app_readmes.sh`.
- `.github/workflows/backend-ci.yml` (ruff + stubs gate + OpenAPI drift gate + per-app README gate + pytest).
- `.env.example` (committed) and local `.env` (gitignored).
- GitHub repo `{OWNER}/{SLUG}` (private), first commit pushed to `main`, `backend-ci` triggered to register the status check.

**State:**

- Postgres + backend services up via `docker compose`.
- `migrate` applied (only Django built-ins so far — no app models yet).
- `ruff check .` clean; `pytest` runs (no project tests yet — expected).
- Swagger UI live at `/api/schema/swagger/`.

**Next:**

- [ ] Verify / enable branch protection on `main` (PR + status check + no bypass).
- [ ] Fill `docs/PROJECT.md` (or run `/synthesize-brief` if briefs are already in `docs/`).
- [ ] Run `/preflight` to confirm build inputs are green.
- [ ] First feature via the pipeline (`ba → api-architect → tester → django-developer`).

---
