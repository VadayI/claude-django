---
model: sonnet
---

Change the output language for this project after bootstrap. Idempotent — running it twice with the same answer leaves the repo unchanged.

## Log

```bash
python scripts/log-cmd.py /set-language $ARGUMENTS
```

## Input

Optional `$ARGUMENTS`: language code (`en`, `uk`, `pl`, `de`) or native name (`українська`, `Deutsch`, …). If empty, ask via `AskUserQuestion`.

## Steps

1. **Detect current language**:
   - If `.claude/rules/output-language.md` exists, read its first line — the native name is the word after "Always respond in ". Show it as "current: <native>".
   - If not, current language is **English** (the default).

2. **Ask the user** via `AskUserQuestion` (header `Language`):
   - **English** — clears the language override and reverts to the project default.
   - **Українська**
   - **Німецька**
   - **Polski**
   - The harness adds "Other" automatically; the user can type any native name there (`Deutsch`, `Español`, `日本語`, …).

   Highlight the currently-detected language in your question text so the user sees what is set right now.

3. **Apply the change** (orchestrator dispatches `devops`):
   - **If the user picked English**:
     - Delete `.claude/rules/output-language.md` (if present).
     - Remove the line `@.claude/rules/output-language.md` from `CLAUDE.md` (if present). Do not touch other lines.
   - **If the user picked any other language**:
     - Copy `templates/output-language.md` → `.claude/rules/output-language.md`, replacing the literal token `{LANGUAGE_NATIVE}` with the chosen native name. Replace **both** occurrences.
     - Ensure `@.claude/rules/output-language.md` is present in the `@.claude/rules/*.md` block at the top of `CLAUDE.md`. Add it after `@.claude/rules/preflight.md` if missing; do nothing if already there.

4. **Verify**:
   - Re-read `.claude/rules/output-language.md` (or confirm its absence for English).
   - The body must NOT contain the literal `{LANGUAGE_NATIVE}` placeholder.
   - `grep '^@.claude/rules/output-language.md$' CLAUDE.md` returns the expected count (1 for non-English, 0 for English).

5. **Log + summary** — append the invocation to `.claude/memory/command-log.jsonl`:
   ```bash
   mkdir -p .claude/memory
   printf '{"ts":"%s","cmd":"/set-language","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
   ```
   Then print: previous language → new language, files changed (`.claude/rules/output-language.md`, `CLAUDE.md`), and the reminder that the change takes effect in the **next** message (the current orchestrator context is already loaded).

## Hard limits

- No `git commit` — leave changes staged so the user can review the diff before committing.
- Never touch application source code (`backend/apps/`, `backend/config/`, `tests/`).
- Never invent a native name the user did not pick; if "Other" was used and the user typed something ambiguous, ask one follow-up to confirm