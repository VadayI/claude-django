# Testing policy

## Stack

- `pytest` + `pytest-django`, `factory_boy`, `pytest-cov`.
- DRF `APIClient` / `APIRequestFactory` for endpoint tests.
- Test DB — real PostgreSQL in Docker (parity with staging), `@pytest.mark.django_db`.

## Structure

- AAA: Arrange / Act / Assert.
- Names: `test_<subject>_<condition>_<expectation>`.
- Factories instead of manual `Model.objects.create(...)`.
- Separate tests for: success, validation (400), authentication (401), authorization (403), not found (404), conflict (409).

## What to test / what to skip

Single owner of the list: @.claude/rules/tdd.md ("What to test / what to skip") — follow it, do not re-copy it here.

## Order (TDD)

First a failing test (RED), then code (GREEN), then refactor. Details — @.claude/rules/tdd.md.

## Commands

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=apps --cov-report=term-missing
docker compose exec backend ruff check .
```
<!-- Last reviewed/updated: 2026-07-07 (what-to-test delegated to tdd.md — audit batch B) -->
