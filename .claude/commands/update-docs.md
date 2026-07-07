---
model: sonnet
description: "[claude-django] Update project documentation to match the latest changes."
---

You update project documentation to match the latest changes.

## Input
Optional `$ARGUMENTS`: a domain/feature to scope. If empty, infer from the current diff.

## Steps
1. Review what changed:
   ```bash
   git diff --stat
   ```
2. Dispatch the `docs-writer` agent (`subagent_type: "docs-writer"`) to:
   - update `docs/api/<domain>.md` for any added/changed endpoint (method, path, body, response, codes, permissions, example);
   - record a `docs/decisions/NNNN-*.md` ADR if a notable decision was made;
   - refresh `README.md` only if commands/stack changed.

   > `docs/WORKLOG.md` and `docs/lessons.md` are owned by `/wrap-up` (the session-summary chronicle) — do NOT append them here, to avoid duplicate entries. This command syncs reference docs (api / README) + ADRs only; an ADR is a unique numbered file, so recording one here carries no duplication risk.
3. Summarize which docs were updated. Do not open a PR unless asked (use `/create-pr`).
<!-- Last reviewed/updated: 2026-05-27 -->
