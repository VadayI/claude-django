---
model: sonnet
description: "[claude-django] Generate (and optionally run) the human-facing endpoint verification guide for a feature."
---

Generate (and optionally run) the **human-facing endpoint verification guide** for a feature — the manual, copy-paste smoke test described in `@.claude/rules/verification.md`. This is the on-demand twin of the automatic block `docs-writer` emits at the end of the feature pipeline.

## Log

```bash
python scripts/log-cmd.py /verify $ARGUMENTS
```

## Input

`$ARGUMENTS`:
- a **feature slug** (e.g. `article-crud`) — which feature to (re)generate. If empty, ask via `AskUserQuestion`, defaulting to the current branch name stripped of its `feat/|fix/|chore/` prefix. `all` regenerates every feature present in `.claude/memory/endpoints.json`.
- optional flag **`--run`** — after generating, execute the guide against a live server and report pass/fail.

## Preconditions

- `.claude/memory/endpoints.json` exists and is non-empty (the route registry written by `api-architect`). If missing/empty -> STOP: "no recorded endpoints; run the feature pipeline (api-architect records routes) first."
- `docs/api/openapi.yml` exists (the vendored external contract — source of truth, ADR 0017). If missing -> warn that field shapes can't be verified against the schema and proceed from `endpoints.json` only.

## Steps

### 1. Reconcile (always, read-only)

Before generating, confirm the three sources agree per `@.claude/rules/verification.md`:

```
.claude/memory/endpoints.json  <->  docs/api/openapi.yml  <->  docs/api/INDEX.md
```

`openapi.yml` is the source of truth. If `endpoints.json` disagrees (renamed path, dropped endpoint, changed status), report the drift and dispatch `docs-writer` to correct `endpoints.json` / `INDEX.md` to match the schema — do NOT silently generate from a stale registry.

### 2. Generate `docs/verify/<feature>.md` (default)

Dispatch `docs-writer` to:
- `mkdir -p docs/verify`
- For each endpoint of the feature in `endpoints.json`, render the per-endpoint block from `templates/verify_TEMPLATE.md` (or `docs/verify/_TEMPLATE.md` if the template was already copied into the project): Swagger step, `curl` success example with a realistic body, expected success code + key fields, and one-line negative `curl`s for exactly the declared codes (401/403/400/404/409 — only those the contract lists).
- Bodies and field names come from `openapi.yml`; never invent fields.
- Write/overwrite `docs/verify/<feature>.md`. Idempotent — re-running with no contract change leaves the file unchanged.

### 3. `--run` (optional — execute against a live server)

Only when `$ARGUMENTS` contains `--run`. Dispatch `devops`:

- Ensure the stack is up: `docker compose up -d` (wait for healthy). If it can't come up -> STOP and report; do not fake results.
- For each endpoint, execute the success `curl` and the negative `curl`s, capturing only the HTTP status (`-o /dev/null -w '%{http_code}'`).
- **State-change safety:** for `POST/PUT/PATCH/DELETE`, prefer the negative cases (401/403/400) that do NOT mutate state. Run a mutating success call ONLY against the dev database, and tell the user it wrote real rows. Never run `--run` against staging/production base URLs.
- Report a table: `method path | case | expected | actual | PASS/FAIL`. Any mismatch is a FAIL; summarize counts.

### 4. Summary

Print the path(s) written (`docs/verify/<feature>.md`) and, if `--run` was used, the pass/fail table. Remind the user this guide is the manual mirror of the pytest suite — green tests + a green `/verify --run` is the strongest signal.

## Hard limits

- No `git commit` / `git push` — leave the generated file staged for review.
- Never invent request/response fields not present in `openapi.yml`.
- Never print secret values; use placeholders (`$TOKEN`) in examples.
- `--run` targets the **dev** base URL only — never staging/production.
