---
model: sonnet
description: "[claude-django] Workflow audit — read the command log + live state and propose what to run next (dispatches `auditor`)."
---

You run a workflow audit — read the command log and the live state, then propose what to run next. Dispatch the `auditor` agent and relay its findings; never decide for the user.

## Input
Optional `$ARGUMENTS`: a focus area — `git`, `ci`, `docs`, `gates`, or empty (full audit).

## Steps

0. **Sync preflight — always first.** Check that previous changes are committed and synchronized with GitHub:
   ```bash
   python scripts/ai/git_lifecycle.py --json inspect --fetch
   ```
   Synchronized means: no staged, unstaged or untracked paths in `working_tree`;
   `head` equals the branch's remote-tracking tip (`remote_tracking`, or
   `base_refs.remote_tracking` on the base branch); no blockers; PR evidence
   `VERIFIED`. Anything else (for example `LOCAL_CHANGES`, `COMMITTED_UNPUSHED`,
   `BEHIND_REMOTE`, `DIVERGED`, `LOCAL_COMMITS_ON_BASE`, `PR_HEAD_MISMATCH`,
   `NOT_VERIFIED`, a pending cleanup) is reported as the first finding with the
   exact paths, commits and next step. Then ask the user whether to finalize first
   (`/wrap-up`: commit, push, PR) or audit the current state anyway. The audit
   itself never commits, pushes, pulls or cleans; the fetch only updates
   remote-tracking refs. Unavailable gh or network is `NOT_VERIFIED`, never
   synchronized.

1. **Dispatch `auditor`** (`subagent_type: "auditor"`) with the focus from `$ARGUMENTS`. It reads `.ai-runtime/command-log.jsonl` + live state and produces a primary suggestion + up to 3 secondaries + a recent-activity table.

2. **Relay** the auditor's report verbatim and finish with one line: `next: <primary command>`.

## Hard limits
- Read-only — no commits, no edits, no secrets in output; the preflight fetch only updates remote-tracking refs.
- Suggestions, not auto-actions — the user decides.

> Pairs with all other commands; the `UserPromptExpansion` log hook (`scripts/policy/log_command.py`) records every invocation into the same log, so this can see them.

<!-- Last reviewed/updated: 2026-09-28 (step 0: sync preflight via git_lifecycle.py inspect --fetch); 2026-07-07 (Log step removed — UserPromptExpansion hook logs; audit batch D) -->
