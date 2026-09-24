# Plan 0015 — P06 hosted Django conformance

> Status: 🟡 IN PROGRESS · seeded 2026-09-24 · Driver: P06 hosted Django backend runner validation
> Type: config-template change. No backend application code; the canonical inert CI workflow must boot its test Django app before strict live contract conformance.
>
> **Living plan** — discipline in `.claude/rules/living-plan.md`.

## Status

| Step | State | Owner |
|---|---|---|
| 1. Review CI workflow and conformance requirements | done | ci-cd-engineer |
| 2. Add DB migration, loopback Django startup/readiness, conformance URL, and cleanup | done | ci-cd-engineer |
| 3. Validate YAML and inspect focused diff | done | ci-cd-engineer |
| 4. Run the hosted workflow on a derived Django project | blocked | user / orchestrator |

## Goal

Make the shipped `backend-ci.yml` template perform live Schemathesis conformance on a real derived Django project, removing the current guaranteed strict-stage failure caused by the missing `CONFORMANCE_BASE_URL` and stopped/nonexistent server.

## Approach

Keep workflow triggers, jobs, job names, permissions, and the exact-candidate runner unchanged. In the existing `test` job, migrate its PostgreSQL service database after installing dev dependencies, start Django on `127.0.0.1:8000` with the autoreloader disabled, wait for `/api/v1/health/`, pass the loopback URL only to the strict conformance step, then stop the server even when conformance fails. Do not supply authentication secrets; authenticated behavior remains covered by pytest conformance tests.

## Steps

1. Review the CI engineer instructions, conformance script, and canonical workflow — complete.
2. Add the live-server lifecycle to the canonical workflow and preserve exact runner/check names.
3. Parse/inspect the YAML and diff; report any behavior not verifiable without GitHub Actions.
4. Once a derived Django project has the materialized workflow, perform its hosted run and record the run SHA/result separately before closing P06.

## Verification

- Parse the edited workflow as YAML (accounting for GitHub Actions' `on` key semantics).
- Inspect `git diff --check` and the exact diff to verify only the intended workflow and plan changed.
- Confirm the existing `family-core` job and `test` job names are unchanged.
- Hosted runner behavior, database connectivity, and real contract conformance require a separate GitHub Actions run against a derived project and remain unverified here.

## Open questions

- [ ] Which derived Django repository and branch will host the workflow run?

## Execution log

> Append-only. Short confirmations of execution facts as the work runs — e.g. "step N green (pytest)", "contract recorded in endpoints.json", "gate: 1×🟡 → back to django-developer". Never edited retroactively. Distinct from `docs/WORKLOG.md` (cross-session chronicle, owned by `/wrap-up`); this log tracks the course of *one* task.

- 2026-09-24 — plan seeded; source repository clean on main; feature branch created locally.
- 2026-09-24 — canonical workflow updated; YAML structure and added Bash snippets validated; diff check clean. Hosted behavior remains unverified pending a derived-project run.
- 2026-09-24 — RED: focused `file_digests` directory regression tests fail as expected because the runner rejects the `backend` directory input.
- 2026-09-24 — GREEN: synced reviewed core commit `90fdafde68454d665a53de78dc8f5fd8420465c2`; directory digest and no-cache Ruff catalog checks pass locally. Fixture exact runner passes Ruff; PostgreSQL conformance/pytest remain `NOT_VERIFIED`, and public drift fetch is blocked by local Windows Schannel.

## Amendments

> Append-only. When a decision in the body changes, do NOT delete the original — add an entry here and an inline pointer next to the original paragraph (`> ⚠️ Changed — see Amendment #k`). Keeps the decision history transparent.

_(none yet)_
