# Living plan (agents keep `docs/plans/NNNN-*.md` current as work runs)

A plan is a **living artifact**, not a frozen Plan-Mode snapshot. The orchestrator seeds `docs/plans/NNNN-<slug>.md` at the start of a non-trivial task, and the work's actual course flows back into it — confirmations of what ran, and changes of direction — instead of the plan drifting from reality and duplicating WORKLOG. This stays within Simplicity First: no new tooling, just discipline + one template (`templates/plan.md`) + this rule.

## When a plan is seeded

- **Scope = every non-trivial task** — the same threshold that activates Plan Mode (`@.claude/rules/workflow.md`): 3+ steps, an architectural decision, or touching >2 files. Trivial tasks (a typo, a single config value) do NOT seed a plan.
- **The orchestrator seeds it**, copying `templates/plan.md` → `docs/plans/NNNN-<slug>.md`. `NNNN` is the next free number in `docs/plans/`, assigned by the orchestrator at seed time — never by agents (avoids number races between parallel agents).

## The three managed sections

Each `docs/plans/NNNN-*.md` carries three managed sections on top of the ordinary plan body:

1. **Status table** (top) — step / state (`pending`/`in_progress`/`done`/`blocked`) / owner-agent. The plan's cursor; updated as steps move.
2. **Execution log** (append-only) — short confirmations of execution facts: "step N green (pytest)", "contract recorded in endpoints.json", "gate: 1×🟡 → back to django-developer". Appended, never edited retroactively.
3. **Amendments** (append-only) — changes of direction. If a plan decision changes, the original paragraph is **not deleted**; instead add an Amendments entry plus an inline pointer next to the original (`> ⚠️ Changed — see Amendment #k`). The decision history stays transparent.

## Who updates what

- **Orchestrator** — seeds the plan; owns the Status table; records gate outcomes into the Execution log (gate agents report to it, see below); appends Amendments when a body decision changes.
- **Executor agents** (`ba`, `api-architect`, `django-developer`, `tester`, `docs-writer`) — after finishing their phase, **append** a one-line confirmation to the active plan's Execution log (via `Edit` append, never a full-file rewrite).
- **Gate agents** (`reviewer`, `security-scanner`, `dba`) — do NOT edit the plan; they stay read-only over both code and plan. They **report the gate result to the orchestrator**, which records the Execution log entry. This preserves the "gate agents only read and report" invariant.

## Boundary with WORKLOG

**Execution log ≠ WORKLOG.** The Execution log is an in-plan journal of confirmations during one task. `docs/WORKLOG.md` is the cross-session chronicle, single owner `/wrap-up`. They do not duplicate: the plan records the course of one task, WORKLOG the session summary.

## Binds these agents (rule is auto-loaded)

- `ba`, `api-architect`, `django-developer`, `tester`, `docs-writer` — append an Execution log confirmation at the end of their phase (need `Edit` to append).
- `reviewer`, `security-scanner`, `dba` — never edit the plan; report the gate result to the orchestrator.

## Out of scope (v1)

- A CI gate "plan updated in the same PR" (like `check_app_readmes.sh`) — only after the discipline is hand-proven. Tracked in HANDOFF open questions.
- A machine-readable Status format (JSON) — markdown tables suffice for now (Simplicity First).

> Goal: at any point in a non-trivial task, the plan shows where we are (Status), what has actually run (Execution log), and why decisions changed (Amendments) — without drifting from reality or duplicating WORKLOG.
