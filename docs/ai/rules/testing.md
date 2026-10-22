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

Single owner of the list: docs/ai/rules/tdd.md ("What to test / what to skip") — follow it, do not re-copy it here.

## Order (TDD)

First a failing test (RED), then code (GREEN), then refactor. Details — docs/ai/rules/tdd.md.

## Full suite vs targeted runs (D12)

- **Agents never run the full suite.** They run only targeted subsets: the tests
  of the changed module or app, `-k <name>`, `--lf` (last failed).
- **The full suite runs at most twice a day and the user starts it.** When a full
  run is due (before a PR leaves draft, after a wide refactor), the agent stops and
  gives the exact command — `make ci` (or the raw command below) — and records the
  result the user reports, with its time, in the session record. A full run the
  agent did not see is `NOT_VERIFIED`, never assumed green.
- Parallelism: `pytest-xdist` (`-n auto --dist loadfile`) is on by default in
  `make test`/`make ci`. It pays off only with the clone in WSL ext4 (ADR `0027`);
  on a Windows-drive bind mount the workers serialize on I/O. For one quick test
  drop it: `make test PYTEST_XDIST= ARGS="-k name"`.

## Commands

```bash
# targeted (agents)
make test ARGS="apps/orders/tests -x"        # docker compose exec backend pytest -n auto --dist loadfile apps/orders/tests -x
make test PYTEST_XDIST= ARGS="--lf"          # last failed, single process
# full suite (the user, at most twice a day)
make ci                                      # docker compose exec backend pytest -n auto --dist loadfile --cov=apps --cov-report=term-missing
docker compose exec backend ruff check .
```
<!-- Last reviewed/updated: 2026-10-22 (D12 full-suite discipline, xdist — ADR 0027) -->
