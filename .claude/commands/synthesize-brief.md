---
model: sonnet
description: "[claude-django] Synthesize/update docs/PROJECT.md from docs/** input documents (via feature branch + PR)."
---

Recursively synthesize/update `docs/PROJECT.md` from input documents in `docs/**`. Always commits via feature branch + PR — NEVER direct push to `main`.

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

2. **Delegate to `brief-synthesizer`** (`subagent_type: "brief-synthesizer"`). Pass the discovered file list. The agent produces `docs/PROJECT.md`. Three fields are **required** — the brief is NOT complete until all three are resolved:

   - **Maturity stage** (`demo / prototype / PoC / MVP / production / other`) — controls pipeline depth and Quality Gate rigour (@.claude/rules/project-maturity.md). If absent from all source documents, it becomes the **first Open Question** and the orchestrator asks the user via `AskUserQuestion` (options: demo / prototype / PoC / MVP / production / other) before the brief is finalized.
   - **Contract** (`CONTRACT_VERSION=vX.Y.Z`, repo `VadayI/claude-api-contract`) — which `claude-api-contract` tag this backend consumes. Without it `/preflight` will fail. If absent from sources, add as Open Question: "Which claude-api-contract version does this backend consume?".
   - **Definition of Done §7** — standard Django CI gates (pre-filled) **plus** project-specific criteria agreed with the team. If no source provides project-specific criteria, ask the user explicitly — the section must never remain `{TODO}`. "None beyond standard gates" is a valid explicit answer.

   The fixed 9 sections remain: Purpose, Domain, Scope (in/out), Key requirements, Non-functional requirements, Constraints, Stakeholders, **Definition of Done (§7)**, Open questions, plus a *Source documents* table.

3. **Branch + PR** (orchestrator handles git — agent is forbidden from running git):
   - `git checkout main && git pull`
   - `git checkout -b docs/synthesize-brief-$(date +%Y%m%d)`
   - Agent has written `docs/PROJECT.md`; verify it exists and is non-empty.
   - `git add docs/PROJECT.md`
   - `git commit -m "docs: synthesize project brief from docs/"`
   - `git push -u origin docs/synthesize-brief-$(date +%Y%m%d)`
   - `gh pr create --fill --title "docs: synthesize project brief"`

4. **Summary.** Invocation logging is automatic (`UserPromptExpansion` hook). Print: how many source documents were read, which were `unprocessed`, the PR URL, whether maturity stage and DoD were resolved or remain as Open Questions, and the next step (review the PR diff before merging).

## Hard limits

- Never direct-commit or push to `main` — always a feature branch + PR.
- Never invent facts not in source documents. If a section has no source, the agent writes `TODO — source missing` and the *Source documents* table makes the gap auditable. **Exception:** the standard DoD gates are pre-filled from the template (they are always required, not invented).
- Never write outside `docs/PROJECT.md` (no edits to source docs, no new files, no `templates/` writes).
- The brief is incomplete while any of the three required fields (maturity stage, contract, DoD project-specific criteria) remains unresolved — surface them to the user before closing.

> Run AFTER `/bootstrap` Mode A, BEFORE `/preflight` and the first feature pipeline. Re-runnable as briefs evolve — each run opens its own dated PR.

<!-- Last reviewed/updated: 2026-06-08 -->
