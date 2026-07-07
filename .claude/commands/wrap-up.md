---
model: sonnet
description: "[claude-django] Wrap up the work session — summarize, persist context to Git, run checks, prepare to commit."
---

You wrap up the current work session: summarize, persist context to Git-tracked files, run checks, and prepare for commit. Invoke this when the user wants to finish work in this session / context window. This operationalizes principle 5 (Context in Git).

## Input
Optional `$ARGUMENTS`: a short note about the session focus/outcome. If empty, infer from the session.

## Steps

1. **Summarize the session** — concise: what changed, key decisions, open items / blockers.

2. **Verify merge status BEFORE writing anything** (never record intent as fact):
   ```bash
   BRANCH=$(git branch --show-current)
   gh pr list --head "$BRANCH" --state all --json number,state,mergedAt 2>/dev/null || echo "[]"
   git branch --merged origin/main 2>/dev/null
   ```
   Wording rule for the WORKLOG/summary: a branch whose PR has **no `mergedAt`** is described as **"open / not merged"**, NEVER as "merged" or "shipped to main". If `gh` is unavailable, fall back to `git branch --merged origin/main` and tag the statement **"(unverified - gh unavailable)"**. Do not claim a PR is merged without one of these confirmations.

3. **Persist context** (delegate to `docs-writer`, or do it directly if trivial):
   - Append an entry to `docs/WORKLOG.md` (using the verified status from step 2):
     ```
     ## <YYYY-MM-DD> — <branch>
     - Done: ...
     - Decisions: ... (link ADR if any)
     - Status: <branch> — PR #<n> open/not merged | merged YYYY-MM-DD (verified via gh)
     - Next steps: ...
     ```
   - If the user corrected your approach this session, add a note to `docs/lessons.md`.
   - If durable project facts changed, update `.claude/memory/`.
   - If a notable architectural decision was made, add an ADR in `docs/decisions/NNNN-*.md`.
   - **Regenerate `docs/HANDOFF.md` by running `/handoff`** — the single source of HANDOFF generation. Do NOT restate or duplicate its logic here. This is mandatory: a wrap-up that leaves `HANDOFF.md` full of `{TODO}` placeholders has not finished. After `/handoff` returns, verify its output — confirm `grep -c '{TODO}' docs/HANDOFF.md` is `0` (the carry-over `## Open questions` / `## Environment notes` sections may legitimately keep a `{TODO}`, but the state sections must be filled).

4. **Run quick checks** and report status (skip silently if the `backend` container is down):
   ```bash
   docker compose exec -T backend ruff check . || true
   docker compose exec -T backend pytest -q || true
   bash scripts/check_stubs.sh || true   # residual stubs vs docs/STUBS.md
   ```
   Report any residual `# STUB:` / `NotImplementedError` and whether each is logged in `docs/STUBS.md` (per @.claude/rules/no-stubs.md).

5. **Show the working state** and enumerate the doc files this command touched so none is silently left behind (`docs/WORKLOG.md`, `docs/HANDOFF.md`, and any `docs/lessons.md` / ADR / `.claude/memory/` edits):
   ```bash
   git status -sb
   git --no-pager diff --stat
   ```

6. **Propose** a Conventional-Commits message for the pending changes (it MUST include the doc files from step 5 — WORKLOG + HANDOFF + lessons/ADR). Do NOT commit or push automatically; the user reviews the diff and commits.

7. **Remind the rules:** never push to `main`; open work via `/create-pr`. Finish with a one-line "session wrapped" summary and the suggested next step.

> Pair with `/create-pr` when ready to open a PR. Tests/lint/stub failures here are informational — fix via the normal pipeline, not inside this command.

<!-- Last reviewed/updated: 2026-06-05 (HANDOFF step delegates cleanly to /handoff, no logic restatement) -->
