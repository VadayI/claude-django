---
model: sonnet
---

Recursively synthesize/update `docs/PROJECT.md` from input documents in `docs/**`. Always commits via feature branch + PR — NEVER direct push to `main`.

## Log

```bash
python scripts/log-cmd.py /synthesize-brief $ARGUMENTS
```

## Input

Optional `$ARGUMENTS`:
- nothing -> full re-synthesis of all input documents in `docs/**`.
- a subpath (e.g. `docs/briefs/`) -> limit input discovery to that subtree.

## Steps

1. **Discovery.** List files under `docs/**` EXCLUDING service folders and files (they are project bookkeeping, not source briefs):
   - Folders: `docs/api/`, `docs/decisions/`, `docs/plans/`
   - Files: `docs/WORKLOG.md`, `docs/STUBS.md`, `docs/lessons.md`, `docs/APP_README.md`, `docs/PROJECT.md` (the output itself)

   Supported extensions:
   - `.md`, `.txt` — read via `Read`.
   - `.pdf` — invoke `anthropic-skills:pdf` skill.
   - `.docx` — invoke `anthropic-skills:docx` skill.
   - Images (`.png`, `.jpg`, `.jpeg`, `.webp`) — described visually by the multimodal agent.

   Any other binary extension (`.xlsx`, `.zip`, `.fig`, ...) is listed under *Source documents* with the note `unprocessed: unsupported format`.

2. **Delegate to `brief-synthesizer`** (`subagent_type: "brief-synthesizer"`). Pass the discovered file list. The agent produces `docs/PROJECT.md` with the fixed 9 sections: Purpose, Domain, Scope (in), Scope (out), Key requirements, Non-functional requirements, Constraints, Stakeholders, Open questions, plus a *Source documents* table.

3. **Branch + PR** (orchestrator handles git — agent is forbidden from running git):
   - `git checkout main && git pull`
   - `git checkout -b docs/synthesize-brief-$(date +%Y%m%d)`
   - Agent has written `docs/PROJECT.md`; verify it exists and is non-empty.
   - `git add docs/PROJECT.md`
   - `git commit -m "docs: synthesize project brief from docs/"`
   - `git push -u origin docs/synthesize-brief-$(date +%Y%m%d)`
   - `gh pr create --fill --title "docs: synthesize project brief"`

4. **Log + summary.** Append to `.claude/memory/command-log.jsonl` and print: how many source documents were read, which were `unprocessed`, the PR URL, and the next step (review the PR diff before merging — the agent may have introduced `TODO — source missing` markers that need human-supplied facts).

## Hard limits

- Never direct-commit or push to `main` — always a feature branch + PR.
- Never invent facts not in source documents. If a section has no source, the agent writes `TODO — source missing` and the *Source documents* table makes the gap auditable.
- Never write outside `docs/PROJECT.md` (no edits to source docs, no new files, no `templates/` writes).

> Run AFTER `/bootstrap` Mode A, BEFORE `/preflight` and the first feature pipeline. Re-runnable as briefs evolve — each run opens its own dated PR.

<!-- Last reviewed/updated: 2026-05-29 -->
