---
model: sonnet
---

You update project documentation to match the latest changes.

## Log

```bash
python scripts/log-cmd.py /update-docs $ARGUMENTS
```

## Input
Optional `$ARGUMENTS`: a domain/feature to scope. If empty, infer from the current diff.

## Steps
1. Review what changed:
   ```bash
   git diff --stat
   ```
2. Dispatch the `docs-writer` agent (`subagent_type: "docs-writer"`) to:
   - update `docs/api/<domain>.md` for any added/changed endpoint (method, path, body, response, codes, permissions, example);
   - append a `docs/WORKLOG.md` entry (date, what was done, next steps);
   - record a `docs/decisions/NNNN-*.md` ADR if a notable decision was made;
   - if the user corrected the approach, capture it in `docs/lessons.md`;
   - refresh `README.md` only if commands/stack changed.
3. Summarize which docs were updated. Do not open a PR unless asked (use `/create-pr`).
<!-- Last reviewed/updated: 2026-05-27 -->
