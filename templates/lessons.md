# Lessons learned — {SLUG}

Running log of non-obvious findings, anti-patterns, and surprises encountered while building this project. Append-only — never delete an entry, mark it `~~obsolete~~` if it no longer applies. Maintained by the `docs-writer` agent at `/wrap-up` and `/update-docs`.

Each entry: one paragraph, dated, with a one-line title.

## Format

```markdown
## YYYY-MM-DD — <one-line title>

What happened, why it surprised us, what we will do differently next time. Link to the PR / commit / ADR if relevant.
```

## Entries

## {DATE_ISO} — Bootstrap completed

Initial scaffold from [`claude-django`](https://github.com/VadayI/claude-django) — Django/DRF stack, drf-spectacular wired, CI gates (ruff + stubs + OpenAPI drift + per-app README) live. No business logic yet; first feature should follow the standard pipeline (`ba` → `api-architect` → `tester` → `django-developer`).

> This is a seed entry showing the expected format. Newer entries go below, one per session / lesson / surprise.

<!-- New entries appended below. Newest at the bottom. -->

<!-- Last reviewed/updated: 2026-05-30 (P2: title slug + seed entry) -->
