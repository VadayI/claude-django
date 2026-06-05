# Plan {NNNN} — {TITLE}

> Status: 🟡 IN PROGRESS · seeded {DATE_ISO} · Driver: {what triggered this — user request / todo item / bug}
> Type: {feature pipeline | config-template change | bugfix | infra}. {If no production code is involved, note which pipeline applies / does not.}
>
> **Living plan** — discipline in `.claude/rules/living-plan.md`. The orchestrator seeds this file at the start of a non-trivial task and keeps the **Status table** + **Execution log** current as the pipeline runs. Body decisions are never rewritten in place — a changed decision goes to **Amendments** with an inline pointer next to the original.

## Status

| Step | State | Owner |
|---|---|---|
| 1. {step} | pending | {agent} |
| 2. {step} | pending | {agent} |

> States: `pending` · `in_progress` · `done` · `blocked`. This table is the cursor — update it as steps move.

## Goal

{What we are building and why. The gap / problem this plan closes.}

## Approach

{High-level strategy, key decisions, constraints. How, not a line-by-line diff.}

## Steps

1. {step}
2. {step}

## Verification

{How we confirm it works: tests, CI gates, grep checks, manual smoke, file-integrity.}

## Open questions

- [ ] {unresolved decision blocking or shaping the work}

## Execution log

> Append-only. Short confirmations of execution facts as the work runs — e.g. "step N green (pytest)", "contract recorded in endpoints.json", "gate: 1×🟡 → back to django-developer". Never edited retroactively. Distinct from `docs/WORKLOG.md` (cross-session chronicle, owned by `/wrap-up`); this log tracks the course of *one* task.

- {DATE_ISO} — plan seeded.

## Amendments

> Append-only. When a decision in the body changes, do NOT delete the original — add an entry here and an inline pointer next to the original paragraph (`> ⚠️ Changed — see Amendment #k`). Keeps the decision history transparent.

_(none yet)_
