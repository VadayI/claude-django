---
model: sonnet
---

Update a **derived project** (one bootstrapped from `claude-django`) to a newer version of the template config — agents, commands, skills, rules, and CI gate scripts — overwriting only template-owned files and preserving everything the project owns. Dispatches `template-sync`, then opens a **PR** (derived projects are PR-only, `@.claude/rules/git-operations.md`). Background: ADR `0014`; derived projects carry a pinned copy with no automatic upgrade channel (ADR `0002`).

## Log

```bash
python scripts/log-cmd.py /update-from-template $ARGUMENTS
```

## Input

`$ARGUMENTS` (all optional):
- an **upstream repo URL or git ref** — defaults to the URL recorded in `.claude/memory/template-sync.json`, else `https://github.com/VadayI/claude-django.git` at its default branch HEAD.
- **`--dry-run`** — report what WOULD change without writing any files.

## Preconditions

- This is a **derived project**, not the template itself: `.claude/` exists; treat the presence of `templates/` + `docs/decisions/0001-*` + no `backend/` as "this is the template repo" -> STOP.
- Working tree is clean (or only intended changes). If dirty -> STOP and ask the user to commit/stash first.
- `git` available; network access to clone the upstream.

## Steps

1. **Log** the invocation (above).
2. **Clone upstream** (read-only) to a temp dir:
   ```bash
   rm -rf /tmp/claude-django && git clone --depth 1 <upstream-url> /tmp/claude-django
   git -C /tmp/claude-django rev-parse HEAD   # the SHA being synced to
   ```
3. **Feature branch** (skip on `--dry-run`): off fresh `main` —
   ```bash
   git checkout main && git pull
   git checkout -b chore/sync-template-$(date +%Y%m%d)
   ```
4. **Dispatch `template-sync`** (`subagent_type: "template-sync"`) with `$UPSTREAM=/tmp/claude-django` and the dry-run flag if present. It performs the categorized sync (template-owned overwrite · merge-by-hand diff · project-owned untouched), wires any new gate scripts into the live `scripts/` + `.github/workflows/backend-ci.yml`, writes `.claude/memory/template-sync.json`, and returns the change report.
5. **Relay** the report. Highlight the **merge-by-hand** items (CLAUDE.md / settings.json / live CI) so the user reviews those hunks.
6. **Open a PR** (skip on `--dry-run`): hand off to `docs-writer` (or run `/create-pr`) with a description summarizing the synced SHA range and the merge-by-hand files to review. **Never push to `main`.**

## Hard limits

- **PR-only** — no direct commit/push to `main`; the sync lands as a reviewable PR.
- Never overwrite project-owned files (`.claude/memory/*`, `.claude/rules/output-language.md`, `docs/**`, `backend/**`, `.env`).
- Never replace `CLAUDE.md` / `.claude/settings.json` / `.mcp.json` / live CI wholesale — additive merge only.
- Never print secret values.

> Pairs with `/doctor` (run it after the PR merges to re-verify the environment against the refreshed `environment.md`).
<!-- Last reviewed/updated: 2026-06-02 -->
