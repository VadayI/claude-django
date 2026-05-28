---
model: sonnet
---

You run a workflow audit — read the command log and the live state, then propose what to run next. Dispatch the `auditor` agent and relay its findings; never decide for the user.

## Input
Optional `$ARGUMENTS`: a focus area — `git`, `ci`, `docs`, `gates`, or empty (full audit).

## Steps

1. **Log this invocation:**
   ```bash
   mkdir -p .claude/memory
   printf '{"ts":"%s","cmd":"/audit","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
   ```

2. **Dispatch `auditor`** (`subagent_type: "auditor"`) with the focus from `$ARGUMENTS`. It reads `.claude/memory/command-log.jsonl` + live state and produces a primary suggestion + up to 3 secondaries + a recent-activity table.

3. **Relay** the auditor's report verbatim and finish with one line: `next: <primary command>`.

## Hard limits
- Read-only — no commits, no edits, no secrets in output.
- Suggestions, not auto-actions — the user decides.

> Pairs with all other commands; they all write to the same log so this can see them.

<!-- Last reviewed/updated: 2026-05-27 -->
