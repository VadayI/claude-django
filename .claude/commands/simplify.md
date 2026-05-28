---
model: sonnet
---

You simplify the most recent changes without altering behavior (Code Simplifier). Tests must stay green.

## Log

```bash
mkdir -p .claude/memory && printf '{"ts":"%s","cmd":"/simplify","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
```

## Input
Optional `$ARGUMENTS`: a path/glob to limit scope. If empty, use the current diff.

## Steps
1. Show what you'll inspect:
   ```bash
   git diff --stat
   git diff
   ```
   If `$ARGUMENTS` is given, limit to those files.
2. Identify simplification opportunities (no behavior change):
   - remove duplication, dead code, needless `if`/nesting (early returns);
   - extract logic to the model/service where it belongs (thin views, fat models);
   - replace magic numbers with `TextChoices`/constants;
   - simplify serializers/querysets; remove premature abstractions.
3. Apply minimal edits. Do NOT add features or change the public contract.
4. Verify nothing broke:
   ```bash
   docker compose exec backend ruff check . && docker compose exec backend ruff format .
   docker compose exec backend pytest
   ```
5. Summarize: what was simplified and why, and confirm tests are green.

For anything beyond a quick pass, delegate to the `django-refactoring-expert` agent (under green tests).
<!-- Last reviewed/updated: 2026-05-27 -->
