---
name: test-master
description: Test strategy and coverage planning on top of TDD for Django/DRF — what to test, test pyramid, fixtures/factories, coverage targets. Activate when planning test strategy or reviewing coverage (complements pytest-tdd).
---

# Test Master (strategy)

Sits above `pytest-tdd` (which is the RED-GREEN-REFACTOR mechanics). Here: WHAT to test and HOW MUCH.

## Test pyramid (for this stack)

- **Many**: unit tests for model methods, serializer validators, permissions, services.
- **Solid layer**: API feature tests via DRF `APIClient` per endpoint.
- **Few**: E2E browser flows (delegate to `qa`/`playwright-e2e`).

## Coverage targets

- Business logic ~100%; overall high. Use `pytest-cov --cov=apps --cov-report=term-missing`.
- Coverage is a floor, not a goal — a green % with weak assertions is still weak.

## What MUST be covered

Per endpoint: success, 400 (validation), 401 (anon), 403 (other user), 404, 409 (conflict), pagination/filter/throttle where present, and IDOR.
Logic: custom model methods, serializer `validate_*`, permission classes, signals, Celery tasks (idempotency + enqueue), data migrations (transform + reverse).

## What to skip

Trivial CRUD with no customization, auto-migrations without data logic, trivial `__str__`.

## Hygiene

- `factory_boy` factories over manual creation; AAA structure; descriptive names.
- Assert DB state after writes, not only the response. Use `assertNumQueries`/`django_assert_num_queries` to catch N+1 in tests.
<!-- Last reviewed/updated: 2026-05-27 -->
