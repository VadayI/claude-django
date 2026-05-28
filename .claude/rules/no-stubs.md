# No stubs / no fake data in production code (enforced)

TDD's GREEN phase ("minimal code to pass") legitimately produces **temporary stubs** — hardcoded return values, `pass` bodies, fake datasets that satisfy a test without real logic. That is fine **inside the inner loop on a feature branch**. The risk is a stub surviving into a merged PR. This rule makes every stub **visible, tracked, and gated** so none reaches `main` unnoticed.

## Canonical marker (one greppable token)

- Any intentional placeholder in non-test code is marked with **`# STUB:`** plus a reason, e.g. `# STUB: returns fixed score until ranking service lands (#142)`.
- For unimplemented branches, prefer `raise NotImplementedError("STUB: <reason>")` — it is self-flagging (tests covering it fail).
- One token only (`STUB`) so `grep`/CI can find every one of them.

## Mock / fake data — tests only

Mock objects, fixtures and fake datasets live in **tests** (`factory_boy`, pytest fixtures) or in explicit `management` commands / seed scripts. **Production code (`apps/`) must never** contain inline fake data, hardcoded sample payloads, or imports of test factories. A hardcoded "example" response is a `# STUB:`.

## The ledger — `docs/STUBS.md`

Every `# STUB:` / `NotImplementedError("STUB: …")` in `apps/` MUST have a matching entry in `docs/STUBS.md`:

```
| File:line | Reason | Test that must force the real impl | Owner | Date |
|---|---|---|---|---|
| apps/ranking/services.py:42 | fixed score until ranking lands | test_ranking_orders_by_score | @VadayI | 2026-05-27 |
```

CI fails if a STUB exists in `apps/` whose file is not listed in `docs/STUBS.md` (see Enforcement). This is what *forces* recording it — unlogged stubs do not merge.

## Lifecycle

1. **GREEN (inner loop):** a stub is allowed only to get the current test green quickly. Mark it `# STUB:` immediately and add a `docs/STUBS.md` row.
2. **REFACTOR:** replace the stub with real logic, or — if deferred deliberately — keep it marked + logged and add the test that will later force the implementation.
3. **Quality Gate / PR:** `reviewer` and `security-scanner` explicitly flag any stub or hardcoded/fake data; unlogged stubs are 🔴. No `# STUB:` reaches `main` without a ledger entry; ideally none reaches `main` at all.

## Triangulation (prevent stubs from passing)

Defeat naive hardcoded returns by asserting behavior from **at least 2–3 distinct cases** (different inputs → different outputs), not a single example. `tester` writes triangulating cases so "return 42" cannot stay green. This is the strongest guard — a stub that can't pass the tests can't survive.

## Enforcement (the gate)

- **ruff** `FIX` rules (flake8-fixme) fail the build on leftover `TODO/FIXME/XXX/HACK` markers — secondary net for generic placeholders. Configured in `pyproject.toml` (`[tool.ruff.lint] select` includes `FIX`).
- **`scripts/check_stubs.sh`** (run in `backend-ci.yml` and locally): greps `backend/apps/` for `STUB` / `NotImplementedError`, excludes tests, and **exits non-zero** for any stub whose file is not recorded in `docs/STUBS.md`. Run it locally before pushing.
- **`/wrap-up`** reports residual STUBs at end of session.
- **Reviewer/security gate:** a stub in production logic (especially anything returning auth/permission/financial values) is a blocker, not a nit.

## Binds these agents (rule is auto-loaded)

- `django-developer` — when stubbing to go GREEN, immediately add the `# STUB:` marker and a `docs/STUBS.md` row; remove in REFACTOR when possible.
- `tester` — triangulate so hardcoded returns fail; add the test named in the ledger that will force the real implementation.
- `reviewer` / `security-scanner` — at the Quality Gate, flag every stub / fake-data / unlogged marker.

> Goal: stubs are a *visible, temporary* TDD tool — never silent technical debt that ships.

<!-- Last reviewed/updated: 2026-05-27 -->
