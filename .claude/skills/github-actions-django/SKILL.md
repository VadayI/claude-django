---
name: github-actions-django
description: GitHub Actions CI for Django (ruff + pytest with a postgres service) and a Vite build for the frontend; the gate before merging to main. Activate for CI/CD.
---

# GitHub Actions for Django/React

## backend-ci.yml (on pull_request)
- `services.postgres` (parity with dev/staging).
- pip cache; install dependencies.
- `ruff check .`; `pytest --cov=apps`.
- Test/lint failure blocks merge (branch protection requires green CI).

## OpenAPI drift gate (in backend-ci.yml)
- `bash scripts/check_openapi_drift.sh` — regenerates the schema from code and fails on any diff with `docs/api/openapi.yml`.

## Stub gate (in backend-ci.yml)
- `bash scripts/check_stubs.sh` — fails on `# STUB:` / `NotImplementedError("STUB: …")` in `backend/apps/` without a row in `docs/STUBS.md`.

## (optional) deploy.yml
- On push to `main`: SSH to the VPS, `git pull`, `docker compose -f docker-compose.staging.yml up -d --build`, `migrate`. Secrets — in Actions Secrets.

## Principles
- CI is a mandatory gate before merge alongside review.
- Backend-only CI; cache deps for speed; gates run in order: ruff → stub-gate → OpenAPI drift → pytest.

> Ready templates — `templates/.github/workflows/`.
<!-- Last reviewed/updated: 2026-05-27 -->
