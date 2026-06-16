# Deviation register (deviations & contract findings are documented, never silent)

When an agent departs from the agreed plan — finds a contract error, a better
technical alternative, a blocker that forces a different route, or must raise the
contract pin (`CONTRACT_VERSION`) — that is a **deliberate, documented act**, never
a silent course change. The record lives in `docs/reviews/`.

## When a deviation doc is REQUIRED

Create `docs/reviews/YYYY-MM-DD-<slug>.md` when any of these happen in a PR:

- an agent deviates from the approved living plan (a plan **Amendment** is added);
- an agent finds a defect or ambiguity in the consumed contract (`docs/api/openapi.yml`);
- an agent chooses a materially different technical approach than the plan stated;
- `CONTRACT_VERSION` is raised (the consumed contract pin changes).

A trivial in-scope clarification that does not change the plan does NOT need one —
the bar is "the course changed, or the contract is wrong."

## Required fields

```
# Deviation — <short title>   (YYYY-MM-DD)
- Original plan / expectation: what we said we'd do.
- What changed / problem: the deviation, defect, or better alternative.
- Evidence: test output, contract excerpt, link to the failing case.
- Decision: what we did instead, and why.
- Impact: contract / code / tests / docs / consumers affected.
- Status: proposed | accepted | superseded.
```

## Relationship to the living plan

The living plan's **Amendments** section records *that* a decision changed
(@.claude/rules/living-plan.md); the deviation doc records *why* in reviewable
detail and survives beyond the single task. An Amendment that changes the contract
or the agreed approach MUST point to its `docs/reviews/` entry.

## Enforcement

- `backend-policy.yml` blocks a PR that raises `CONTRACT_VERSION` without a
  `docs/reviews/` note or an ADR (`docs/decisions/`).
- `reviewer` flags, at the Quality Gate, any plan Amendment or contract finding
  that lacks a `docs/reviews/` entry.
- `docs/reviews/` is append-only history — never edit a past deviation; supersede
  it with a new dated entry.

> Goal: an agent can change course or report a contract defect — but it must leave
> a trace in `docs/reviews/`, so "agents follow the plan, and every deviation is
> documented" is mechanically visible, not honor-system.
