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

## What is MANDATORY to test

- custom model logic, serializer validators, permissions;
- every endpoint: codes, response shape, DB state after the request;
- pagination, filters, sorting, throttling where present;
- edge and error cases.

## What can be skipped

- standard CRUD with no customization;
- auto-migrations without data logic;
- trivial `__str__`.

## Order (TDD)

First a failing test (RED), then code (GREEN), then refactor. Details — @.claude/rules/tdd.md.

## Commands

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=apps --cov-report=term-missing
docker compose exec backend ruff check .
```
<!-- Last reviewed/updated: 2026-05-27 -->
