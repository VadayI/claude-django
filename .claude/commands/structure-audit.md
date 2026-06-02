---
model: sonnet
---

Audit the codebase against the **800-line file limit** and propose concrete folder-splits for oversized files. Dispatches `code-structure-auditor` (read-only). Spec: `@.claude/rules/code-style.md` ("File size limit").

## Log

```bash
python scripts/log-cmd.py /structure-audit $ARGUMENTS
```

## Input

`$ARGUMENTS` (optional): a path scope (e.g. `apps/billing`) to narrow the audit. Empty = whole `backend/`.

## Steps

1. **Run the gate** to get the hard PASS/FAIL exactly as CI sees it:
   ```bash
   bash scripts/check_file_size.sh; echo "gate exit=$?"
   ```
2. **Dispatch `code-structure-auditor`** (`subagent_type: "code-structure-auditor"`) to measure every non-migration `*.py`, classify (🔴 >800 / 🟡 600-800 / 🟢 <600), and for each 🔴/🟡 propose a concrete split into a package of single-responsibility modules with stable `__init__.py` re-exports.
3. **Relay** its report. If any 🔴 exist, the next step is to hand the split plans to `django-refactoring-expert` (execute the split under green tests) — do not auto-refactor here.

## Hard limits

- Read-only — the auditor never edits, commits, or pushes; it only measures and proposes.
- Splits must preserve behavior and public import paths.

> Pairs with `check_file_size.sh` (the CI gate) — this command is the human-facing deep analysis + remediation plan behind the gate.
<!-- Last reviewed/updated: 2026-06-02 -->
