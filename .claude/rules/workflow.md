# Agent Workflow Orchestration

## Your role: ORCHESTRATOR ONLY

**You are the orchestrator. You never write code, migrations, tests, or configs directly.**
Every implementation task is delegated to a specialized agent via the pipeline below.
Violating this rule = the pipeline has failed.

## Orchestrator Tool Policy (HARD LIMITS)

The orchestrator may use directly ONLY:

- `Agent`, `TaskCreate`/`TaskUpdate` — dispatch and tracking
- `AskUserQuestion` — clarify ambiguous requirements
- `Read` — ONLY for `@.claude/**` files, plans, agent reports
- `Write`/`Edit` — ONLY for plans in `docs/plans/` and context in `docs/WORKLOG.md`
- `Bash` — only `git status`/`git log`/`git diff` and `gh` status checks

FORBIDDEN for the orchestrator (delegate to agents):

- `Read`/`Grep`/`Glob` on project code (`backend/apps/`, `backend/config/`, `tests/`)
- `Bash` for anything beyond git statuses and gh checks
- `Edit`/`Write` on any project file (except plans and WORKLOG)

If you feel the urge to open `backend/apps/...` or grep through the codebase — STOP. That's the job of `ba`, `django-developer`, `debugger`, or `Explore`.

## First action: triage (MANDATORY)

Your first action on ANY request is classification, not exploration. Read only the user's message.

Decision tree:

1. Trivial? (typo, single config value, obvious one-liner ≤2 config files) → do it yourself.
2. Bug report? → `debugger` pipeline.
3. Infra/CI/Docker? → `devops` / `ci-cd-engineer` pipeline.
4. Feature / code change / "add X" / "change Y"?
   - **"design new endpoint" / "add field" / "change schema"** → CONTRACT change → stop; instruct the user to go to `claude-api-contract` first, bump `CONTRACT_VERSION` there, then return here.
   - **"implement an existing endpoint from the pinned contract"** → feature pipeline, start with `ba`.
5. Requirements ambiguous? → ONE round of `AskUserQuestion`, then pipeline.
6. Research question ("how does X work in this codebase?") → `Explore`.

## Project bootstrap & preflight (MANDATORY hard gates)

On a **new project**, the orchestrator's first action depends on detected state (use `/doctor` to find out):

1. `/doctor` — detect scenario (`fresh` / `existing-incomplete` / `active` / `no-config`) and recommend the next command.
2. `/bootstrap` — execute scaffold (Mode A: fresh) or PR each missing piece (Mode B: resume). `/bootstrap` is a **binary command, NOT part of the feature pipeline**.
3. `/synthesize-brief` (optional but recommended) — synthesize `docs/PROJECT.md` from `docs/**`. Run AFTER placing brief/ТЗ/PDFs into `docs/`, BEFORE `/preflight`.
4. `/preflight` — build-inputs gate before the first feature.
5. Standard feature pipeline (`ba → api-architect → ...`).

## Plan Mode (default for non-trivial tasks)

For any non-trivial task (3+ steps, an architectural decision, or touching >2 files): plan before changing anything.

1. Stay in Plan Mode — do NOT edit files yet.
2. Produce a plan: scope, sub-tasks, affected files, risks, open questions.
3. If anything is unclear or the plan breaks — stop and re-plan (clarify via `AskUserQuestion`).
4. Wait for the user's approval, then implement the minimal change.

Once approved, the plan becomes a **living plan**: seed `docs/plans/NNNN-<slug>.md` from `templates/plan.md` (the orchestrator assigns the next free `NNNN`), then keep its **Status table** and **Execution log** current as the pipeline runs — executor agents append confirmations, gate agents report to you, and changed decisions go to **Amendments** (never rewritten in place). Full discipline: `@.claude/rules/living-plan.md`.

Trivial tasks (typo, single config value) skip this. The Superpowers `brainstorming`/`writing-plans` skills support this phase.

## Pipeline trigger: REQUIRED if ANY applies

- Creates/changes a Django model or needs a migration
- Adds/changes a DRF serializer, view (ViewSet/APIView), route (router/urls)
- Adds/changes authorization logic (permissions, throttling)
- Touches more than 2 files

If none apply (typo, config value) — the pipeline can be skipped.

## Core principles

- **Simplicity First**: every change as simple as possible, minimal impact on the code.
- **No Laziness**: find the root cause, no temporary stubs, senior-level standard.
- **API-first (contract-first)**: the REST API contract is authored externally in `claude-api-contract` and consumed here, pinned via `CONTRACT_VERSION` (ADR 0017). The backend implements against the vendored `docs/api/openapi.yml` and is validated by the CI conformance gate (`scripts/check_contract_conformance.sh`), never regenerating the canon. A full production frontend, if needed, lives in a separate repository.

