---
model: sonnet
---

Regenerate `docs/HANDOFF.md` — the rolling snapshot read by every new session ("where we are right now and what's next").

Pairs with `/wrap-up` (which still owns `docs/WORKLOG.md` append + `docs/lessons.md` + lint/tests + commit suggestion). `/handoff` ONLY touches `docs/HANDOFF.md`; nothing else, no commits, no pushes. Run it whenever the project state has shifted enough that the snapshot is stale — typically at session end after `/wrap-up`, after merging a PR, or before context-switching to a different branch.

## Log

```bash
python scripts/log-cmd.py /handoff $ARGUMENTS
```

## Input

Optional `$ARGUMENTS`:
- `--note "<text>"` — free-text note appended verbatim to the "Current state" section (use sparingly; the section is meant to be self-explanatory from git state).
- `--print` — render the would-be HANDOFF.md to stdout WITHOUT writing the file. Useful for previewing.

## Probes (read-only)

Run before writing anything. Capture each into a shell variable so the final rendering is deterministic.

```bash
BRANCH=$(git branch --show-current 2>/dev/null || echo "(detached)")
DIRTY=$(test -n "$(git status --porcelain 2>/dev/null)" && echo yes || echo no)
LAST_COMMIT_SHORT=$(git log -1 --format='%h %s' 2>/dev/null || echo "(no commits)")
LAST_COMMIT_ISO=$(git log -1 --format='%cI' 2>/dev/null || echo "")
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)

# Open PRs from this branch
PR_JSON=$(gh pr list --head "$BRANCH" --json number,title,state,url,statusCheckRollup 2>/dev/null || echo "[]")
PR_NUMBER=$(printf '%s' "$PR_JSON" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['number'] if d else '')")
PR_TITLE=$(printf '%s' "$PR_JSON" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['title'] if d else '')")
PR_URL=$(printf '%s' "$PR_JSON" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['url'] if d else '')")

# CI rollup for the head commit (if a PR exists)
CI_STATE=$(printf '%s' "$PR_JSON" | python -c "
import sys, json
d = json.load(sys.stdin)
if not d: print(''); sys.exit()
rollups = d[0].get('statusCheckRollup', [])
if not rollups: print('pending')
elif all(r.get('conclusion') == 'SUCCESS' for r in rollups): print('green')
elif any(r.get('conclusion') in ('FAILURE','TIMED_OUT','CANCELLED') for r in rollups): print('red')
else: print('mixed')
")

# Stub ledger count
STUB_COUNT=$(grep -rE 'STUB:|NotImplementedError\(.*STUB' backend/apps 2>/dev/null | grep -vE '/tests?/' | wc -l)

# Last schema change vs last code change (drift hint, not gate)
SCHEMA_LAST=$(git log -1 --format='%cI' -- docs/api/openapi.yml 2>/dev/null || echo "")
APPS_LAST=$(git log -1 --format='%cI' -- backend/apps 2>/dev/null || echo "")
```

## Generation

Render the new `docs/HANDOFF.md` from the probes above plus a few from-disk reads. Use these section rules:

### Current state

One paragraph derived from `BRANCH`, `DIRTY`, `AHEAD`, `BEHIND`, `LAST_COMMIT_SHORT`, `PR_NUMBER`, `CI_STATE`. Examples:

- `main` clean, in sync with origin -> "On `main`, working tree clean, in sync with `origin/main`. Last commit: `<sha> <subject>`."
- Feature branch with open PR + green CI -> "On `feat/<slug>`, PR #<n> open ([link](<url>)), CI green. <ahead> commits ahead of `origin/main`, working tree clean."
- Feature branch, no PR yet, dirty -> "On `feat/<slug>`, <ahead> commits ahead of `origin/main`, working tree DIRTY (uncommitted changes). No PR opened yet."

If `$ARGUMENTS` includes `--note "..."`, append the note in italics on a new line at the end of the paragraph.

### Last finished

The most recent merged PR (probe: `gh pr list --state merged --limit 1 --json number,title,mergedAt,url`). Render as `- PR #<n>: <title> -- merged YYYY-MM-DD ([link](<url>))`. If none yet, write `- (no PRs merged yet)`.

### In progress

Bullet list of: the current PR (if open), the current branch (if ahead of origin without a PR), and any non-empty `## Now` items from `docs/todo.md` (if present). If all are absent, write `- (nothing in flight)`.

### Next step (single)

Apply this decision order -- the first one that fires becomes the "Next step":

1. Working tree DIRTY -> "Commit or stash the working changes before switching context."
2. On `main` + no `/preflight` in `command-log.jsonl` for this slug -> "Run `/preflight` to verify build inputs before the first feature."
3. CI red on the open PR -> "Run `/fix-ci <PR>` to investigate the failure."
4. Open PR + green CI + no `/review-pr` recorded for this PR -> "Run `/review-pr <PR>`."
5. Feature branch ahead of origin without an open PR -> "Run `/create-pr` to push and open the PR."
6. `STUB_COUNT > 0` and any STUB older than 30 days -> "Triage the stub ledger (`docs/STUBS.md`); old STUBs need real implementations."
7. None of the above -> "Pick the next item from `docs/todo.md` (`## Next`); if empty, run `/audit` for a fresh suggestion."

### Open questions

Carry over the existing `## Open questions` section from the current `docs/HANDOFF.md` verbatim (do NOT regenerate from probes -- these are human-managed). If the file doesn't exist yet (first `/handoff` after bootstrap), seed with `- [ ] {TODO}` and a hint to fill them as they arise.

### Environment notes

Same carry-over rule as `## Open questions` -- preserve what was there.

## Write

```bash
# Render the assembled markdown to /tmp/handoff.md, then either print or write.
if [[ "$ARGUMENTS" == *"--print"* ]]; then
  cat /tmp/handoff.md
else
  mkdir -p docs
  mv /tmp/handoff.md docs/HANDOFF.md
  echo "v docs/HANDOFF.md regenerated."
fi
```

> Do NOT `git add` / `git commit` / `git push`. Leaving the file unstaged lets the user inspect the diff (`git diff docs/HANDOFF.md`) before deciding to commit it as part of `/wrap-up`.

## Hard limits

- Read-only on everything except `docs/HANDOFF.md` (or stdout under `--print`).
- Never invent state -- if a probe fails (e.g. no `gh` auth), say `(unavailable)` in the rendered section, never a plausible-looking placeholder.
- Never print secret values.
- The "Open questions" and "Environment notes" sections are carry-over only; the command does not delete or rewrite their content. Empty them yourself if a question is resolved.

> Pairs with `/wrap-up` (WORKLOG + lessons + lint/tests + commit suggestion) and `/audit` (next-command suggestion -- `auditor` reads `docs/HANDOFF.md` and may promote the "Next step" to its primary suggestion).

<!-- Last reviewed/updated: 2026-05-30 (P3: new command) -->
