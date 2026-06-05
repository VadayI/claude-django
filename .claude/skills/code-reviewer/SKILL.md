---
name: code-reviewer
description: "[claude-django] Code-review methodology and checklist for Django/DRF (backend-only). Activate when reviewing changes before a PR (used by the reviewer agent)."
---

# Code Reviewer

Systematic review focused on correctness, design, and maintainability. Read the actual changed files, not only the diff.

> **Security is out of scope here** — authorization/IDOR/401/403, secret leakage, and sensitive-field exposure belong to the `security-reviewer` skill (used by the `security-scanner` agent), which runs in parallel in the Quality Gate. Do not duplicate those checks; keep this review on design, correctness, and maintainability.

## Severity

- 🔴 **Critical** — bug, architecture violation, missing test for key behavior. Blocks merge.
- 🟡 **Important** — should fix before merge (duplication, unclear naming, weak test, over-engineering).
- 🟢 **Suggestion** — nice-to-have.

## Django/DRF checklist

- Thin views, fat models; validation in serializers; logic not duplicated in views.
- No N+1 (`select_related`/`prefetch_related`); queries bounded; indexes where filtered/sorted.
- Migrations reversible; no edits to applied migrations; data migrations tested.
- **File size** (@.claude/rules/code-style.md): no source file over **800 lines** (migrations exempt) — `scripts/check_file_size.sh` is the hard gate; flag files in the 600-800 range as 🟡 with a suggested split seam.

### Silent-failure anti-patterns (flag explicitly — these slip past green tests)

These compile, lint clean, and pass happy-path tests, yet ship broken behavior. Treat as 🔴/🟡, not nits:

- **Broad `except Exception` / bare `except:` that swallows the error and still returns success.** A per-row handler that appends to an `errors[]` list and returns 200 makes a corrupt batch indistinguishable from a clean one. Demand a machine-readable failure signal (partial-success status, a `failed` count, or non-2xx on hard errors); narrow the except to expected types.
- **Writing to the DB without validating that the content matches the declared format/shape** (e.g. trusting `format=csv` without verifying the actual columns/required fields) — silently creates empty/junk rows. Require header/required-field validation; reject mismatches with 400.
- **Unguarded `perform_create`/`save()` where a uniqueness conflict is expected** — a serializer `UniqueValidator` is read-then-write, not atomic; concurrent writes raise `IntegrityError` → unhandled 500 instead of 409. Require `try/except IntegrityError` mapping to 409.

## Process rules

- PR scope: one logical change per PR; the full production frontend lives in a separate repo and is never mixed into a backend PR.
- Tests cover new behavior: success + 400/401/403/404/409 + edge cases.
- **Simplicity & surgical changes** (@.claude/rules/simplicity-surgical.md): flag over-engineering (premature/speculative abstractions, unrequested configurability, 200 lines where 50 would do) and drive-by edits (refactors or reformatting of code the task didn't touch) as 🟡 — every changed line must trace to the PR's stated request.

Return findings as: file, line, severity, comment. Do not edit code — report only.
<!-- Last reviewed/updated: 2026-06-05 (security dedup → security-reviewer; synced with reviewer agent: 800-line, silent-failure, surgical) -->
