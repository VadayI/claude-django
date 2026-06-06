---
name: github-actions-django
description: "[claude-django] GitHub Actions CI for Django (ruff + pytest with a postgres service); the gate before merging to main. Activate for CI/CD."
---

# GitHub Actions for Django

## backend-ci.yml (on pull_request)
- `services.postgres` (parity with dev/staging).
- pip cache; install dependencies.
- `ruff check .`; `pytest --cov=apps`.
- Test/lint failure blocks merge (branch protection requires green CI).

## Contract conformance gate (in backend-ci.yml)
- `bash scripts/check_contract_conformance.sh` — validates the implementation against the pinned external contract (`docs/api/openapi.yml`, pulled via `scripts/pull_contract.sh`): schemathesis + django-contract-tester. Any divergence fails the PR (ADR 0017).

## Stub gate (in backend-ci.yml)
- `bash scripts/check_stubs.sh` — fails on `# STUB:` / `NotImplementedError("STUB: …")` in `backend/apps/` without a row in `docs/STUBS.md`.

## (optional) deploy.yml
- On push to `main`: SSH to the VPS, `git pull`, `docker compose -f docker-compose.staging.yml up -d --build`, `migrate`. Secrets — in Actions Secrets.

## Principles
- CI is a mandatory gate before merge alongside review.
- Backend-only CI; cache deps for speed; gates run in order: ruff → stub-gate → OpenAPI drift → pytest.

> Ready templates — `templates/.github/workflows/`.
<!-- Last reviewed/updated: 2026-05-27 -->
