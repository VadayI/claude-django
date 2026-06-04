---
model: sonnet
description: "[claude-django] Generate/refresh the user-facing onboarding guides (docs/guides/admin.md + api-consumer.md)."
---

Generate or refresh the **user-facing onboarding guides** — `docs/guides/admin.md` (operator) and `docs/guides/api-consumer.md` (API integrator) — per `@.claude/rules/user-guides.md`. This is the on-demand twin of the guide updates `guide-writer` emits in the Documentation phase of the feature pipeline.

## Log

```bash
python scripts/log-cmd.py /guides $ARGUMENTS
```

## Input

`$ARGUMENTS` (optional):
- empty -> refresh **both** guides.
- `admin` -> only `docs/guides/admin.md`.
- `api` -> only `docs/guides/api-consumer.md`.

## Preconditions

- A Django project exists (`backend/`). If not -> STOP: "no backend yet; run /bootstrap first."
- `docs/api/openapi.yml` and `.claude/memory/endpoints.json` are the source of truth for any endpoint/auth the api-consumer guide names. If missing, warn that API references can't be reconciled and proceed from code only.

## Steps

1. **Dispatch `guide-writer`** (`subagent_type: "guide-writer"`) to:
   - `mkdir -p docs/guides`
   - For each requested guide: if absent, create it from `templates/guides_admin.md` / `templates/guides_api_consumer.md`; otherwise refresh the volatile sections (First start, Loading initial data, Django admin / Authentication, First request, Conventions).
   - **Reconcile** every concrete reference against the code + schema (routes/auth in `openapi.yml` + `endpoints.json`; management commands under `backend/apps/*/management/commands/`). Fix anything that drifts; the schema is the source of truth. Replace any unbuilt capability with "not yet available" rather than fiction.
2. **Report** which guides were written/updated and any reconciliation findings (invented or removed references it corrected).

## Hard limits

- No `git commit` / `git push` — leave the files staged for review (open a PR via `/create-pr`).
- Never invent endpoints, auth flows, or management commands the code does not have.
- Never print secret values; use placeholders (`$TOKEN`) in examples.

> Pairs with `/verify` (per-endpoint smoke test) and `/update-docs` (api/README/WORKLOG). The guides are the "getting started" layer above both.
<!-- Last reviewed/updated: 2026-06-02 -->
