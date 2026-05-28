---
model: sonnet
---

You wrap up the current work session: summarize, persist context to Git-tracked files, run checks, and prepare for commit. Invoke this when the user wants to finish work in this session / context window. This operationalizes principle 5 (Context in Git).

## Log

```bash
mkdir -p .claude/memory && printf '{"ts":"%s","cmd":"/wrap-up","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
```

## Input
Optional `$ARGUMENTS`: a short note about the session focus/outcome. If empty, infer from the session.

## Steps

1. **Summarize the session** — concise: what changed, key decisions, open items / blockers.

2. **Persist context** (delegate to `docs-writer`, or do it directly if trivial):
   - Append an entry to `docs/WORKLOG.md`:
     ```
     ## <YYYY-MM-DD> — <branch>
     - Done: ...
     - Decisions: ... (link ADR if any)
     - Next steps: ...
     ```
   - If the user corrected your approach this session, add a note to `docs/lessons.md`.
   - If durable project facts changed, update `.claude/memory/`.
   - If a notable architectural decision was made, add an ADR in `docs/decisions/NNNN-*.md`.

3. **Run quick checks** and report status (skip silently if the `backend` container is down):
   ```bash
   docker compose exec -T backend ruff check . || true
   docker compose exec -T backend pytest -q || true
   bash scripts/check_stubs.sh || true   # residual stubs vs docs/STUBS.md
   ```
   Report any residual `# STUB:` / `NotImplementedError` and whether each is logged in `docs/STUBS.md` (per @.claude/rules/no-stubs.md).

4. **Show the working state:**
   ```bash
   git status -sb
   git --no-pager diff --stat
   ```

5. **Propose** a Conventional-Commits message for the pending changes. Do NOT commit or push automatically.

6. **Remind the rules:** never push to `main`; open work via `/create-pr`. Finish with a one-line "session wrapped" summary and the suggested next step.

> Pair with `/create-pr` when ready to open a PR. Tests/lint/stub failures here are informational — fix via the normal pipeline, not inside this command.

<!-- Last reviewed/updated: 2026-05-27 -->