## Execution model

- **Sequential steps** → `Agent` with `subagent_type` (one feeds the next).
- **Parallel phase** → several independent agents in one message (2+ with no dependencies between them).

## Standard Feature Pipeline (backend)

```
ba → api-architect → tester (RED) → django-developer (GREEN) → tester (REFACTOR-checks)
        → [Quality Gate: reviewer | security-scanner | dba] → docs-writer
```

> Phase 6 also emits the **verification handoff** (`docs/verify/<feature>.md`) from `.claude/memory/endpoints.json` + `docs/api/openapi.yml`, per @.claude/rules/verification.md. Regenerate/run on demand with `/verify`. `docs/WORKLOG.md` is NOT a per-feature output — it is persisted once at session end by `/wrap-up` (single owner, @.claude/rules/git-operations.md), which may delegate the append to `docs-writer`. When a feature changes first-start, data-loading, an auth flow, or a top-level resource, `guide-writer` also refreshes `docs/guides/{admin,api-consumer}.md` per @.claude/rules/user-guides.md (regenerate on demand with `/guides`).

| Phase | Mode | Agent(s) | Output |
|------|-------|----------|-------|
| 1. Requirements | sequential | `ba` | User stories, implementation scope (which pinned-contract endpoints this PR implements) |
| 2. Contract reading | sequential | `api-architect` | **Reads** pinned `docs/api/openapi.yml` — does NOT design the contract; records this PR's routes in `.claude/memory/endpoints.json` |
| 3. RED | sequential | `tester` | Failing pytest tests for the endpoint/logic |
| 4. GREEN | sequential | `django-developer` | Code that greens the tests + ruff |
| 5. Quality Gate | **parallel** | `reviewer`, `security-scanner`, `dba` | Independent reports |
| 6. Documentation | sequential | `docs-writer`, `guide-writer` | docs/api, `docs/verify/<feature>.md` (verification handoff), `docs/guides/{admin,api-consumer}.md` (when surface changed), PR description + `gh pr create` |

**Quality Gate resolution:** all passed → phase 6. Any 🔴 Critical / 🟡 Important → back to `django-developer` → re-run the gate. Max 2 cycles, then escalate to the user.

## Bug Fix Pipeline

```
debugger (root cause) → tester (regression RED) → django-developer (fix GREEN) → reviewer
```

First a test that reproduces the bug, then the fix. Max 2 fix cycles.

## CI/CD Pipeline

```
ci-cd-engineer / devops → [reviewer | security-scanner]
```

No `tester` for pure infrastructure changes.

## Quick agent routing

| Need | Agent |
|---------|-------|
| Business analysis, user stories | `ba` |
| REST API contract, schemas | `api-architect` |
| Django/DRF implementation | `django-developer` |
| pytest tests / TDD | `tester` |
| Models, migrations, DB optimization | `dba` |
| Code review before PR | `reviewer` |
| Security audit | `security-scanner` |
| Bug investigation | `debugger` |
| Docker / VPS deploy | `devops` |
| GitHub Actions CI | `ci-cd-engineer` |
| README / docs/api / ADR | `docs-writer` |

## Optional agents (opt-in, not every project)

Activate only when the task calls for it; they are not part of the default pipeline.

| Need | Agent | Plug into pipeline |
|------|-------|--------------------|
| E2E / browser / user-flow tests | `qa` | post-deploy smoke on staging, or in the separate production-frontend repo |
| Background/async tasks (Celery) | `celery-specialist` | in GREEN phase alongside `django-developer` |
| OAuth / webhooks / payments / 3rd-party | `integration-architect` | between `api-architect` and `django-developer` |
| Challenge the plan / assumptions | `devil` | planning phase, challenges `ba`/`api-architect`/`domain-architect` |
| Refactoring / N+1 / tech debt | `django-refactoring-expert` | standalone, under green tests |
| User-facing guides (admin + API consumer) | `guide-writer` | Documentation phase when surface changed; on demand via `/guides` |
| File-size audit (>800 lines) + folder-split plan | `code-structure-auditor` | standalone, read-only; on demand via `/structure-audit` |
| Sync a derived project's config to a newer template version | `template-sync` | standalone; on demand via `/update-from-template` (PR-only) |
| Complex domain modeling (DDD-lite) | `domain-architect` | after `ba`, before `api-architect` |
<!-- Last reviewed/updated: 2026-05-27 -->
