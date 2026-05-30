# Plan 0005 — `/handoff` command + repo-conflict probe + auditor reads HANDOFF (P3)

> Author: orchestrator session, 2026-05-30. Source: P3 backlog. Reframes the original "WSL gate Skill" (a misnamed non-issue: environment.md already gates WSL2 conditionally) into a third concrete polish item: the `auditor` agent should read `docs/HANDOFF.md` so `/audit` surfaces stale "Next step" and open questions in its suggestions.

## Scope (P3)

1. **`/handoff` command** — new file `.claude/commands/handoff.md`. Reads current state (git status/log, current branch, open PRs via `gh pr list`, last CI status via `gh pr checks`, `docs/STUBS.md` count, `docs/todo.md` Now/Next sections) and rewrites `docs/HANDOFF.md` from a structured template. Read-only on everything except `docs/HANDOFF.md`. Pairs with `/wrap-up` (WORKLOG + lessons + lint/tests + commit suggestion) and `/audit` (suggests next command from state). Each invocation appends to `.claude/memory/command-log.jsonl` via `scripts/log-cmd.py`.

2. **Pre-bootstrap repo-name conflict probe** (`bootstrap.md` Step 1 + Hard preflight) — before `gh repo create` runs, probe `gh repo view "$OWNER/$SLUG"`. If 200 (repo exists), STOP with new flag `REPO_ALREADY_EXISTS` and remediation: either pick a different slug, or `cd` into the existing repo (so detection routes to Mode B). Today the spec relies on `git remote get-url origin` which only catches a previous local `gh repo create` attempt — it doesn't catch the case where the user manually created the repo on GitHub (the exact path the carlsberg run took, where the user manually created the repo midway through bootstrap).

3. **`auditor` agent reads `docs/HANDOFF.md`** — small edit to `.claude/agents/auditor.md` Inputs section. Add HANDOFF.md to the read list; add a new rule near the top of the Suggestion rules ladder: **"HANDOFF.md `Next step` is concrete and not yet done → propose that as primary"**. Surface any open `## Open questions` items in the Secondary list (up to 3). Means `/audit` becomes the natural first command after every session-resume.

## Out of scope (true P4, ideas)

- A `/handoff --append` mode that appends a dated snapshot instead of rewriting.
- An `/audit` command that auto-runs `/handoff` first to refresh state before suggesting.
- `gh pr list --json statusCheckRollup` parsing in `/handoff` to show a one-line PR/CI summary in HANDOFF.

## Files touched

- `.claude/commands/handoff.md` (new)
- `.claude/commands/bootstrap.md` (Step 1 + Hard preflight remediation table — new `REPO_ALREADY_EXISTS` flag)
- `.claude/agents/auditor.md` (Inputs + Suggestion rules)
- `README.md` (Commands count 13 → 14 + cheat-sheet entry for `/handoff`)
- `docs/WORKLOG.md` (record this batch)

## Risks

- `/handoff` overwrites `docs/HANDOFF.md`. Mitigation: the command's spec says "regenerate from current state" and the WORKLOG is the append-only chronicle. Users who want to preserve a HANDOFF snapshot can commit before running. We don't append-mode for now.
- The `REPO_ALREADY_EXISTS` probe slows Step 1 by ~1 s (one extra API call). Acceptable for the safety it adds.
- `auditor` Inputs list grows — Bash output stays bounded because HANDOFF.md is short (< 100 lines by design).

## Verification

After each file: `wc -c`, grep for `REPO_ALREADY_EXISTS`, `handoff`, `HANDOFF.md` (in auditor), and the new auditor rule key phrase.

## Commit

Single commit in `main`:

```
feat(bootstrap): /handoff command + repo conflict probe + auditor reads HANDOFF

- .claude/commands/handoff.md (new): regenerate docs/HANDOFF.md from current git/PR/CI state
- bootstrap.md Step 1: pre-create probe `gh repo view $OWNER/$SLUG`; STOP REPO_ALREADY_EXISTS with remediation
- auditor.md: add docs/HANDOFF.md to Inputs; promote HANDOFF "Next step" to primary suggestion when set
- README: commands 13 -> 14, add /handoff to cheat-sheet
- docs: plan 0005 + WORKLOG entry
```
