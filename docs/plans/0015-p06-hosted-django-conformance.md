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
| 4. Run the hosted workflow on a derived Django project | in progress — see Amendment #1 | user / orchestrator |

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

### Amendment #1 — first exact-candidate hosted run (2026-09-24)

The fixture repository and branch are `VadayI/p06-django-derived-fixture-2026-09-24` / `feat/p06-derived-django-backend`. Run `36034509602` on candidate `54904a5f83251f157cd0ebd5d07aacdefab237a4` and base `948454cbedd7910e58fb8b2b72c3db2ed2eafba1` exercised the hosted PostgreSQL and live server successfully, then failed conformance on two generated cases: NUL in a login password was allowed by the schema but rejected by Django, and the derived registration password validators rejected a schema-shaped value with a documented 400 response. This amendment keeps contextual registration validators outside the portable schema while teaching the template gate to accept and schema-check the documented 400 on registration. The reusable contract now prohibits NUL in auth passwords and will be released as v2.0.0. P06 remains open pending a fresh hosted PASS and preserved runner artifact.

> ⚠️ Updated — see Amendment #2 for the v2.0.0 pin and latest hosted-run state.

### Amendment #2 — contract NUL rule and contextual registration validation (2026-09-24)

The reusable contract change is committed locally as `fa6d87d220a70e1287dd2b7bf96147223faebbca` and tagged `v2.0.0`; publication is still pending. The Django template conformance gate now forbids Hypothesis cache writes outside its temporary directory and accepts a documented 400 only for `POST /auth/register`, while retaining response-schema checks. The private fixture's previous exact-candidate run `36034509602` passed PostgreSQL, pytest, and every exact catalog check except live Schemathesis conformance. P06 remains open until the updated template and v2.0.0 pin are pushed and a fresh hosted run passes with its runner artifact preserved.

### Amendment #3 — isolate test settings from live conformance (2026-09-24)

Hosted run `36038160215` passed contract conformance, drift, and the exact-candidate runner, but `Tests + coverage` failed. The job-level `DJANGO_SETTINGS_MODULE=config.settings.conformance` overrode the pytest default from `backend/pyproject.toml`; as a result, the test-only `common_sampleitem` migration was not loaded and the conformance throttle rates (`100000/min`) bypassed the throttling assertions. The canonical workflow now keeps `config.settings.conformance` at job scope for migration and the live server, and sets `config.settings.test` only on the pytest step. Added the reusable conformance settings template and bootstrap delivery mapping so new projects receive the module required by that workflow. P06 remains open pending the follow-up hosted run.
