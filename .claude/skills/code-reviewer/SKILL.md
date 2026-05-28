---
name: code-reviewer
description: Code-review methodology and checklist for Django/DRF + React. Activate when reviewing changes before a PR (used by the reviewer agent).
---

# Code Reviewer

Systematic review focused on correctness, design, and maintainability. Read the actual changed files, not only the diff.

## Severity

- 🔴 **Critical** — bug, security/authz hole, architecture violation, missing test for key behavior. Blocks merge.
- 🟡 **Important** — should fix before merge (duplication, unclear naming, weak test).
- 🟢 **Suggestion** — nice-to-have.

## Django/DRF checklist

- Thin views, fat models; validation in serializers; logic not duplicated in views.
- `permission_classes` explicit; anon→401, other user→403; no IDOR (object-level checks).
- No N+1 (`select_related`/`prefetch_related`); queries bounded; indexes where filtered/sorted.
- Migrations reversible; no edits to applied migrations; data migrations tested.
- Serializers don't leak sensitive fields; owner set server-side, not from client.
- No secrets in code; env-only config.

## React mini-client checklist

- API calls live in `src/api/`; no business logic in components; no bare URLs.

## Process rules

- PR-per-layer respected (mini-frontend never mixed into a backend PR; full production frontend is a separate repo).
- Tests cover new behavior: success + 400/401/403/404/409 + edge cases.
- Simplicity: flag premature abstractions.

Return findings as: file, line, severity, comment. Do not edit code — report only.
<!-- Last reviewed/updated: 2026-05-27 -->
