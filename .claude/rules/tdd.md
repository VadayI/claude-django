# TDD in Python (mandatory)

## Iron rule

**No line of production code without a failing test first.**

Cycle for each unit of functionality:

1. **RED** — write a test describing the expected behavior. Run it — it must fail for the expected reason (not due to an import/syntax error).
2. **GREEN** — write the MINIMAL code to make the test pass. No premature generalization.
3. **REFACTOR** — clean up the code and tests, tests stay green.

Repeat in small steps. One test → a bit of code → green → refactor.

> GREEN may use a temporary stub / hardcoded return to go green fast — but every stub must be marked `# STUB:` and recorded in `docs/STUBS.md`, and must never reach `main` unlogged. Rules and the CI gate: @.claude/rules/no-stubs.md.

## Double-loop TDD — outside-in at the API boundary

Our adaptation of Harry Percival's *Test-Driven Development with Python* ("Obey the Testing Goat"). We keep his discipline — test-first, Red-Green-Refactor, minimal code, **test behavior not implementation** — but the **outer loop is an API feature test, not a browser functional test**, because for a DRF backend the user-facing boundary is the HTTP endpoint.

- **Outer loop (acceptance / functional):** a failing DRF `APIClient` test for the endpoint. It is our functional test — it drives the feature and goes green only when the whole slice works end to end (status code, response shape, DB state, authorization).
- **Inner loop (unit):** fast RED → GREEN → REFACTOR cycles on model methods, serializer validators, permissions, and services — the small steps that make the outer test pass.

Flow per feature: **outer API test RED → run the inner unit loop (RED→GREEN→REFACTOR) until the outer test is GREEN → refactor.** This maps directly onto the pipeline below (`api-architect` sets the contract → `tester` writes the failing outer test → `django-developer` greens it via inner loops).

Why not the literal browser-driven double-loop here: browser/E2E tests are slow and flaky, so they make a poor tight RED driver — especially for an automated agent that iterates on test output and needs fast, deterministic signals; the backend ships before the frontend (separate PRs), so a browser FT cannot even go red first; and the endpoint, not the rendered page, is the real contract boundary. Browser E2E (`qa` / `playwright-e2e`) stays a **thin top layer** for genuine cross-stack journeys and post-deploy smoke on staging — never the inner-loop driver. Rationale recorded in `docs/decisions/0001-tdd-outside-in-at-api-boundary.md`.

## Order for a backend feature

1. `api-architect` fixes the endpoint contract (method, path, body, response, codes, permissions).
2. `tester` writes a feature test via DRF `APIClient` that hits the endpoint and checks:
   - status code,
   - response shape (fields, types),
   - DB state after the request,
   - authorization (anonymous / other user → 401/403).
   The test FAILS (the endpoint does not exist yet).
3. `django-developer` adds the model/serializer/view/route — just enough to green the test. Any stub used to go green is marked + logged per @.claude/rules/no-stubs.md.
4. Refactor + `ruff`.

## What to test / what to skip

**Always test:**
- custom business logic, model methods, serializer validators;
- every endpoint: all response codes, access rights, pagination/filters;
- edge cases and errors (400/401/403/404/409);
- signals, celery tasks, complex queries.

**Can skip:**
- trivial CRUD fully covered by standard DRF with no customization;
- auto-generated migrations without data logic.

## Triangulation

Assert behavior from at least 2–3 distinct cases (different inputs → different outputs), not a single example, so a hardcoded/stub return cannot stay green. See @.claude/rules/no-stubs.md.

## Tools

- `pytest` + `pytest-django` (fixtures, `@pytest.mark.django_db`).
- `factory_boy` for factories instead of manual object creat