---
model: sonnet
description: "[claude-django] Change the project's output language after bootstrap (idempotent)."
---

Change the output language for this project after bootstrap. Idempotent — running it twice with the same answer leaves the repo unchanged.

## Input

Optional `$ARGUMENTS`: language code (`en`, `uk`, `pl`) or native name (`українська`, …). If empty, ask via `AskUserQuestion`.

## Steps

1. **Detect current language**: run `python scripts/ai/project_state.py --root . --language` and show `language` / `status` as "current: <native>".
   - `legacy` or `identical` (only the Claude-only `.claude/rules/output-language.md` holds the choice): move it first with `python scripts/ai/project_state.py --root . --language --apply` — it creates the shared `docs/ai/overrides/output-language.md` and leaves a pointer at the old path.
   - `conflict`: nothing is written; show both files and let the user's current choice decide (step 2).
   - `none`: current language is **English** (the default).

2. **Ask the user** via `AskUserQuestion` (header `Language`):
   - **English** — clears the language override and reverts to the project default.
   - **Українська**
   - **Polski**
   - The harness adds "Other" automatically; the user can type any native name there (`Deutsch`, `Español`, `日本語`, …).

   Highlight the currently-detected language in your question text so the user sees what is set right now.

3. **Apply the change** (orchestrator dispatches `devops`); only the shared file is written — Claude and Codex read it through AGENTS.md:
   - Copy `templates/output-language.md` → `docs/ai/overrides/output-language.md`, replacing the literal token `{LANGUAGE_NATIVE}` (both occurrences) with the chosen native name — `English` included: an explicit English file keeps a migration pointer valid instead of leaving it orphaned. If none was persisted and the user picked English, writing nothing is also fine.
   - On a `conflict`, after writing the shared file run `python scripts/ai/project_state.py --root . --language --apply --keep-shared`: the legacy preference becomes the pointer, so one writable preference remains.
   - Never edit `CLAUDE.md` or create a new `.claude/rules/output-language.md`.

4. **Verify**: `python scripts/ai/project_state.py --root . --language` reports `status` `canonical` (or `none` for English) and the chosen `language`; the shared file does NOT contain the literal `{LANGUAGE_NATIVE}`.

5. **Summary** — invocation logging is automatic (`UserPromptExpansion` hook), no manual append. Print: previous language → new language, files changed (`docs/ai/overrides/output-language.md`, and `.claude/rules/output-language.md` if migrated), and the reminder that the change takes effect in the **next** message (the current orchestrator context is already loaded).

## Hard limits

- No `git commit` — leave changes staged so the user can review the diff before committing.
- Never touch application source code (`backend/apps/`, `backend/config/`, `tests/`).
- Never invent a native name the user did not pick; if "Other" was used and the user typed something ambiguous, ask one follow-up to confirm
