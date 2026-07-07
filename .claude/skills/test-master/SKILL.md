---
name: test-master
description: "[claude-django] Test strategy and coverage planning on top of TDD for Django/DRF — what to test, test pyramid, fixtures/factories, coverage targets. Activate when planning test strategy or reviewing coverage (complements pytest-tdd)."
---

# Test Master (strategy)

Sits above `pytest-tdd` (which is the RED-GREEN-REFACTOR mechanics). Here: WHAT to test and HOW MUCH.

## Test pyramid (for this stack)

- **Many**: unit tests for model methods, serializer validators, permissions, services.
- **Solid layer**: API feature tests via DRF `APIClient` per endpoint.
- **Few**: E2E browser flows (delegate to `qa`; browser tools come from the `playwright@claude-plugins-official` plugin).

## Coverage targets

- Business logic ~100%; overall high. Use `pytest-cov --cov=apps --cov-report=term-missing`.
- Coverage is a floor, not a goal — a green % with weak assertions is still weak.

## What MUST be covered / what to skip

Owned by @.claude/rules/tdd.md ("What to test / what to skip") — do not re-copy the list here. Async/migration testing specifics (Celery idempotency + enqueue, data-migration transform + reverse) live in @.claude/rules/migrations-tasks.md.

## Hygiene

- `factory_boy` factories over manual creation; AAA structure; descriptive names.
- Assert DB state after writes, not only the response. Use `assertNumQueries`/`django_assert_num_queries` to catch N+1 in tests.
<!-- Last reviewed/updated: 2026-07-07 (list delegated to tdd.md/migrations-tasks.md — audit batch B) -->
