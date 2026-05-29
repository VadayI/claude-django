---
model: sonnet
---

You run the **project kickoff preflight** — a hard gate that verifies agents have the inputs and access to build correctly, BEFORE any feature work. Spec: `@.claude/rules/preflight.md`. Invoke at the start of a new project, or whenever access/inputs are in doubt.

## Log

```bash
python scripts/log-cmd.py /preflight $ARGUMENTS
```

## Contract
Hard gate: if a CRITICAL item is missing, STOP — do not start the feature pipeline. Report a checklist and ask the user or fix access. Never print secret values.

## Input
Optional `$ARGUMENTS`: a scope — `brief`, `stack`, `docs`, `github`. Default: all.

## Steps

1. **Access checks** — dispatch `devops` (`subagent_type: "devops"`) to verify, read-only:
   - `context7` MCP reachable (`resolve-library-id` for "django"); `CONTEXT7_API_KEY` set (report set/unset, never the value);
   - `gh auth status` authenticated (via `GITHUB_PERSONAL_ACCESS_TOKEN` env OR stored creds — either is fine) and `gh repo view` succeeds for the project repo. NOTE: if the env var is set, `gh auth login` will refuse to store separate creds — that is EXPECTED, not a failure; auth is green as long as `gh auth status` succeeds. Also verify that `gh` here means **Linux `gh` in WSL2**, not a Windows `gh.exe` from `winget`.
   - tech stack declared (CLAUDE.md / README) and `backend/pyproject.toml` deps resolvable.

2. **Brief / stack comprehension** — dispatch `ba` (`subagent_type: "ba"`) to confirm there is a usable project brief/description (`docs/PROJECT.md`, README, or user-provided) and that the declared stack is unambiguous. If the brief is missing/vague, `ba` returns the specific questions to ask.

3. **Report** a readiness checklist grouped: Brief · Stack · Library docs (Context7) · GitHub access — each ✅/❌ with what was observed.

4. **Gate.** If any ❌ CRITICAL → STOP: present the gaps and, for a missing brief, ask the user (via the orchestrator's `AskUserQuestion`). Do NOT start `api-architect` / `tester` / `django-developer`.

5. If all ✅ → report "preflight green — ready to start the feature pipeline" and hand back to the orchestrator.

## Hard limits
- No code / schema / migration work in this command.
- Never print secret values; only set/unset.
- Context7 may be waived only on explicit user override (note: APIs will be unverified against current docs).

> Pairs with `/doctor` (environment). Run `/doctor` first on a fresh machine, then `/preflight` before the first feature.

<!-- Last reviewed/updated: 2026-05-27 -->
