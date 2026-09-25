# Generated role pack: tester

Do not edit; generated from full canonical sources.

<!-- SOURCE docs/ai/roles/tester.md SHA256 9ab96be9825e709b82dd381475dd0d799ad1a8381ecac576fbb3cd4c56e66965 -->
# Test Engineer (pytest)

You write robust tests in Python. You work first in the TDD cycle: a **failing** test first.

## TDD Workflow

1. **RED**: a test describing the expected behavior. Run it — it must fail for the expected reason.
2. Hand off to `django-developer` for **GREEN**.
3. After GREEN — verify green and add tests for edge/error cases.

> Rule: no production code without a failing test first.

## Standards (see docs/ai/rules/testing.md)

- `pytest` + `pytest-django`, `@pytest.mark.django_db`, `factory_boy`.
- DRF `APIClient`; check status codes, response shape, DB state, authorization.
- AAA structure; descriptive names `test_<subject>_<condition>_<expectation>`.
- Per endpoint: success, 400 (validation), 401 (anonymous), 403 (other user), 404 (not found), **409 (conflict)** — explicitly, on both create and update where a unique field exists. Always assert DB state after the request, not only the status code.

### File-upload / parsing endpoints — required extra cases

When the endpoint ingests an uploaded file or parses a declared format (import, bulk-load), the happy path is not enough. Add:

- **Both directions of format/content mismatch** — e.g. `format=csv` with JSON bytes AND `format=json` with CSV bytes. Each must 400, not silently create junk rows.
- **Encoding** — a non-UTF-8 file (e.g. cp1250/latin-2) returns a clean 400, never a 500.
- **Missing / empty required fields** in a row (e.g. empty `name` / `source_id`) — rejected, asserted via DB row count unchanged.
- **Conflict / concurrency** — a duplicate of a unique key returns 409 (or the documented upsert behavior), with a test that distinguishes "created" from "updated" (triangulation, so a stub cannot pass).
- **Partial-batch failure** — a file with some good and some bad rows produces a machine-readable summary (counts), and the bad rows do NOT land in the DB.

## Contract conformance (mandatory)

The external API contract is the canonical schema at `docs/api/openapi.yml` (pulled by `scripts/pull_contract.sh`, pinned via `CONTRACT_VERSION`; ADR 0017). It is the source of truth for every request/response shape and status code you test.

- **Read it first.** Take request bodies, response fields/types, and declared status codes from `docs/api/openapi.yml` plus the `api-architect` route notes — never invent a shape the contract does not define.
- **Write conformance tests.** For each endpoint add at least one `@pytest.mark.conformance` test that validates the live DRF response against the contract via `django-contract-tester` (`SchemaTester` / `OpenAPIClient`). These are the Level-2 checks run by `scripts/check_contract_conformance.sh`; at MVP/production the gate is **fail-closed** — missing conformance tests fail the build (docs/ai/rules/project-maturity.md).
- **Do not fudge to pass.** If the implementation cannot match the contract, that is a contract task in `claude-api-contract` — flag it as a deviation (docs/ai/rules/deviation-register.md), never weaken the assertion.

See docs/ai/rules/api-docs.md and docs/ai/rules/verification.md.

## Do NOT test

Trivial CRUD with no customization, auto-migrations without logic, simple `__str__`.

## Commands

```bash
docker compose exec backend pytest -k <pattern>
docker compose exec backend pytest --cov=apps --cov-report=term-missing
```

> Browser E2E and manual UI checks are done by the `qa` agent (against staging / the separate frontend repo) or the user. When a story's acceptance criteria include browser-visible behavior, ask the orchestrator to dispatch `qa` after the Quality Gate. Skills: `pytest-tdd` (the RED-GREEN-REFACTOR mechanics) and `test-master` (test strategy above TDD — what to test, the test pyramid, coverage targets).

> **Living plan.** After finishing your phase, append a one-line confirmation to the active `docs/plans/NNNN-*.md` **Execution log** (via an append-only file update, never a full-file rewrite) — e.g. "phase done: <fact>". See docs/ai/rules/living-plan.md.

<!-- Last reviewed/updated: 2026-07-07 (qa handoff trigger added) -->

<!-- END SOURCE docs/ai/roles/tester.md -->

<!-- SOURCE docs/ai/rules/api-docs.md SHA256 d16c9a392fa795c44dae404bbd5261cf1f5bed1dd9a62be1afdb959e5000911e -->

# REST API contract (external, consumed — enforced)

The REST API contract is the primary user-facing artifact this repo serves, but it is **NOT authored here**. The canonical contract is the OpenAPI 3.1 schema authored in the separate **`claude-api-contract`** repository (the single source of truth). This backend **consumes** that contract, pins it by version, and **validates its implementation against it** — it never generates the contract. So "API documentation" here means: pull the external contract, keep the implementation conformant, and serve a developer-facing UI. Conformance is checked by CI as a hard gate.

> Rationale: ADR `0017` (contract as the external single source of truth). The two conformance levels live in `docs/ai/rules/verification.md`.

## What "the contract" means here

1. **Canonical OpenAPI schema — external.** Authored in `claude-api-contract` (TypeSpec → OpenAPI 3.1, bundled), released as a git tag `vX.Y.Z`. This backend pins it via `CONTRACT_VERSION` and fetches `openapi.yml@CONTRACT_VERSION` with `scripts/pull_contract.sh` (git tag + raw URL). An optional `CONTRACT_URL` lets the build fetch the contract from an online URL instead; it is **fetch-only** — the drift `--check` always validates against the pinned tag (ADR `0025`). Raising the pin is a deliberate PR, never an automatic drift. The committed `docs/api/openapi.yml` is a **vendored copy of the external canon**, not a generated output.
2. **Interactive UI — local, generated.** `Swagger UI` at `/api/schema/swagger/` and `Redoc` at `/api/schema/redoc/`, served by Django in dev and on staging via `drf-spectacular`. drf-spectacular is used **only** to render a developer-facing client from the live code — it is **not** the canonical schema.
3. **Per-endpoint human notes (when needed)** — narrative markdown in `docs/api/<resource>.md` for non-obvious things the schema can't carry (rate-limit reasoning, deprecation path, business invariants, idempotency keys).
4. **Error envelope** — all 4xx/5xx responses share the contract's envelope: `{"detail": "<human>"}` for simple errors and `{"errors": [{"field", "code", "message"}]}` for validation errors, produced by `apps.common.exceptions.exception_handler`. The envelope is part of the consumed contract; see `docs/ai/rules/serializers-permissions.md` (ADR `0020`) for the code/status map.

## The gate — `scripts/check_contract_conformance.sh`

Instead of "code → schema, diff = red" (the old drift gate), CI validates the **running implementation against the external contract** and fails the PR on any divergence; a separate **vendored-copy-vs-pinned-tag** drift gate (`pull_contract.sh --check`, ADR 0021) still guards provenance. Two levels (details in `docs/ai/rules/verification.md`):

- **schemathesis** — property-based; drives generated requests against the running backend and catches 500s / schema violations / response-conformance failures. Pin the version (3.1 is first-class in current releases).
- **django-contract-tester** (`SchemaTester` / `OpenAPIClient`) — point validation of DRF responses against the external `docs/api/openapi.yml` in pytest.

Run locally before pushing:

```bash
bash scripts/pull_contract.sh                 # fetch openapi.yml@CONTRACT_VERSION
bash scripts/check_contract_conformance.sh    # schemathesis + django-contract-tester
```

> The backend **never** regenerates the canonical schema. `drf-spectacular`'s `spectacular` command is only for sanity-checking the Swagger UI rendering, never for producing the contract.

## Lifecycle (per feature)

1. The contract for the endpoint already exists in `claude-api-contract` (designed there first). `api-architect` reads the pinned contract and records the slice's routes in `docs/project-state/endpoints.json`.
2. `tester` writes the failing API feature test (DRF `APIClient`) against the contract.
3. `django-developer` implements until GREEN and conformant — `drf-spectacular` annotations (`@extend_schema`, `@extend_schema_field`) are added only where the Swagger UI needs help matching the contract.
4. **Before opening the PR** (or in `/wrap-up`): run `scripts/check_contract_conformance.sh` (schemathesis + django-contract-tester) against the pinned contract; both must pass.
5. `docs-writer` adds the per-endpoint narrative markdown if needed and includes the endpoint in `docs/api/INDEX.md`, which points at the external contract + `CONTRACT_VERSION`.

## Required `drf-spectacular` setup (Swagger UI only)

- In `INSTALLED_APPS`: `drf_spectacular`.
- In `REST_FRAMEWORK`: `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'`.
- `SPECTACULAR_SETTINGS` with `TITLE`, `DESCRIPTION`, `VERSION` set per project.
- URLs include `SpectacularSwaggerView`, `SpectacularRedocView` (UI). `SpectacularAPIView` may serve a live schema to the UI, but the **committed `docs/api/openapi.yml` is the vendored external contract**, not its output.
- `pyproject.toml` pins `drf-spectacular>=0.27` (UI), plus `schemathesis` (pinned, 3.1) and `django-contract-tester` (conformance).

## Binds these agents (loaded per-agent via `@`-reference)

- `api-architect` — reads the pinned external contract and records the feature's routes in `docs/project-state/endpoints.json`. Does NOT author the contract here; a needed contract change is raised in `claude-api-contract`.
- `django-developer` — implements against the external contract; adds `@extend_schema` only for Swagger-UI parity; runs the conformance gate before declaring GREEN.
- `docs-writer` — owns `docs/api/INDEX.md` (points at the external contract + version) and any per-endpoint narrative; verifies the conformance gate passes before declaring the PR ready.
- `reviewer` — at the Quality Gate, blocks PRs whose implementation diverges from the pinned contract, or that raise `CONTRACT_VERSION` without an ADR / migration note.

> Goal: the contract is owned externally and consumed here; the implementation is continuously validated against it, so the backend can never silently drift from the published API.

<!-- END SOURCE docs/ai/rules/api-docs.md -->


<!-- SOURCE docs/ai/rules/app-readme.md SHA256 9cef659cf2c333bed0b109272479b461bfa30a73bb1e2324452f671aa39d75c2 -->

# Per-app README (mandatory, enforced)

Every Django app under `backend/apps/<app>/` MUST have a local `README.md` describing the app's purpose, public surface, and where it fits in the project. The intent: no app can ship without a one-page primer that a new contributor (or future-you) reads to orient before touching code. Checked in CI by `scripts/check_app_readmes.sh` — a missing README fails the PR.

## Required sections (in order)

1. **Purpose** — one paragraph: what the app owns in the domain, what it does NOT own (boundaries with other apps).
2. **Models** — short table or list of the main models with one-line descriptions and any domain invariants ("invoice total is the sum of line items, enforced by ``Invoice.full_clean()``").
3. **Endpoints** — list of REST endpoints exposed by this app (`method`, `path`, `purpose`, `auth/permissions`). Detail belongs in the OpenAPI schema (`docs/api/openapi.yml`); the README gives the index.
4. **Signals / Celery tasks** — any background work originating from this app, with idempotency notes.
5. **Cross-app dependencies** — which other apps this one reads from or writes to, and why.
6. **Decisions** — links to ADRs in `docs/decisions/` that affect this app.

Optional but recommended: a short "How to extend" pointer (e.g. "to add a new export format, register a subclass of ``BaseExporter`` in ``exporters/registry.py``").

## Lifecycle

- A new app is **born with a README** — newly scaffolded apps copy `templates/APP_README.md` into the new app folder (`/bootstrap` Mode A creates the initial skeleton from this template). When creating an app by hand (`python manage.py startapp <name>`), copy the template immediately.
- The README is updated **in the same PR** as model/endpoint changes that affect it (the *Endpoints* and *Models* sections are the most volatile). `reviewer` flags PRs that change `apps/<app>/views.py` or `apps/<app>/models.py` without touching `apps/<app>/README.md`.
- **After GREEN, before the PR opens:** drop any RED-phase / "target surface" framing the README was scaffolded with, and reconcile the *Endpoints* section against the live code. The endpoint list MUST agree across three sources — `apps/<app>/README.md`, `docs/api/INDEX.md`, and the vendored external `docs/api/openapi.yml` (pulled from `claude-api-contract`). The external contract is the source of truth; if the README or INDEX disagree, they are wrong. `docs-writer` runs this three-way reconciliation as part of the docs phase.
- When deprecating an app, the README's *Purpose* becomes the deprecation note and links to the replacement.

## Enforcement (the gate)

- **`scripts/check_app_readmes.sh`** — run in `backend-ci.yml` and locally before pushing. For each directory under `backend/apps/` (excluding `__pycache__` and hidden dirs), asserts a `README.md` exists and is non-empty. Exits non-zero with the missing app names.
- **Reviewer / docs-writer at Quality Gate** — flag any PR that touches an app's surface without updating its README. `docs-writer` is responsible for keeping the *Endpoints* section in sync with the OpenAPI schema regenerated by the api-docs gate.

## Binds these agents (loaded per-agent via `@`-reference)

- `django-developer` — when creating a new app, copies `templates/APP_README.md` and fills *Purpose* + initial *Models* before opening the PR.
- `api-architect` — updates the app's *Endpoints* section whenever the contract changes.
- `docs-writer` — owns the per-app README as part of the docs pipeline; runs the gate locally before declaring the PR ready.
- `reviewer` — at Quality Gate, blocks PRs that change the app's public surface (models/views/permissions) without a corresponding README update.

> Goal: each app is self-explanatory at the README level; the OpenAPI schema is the contract, the README is the map.

<!-- Last reviewed/updated: 2026-05-27 -->

<!-- END SOURCE docs/ai/rules/app-readme.md -->


<!-- SOURCE docs/ai/rules/architecture.md SHA256 45fc36cbffce5a5d7fef60d2574774c420c3dab7e522a8ab6e3c8ae93ea56c7e -->

# Project architecture

## API-first (contract-first, backend consumes)

The canonical REST API contract is authored externally in `claude-api-contract` and pinned here via `CONTRACT_VERSION` (ADR `0017`). Order of work on a feature:

1. The contract for the endpoint already exists in `claude-api-contract` (designed there first); pull it with `scripts/pull_contract.sh`.
2. The backend implements the endpoint test-first against that contract: read contract → tests (RED) → models / migrations / serializers / views / routes / permissions (GREEN) → endpoint docs.
3. The implementation is validated against the pinned `docs/api/openapi.yml` by `scripts/check_contract_conformance.sh` (schemathesis + django-contract-tester) in the same PR. The backend **never regenerates** the canonical schema.

Interactive API testing is via **Swagger UI / Redoc**, served by Django at `/api/schema/swagger/` and `/api/schema/redoc/` via `drf-spectacular` (UI only, not the canon) — no hand-rolled mini-frontend in this repo. The production frontend lives in a **separate repository** (`claude-react-mui`) that consumes the same external contract. Details: `docs/ai/rules/api-docs.md`.

## Project structure (backend-only)

```
backend/
├── config/                 # Django project
│   ├── settings/
│   │   ├── base.py         # shared settings
│   │   ├── dev.py          # local (WSL2 + Docker)
│   │   └── staging.py      # VPS
│   ├── urls.py             # root router: /api/v1/ ...
│   ├── asgi.py / wsgi.py
├── apps/                   # domain Django apps
│   └── <domain>/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py        # ViewSets / APIViews
│       ├── urls.py         # this domain's router
│       ├── permissions.py
│       └── tests/          # domain tests (TDD)
├── manage.py
└── pyproject.toml
```

## Layers and boundaries

| Layer | Purpose | Rule |
|-----|-------------|---------|
| Models | data + domain invariants | business logic close to the model (fat models, thin views) |
| Serializers | validation + (de)serialization | input validation here, not in views |
| Views (ViewSet/APIView) | HTTP orchestration | thin; no heavy logic |
| Permissions | authorization | separate classes, tested separately |
| Services (when needed) | complex cross-model logic | `apps/<domain>/services.py` |
| Signals/tasks | async work | separate, with tests |
| Cross-cutting infra | error envelope, shared base classes | `apps/common/` — no domain models; wired via project `REST_FRAMEWORK` (see `docs/ai/rules/serializers-permissions.md`) |

## API versioning

- All endpoints under the `/api/v1/` prefix.
- **Paths match the external contract exactly — no trailing slash.** The contract publishes `/api/v1/articles`; DRF routers are therefore declared with `DefaultRouter(trailing_slash=False)` — schemathesis drives requests straight from the contract, and a slash mismatch turns every hit into 301/404 (ADR `0025`). (The local system probe `GET /api/v1/health/` is not part of the contract and keeps its slash.)
- Contract-breaking changes — a new version, not a silent change.

## Principles

- **Simplicity first.** Do not introduce abstractions ahead of time.
- **Thin views, rich models.**
- **Every endpoint — with a test and an entry in `docs/api/`.**

## Design questions (ask before adding structure)

- Does this logic belong on the model, in a serializer, or a service? (Prefer model, then service; never the view.)
- Is a new Django app warranted, or does it fit an existing domain?
- Is an abstraction earning its keep, or is it premature? (Simplicity First.)
- Where must integrity live — DB constraint vs application check? (Prefer DB for hard invariants.)
- Does the API contract stay backward-compatible, or is this a new `/api/vN/`?
<!-- Last reviewed/updated: 2026-07-07 (Design questions ported from architecture-designer skill — audit batch B) -->

<!-- END SOURCE docs/ai/rules/architecture.md -->


<!-- SOURCE docs/ai/rules/code-style.md SHA256 4b56a9dfb90a0a22279a4616796a1bd046c433140f2822a3f6b8769a64dd1c1e -->

# Code style

## Python / Django

- Python 3.13, typing where appropriate. Linter and formatter — **ruff** (`ruff check .`, `ruff format .`).
- Imports ordered (ruff isort). No unused imports.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Django: `verbose_name`, `related_name` explicit; `Meta.ordering` where needed; `__str__` on models.
- DRF: serializers validate input; views are thin; permissions are separate classes.
- No "magic numbers" — move them to constants/enums (`models.TextChoices`).
- Secrets configuration — only via env (`django-environ` / `os.environ`), never in code.
- **Every public function/method/class has a docstring** — see *Docstrings* below.
- **Every Django app has a `README.md`** at `backend/apps/<app>/README.md` — see `docs/ai/rules/app-readme.md`.

## Docstrings (mandatory, Google style)

Every public module, class, function, and method in `backend/apps/` MUST carry a docstring in **Google style**. Private members (`_underscored`) are exempt. Tests, migrations, and `__init__.py` are exempt by ruff `per-file-ignores`. Enforced by ruff `D` rule set with `convention = "google"` — a missing docstring fails lint and CI.

A docstring captures **why** the unit exists and the contract callers depend on (inputs, outputs, side effects, errors), not the *how* of the implementation.

```python
def split_invoice(invoice: Invoice, max_lines: int = 100) -> list[Invoice]:
    """Split an invoice into chunks of at most ``max_lines`` line items.

    Used by the export pipeline to keep generated PDFs under the printer's
    per-document limit. Splitting preserves invoice metadata (number, customer,
    totals) on every chunk; chunk numbering is appended as ``-N``.

    Args:
        invoice: A persisted ``Invoice`` with at least one line item.
        max_lines: Maximum line items per chunk. Must be > 0.

    Returns:
        List of new ``Invoice`` instances (not yet saved). Order matches the
        original line-item order; the first chunk inherits the original ``id``
        as its parent reference.

    Raises:
        ValueError: ``max_lines`` is <= 0 or the invoice has no line items.
        PermissionError: The caller is not the invoice owner.
    """
```

Rules of thumb:

- **Subject of the first line is the *function*, not the *action*** — "Split…", "Compute…", "Return…", "Raise…".
- The first line is a single sentence ending with `.` and fits ≤ 88 chars.
- **Args / Returns / Raises** sections present when there are non-trivial inputs/outputs/exceptions; omit empty sections.
- Cross-reference related units with backticks: ``See ``ranking.services.rank``.``
- For Django models: docstring on the class describes the domain entity, not column types (those are in `verbose_name` / `help_text`).
- For DRF views and serializers: docstring states the contract (resource, allowed methods, who can call) — the schema is in OpenAPI (`docs/ai/rules/api-docs.md`), not the docstring.

## File size limit (max 800 lines, enforced)

No source file may exceed **800 lines**. A file that grows past the limit is a signal it carries more than one responsibility — split it into smaller, cohesively-named modules and **group them in a package (folder)** instead of letting one file sprawl.

- The limit counts **all lines** of the file (code, comments, and blank lines), measured as `wc -l`.
- **Only auto-generated migrations are exempt** (`backend/apps/**/migrations/`). Everything else under `backend/` — models, serializers, views, services, permissions, tests, settings — is in scope. Tests are NOT exempt: a 800+ line test file splits by scenario/resource just like production code.
- Enforced by the CI gate **`scripts/check_file_size.sh`** (run in `backend-ci.yml` and locally before pushing) — any non-migration `*.py` over 800 lines fails the PR. `reviewer` also flags files approaching the limit at the Quality Gate.

### How to split (group into folders)

When a module gets large, convert it into a package and split by cohesion — never by arbitrary line cuts:

```
apps/billing/views.py            ->  apps/billing/views/
                                       __init__.py        # re-export the public names
                                       invoices.py
                                       payments.py
                                       refunds.py
```

- Turn `models.py` -> `models/` (one module per aggregate), `serializers.py` -> `serializers/`, `services.py` -> `services/`, `tests.py` / `tests/test_x.py` -> more focused `tests/test_<topic>.py`.
- Keep the **public import path stable** via `__init__.py` re-exports (`from .invoices import InvoiceViewSet`) so callers and routers do not change.
- Split along domain seams (one resource / one concern per file), not by counting lines. Each resulting file keeps a single responsibility.
- `code-structure-auditor` performs this audit on demand (`/structure-audit`) and proposes the concrete split; `django-refactoring-expert` executes large splits under green tests.

## General

- Comments inside the body explain *why*, not *what* (let names and the docstring carry *what*).
- Small functions with a single responsibility.
- Conventional commits (see docs/ai/rules/git-operations.md).

<!-- Last reviewed/updated: 2026-06-02 (added File size limit: max 800 lines, check_file_size.sh gate) -->

## Template tooling documentation

Every new or changed Python function, including private helpers and tests, documents purpose, arguments, result, side effects, errors, DB interaction and relevant business rules. Shared tooling requires Python 3.13+ stdlib.

<!-- END SOURCE docs/ai/rules/code-style.md -->


<!-- SOURCE docs/ai/rules/deviation-register.md SHA256 0940d8cd41dd5680a4c967884226eda6ee0b10ecabb29e0d0b22d2e5d9abcfbf -->

# Deviation register (deviations & contract findings are documented, never silent)

When an agent departs from the agreed plan — finds a contract error, a better
technical alternative, a blocker that forces a different route, or must raise the
contract pin (`CONTRACT_VERSION`) — that is a **deliberate, documented act**, never
a silent course change. The record lives in `docs/reviews/`.

## When a deviation doc is REQUIRED

Create `docs/reviews/YYYY-MM-DD-<slug>.md` when any of these happen in a PR:

- an agent deviates from the approved living plan (a plan **Amendment** is added);
- an agent finds a defect or ambiguity in the consumed contract (`docs/api/openapi.yml`);
- an agent chooses a materially different technical approach than the plan stated;
- `CONTRACT_VERSION` is raised (the consumed contract pin changes).

A trivial in-scope clarification that does not change the plan does NOT need one —
the bar is "the course changed, or the contract is wrong."

## Required fields

```
# Deviation — <short title>   (YYYY-MM-DD)
- Original plan / expectation: what we said we'd do.
- What changed / problem: the deviation, defect, or better alternative.
- Evidence: test output, contract excerpt, link to the failing case.
- Decision: what we did instead, and why.
- Impact: contract / code / tests / docs / consumers affected.
- Status: proposed | accepted | superseded.
```

## Relationship to the living plan

The living plan's **Amendments** section records *that* a decision changed
(docs/ai/rules/living-plan.md); the deviation doc records *why* in reviewable
detail and survives beyond the single task. An Amendment that changes the contract
or the agreed approach MUST point to its `docs/reviews/` entry.

## Enforcement

- `backend-policy.yml` blocks a PR that raises `CONTRACT_VERSION` without a
  `docs/reviews/` note or an ADR (`docs/decisions/`).
- `reviewer` flags, at the Quality Gate, any plan Amendment or contract finding
  that lacks a `docs/reviews/` entry.
- `docs/reviews/` is append-only history — never edit a past deviation; supersede
  it with a new dated entry.

> Goal: an agent can change course or report a contract defect — but it must leave
> a trace in `docs/reviews/`, so "agents follow the plan, and every deviation is
> documented" is mechanically visible, not honor-system.

<!-- END SOURCE docs/ai/rules/deviation-register.md -->


<!-- SOURCE docs/ai/rules/docker-commands.md SHA256 1a46c42a03ac87dd4e40dd4251e426b8f8f3bda59cf393b1466742753880aefb -->

# Docker / environment commands

> **Shell:** bash on Linux / macOS / WSL2 Ubuntu, or PowerShell / Git Bash on native Windows. The per-session hooks are cross-platform Python (ADR `0022`, which amends ADR `0005`), so no shell is privileged. The `.sh` gate scripts below run on the Linux CI runner; locally on native Windows they need Git Bash (for `make gates`). Working from a Windows drive (`/mnt/c`/`/mnt/d`) is fully supported (ADR `0009`); bind-mounts are just slower there, and git is best run from the host shell (avoids `/mnt` `index.lock`). `~/projects/<project>` is optional for faster bind-mounts, not required.
>
> The `SessionStart` hook writes `.ai-runtime/env-detect.json` with the active shell so agents can verify their assumptions.

## Make wrappers (optional shortcuts)

A root `Makefile` wraps the most common commands below so they are identical on native Debian and WSL2. It is a convenience layer only — the canonical commands are still those in this file, and `make` is never required by the pipeline.

```bash
make help          # list targets
make up            # docker compose up -d
make test ARGS="-k auth"   # docker compose exec backend pytest -k auth
make lint          # ruff check
make gates         # run the CI gate scripts locally before pushing
make doctor-deps   # quick host tool presence check (not the /doctor command)
```

## Environment

```bash
docker compose up -d            # bring up postgres + backend
docker compose ps               # status
docker compose logs -f backend  # logs
docker compose down             # stop
```

## SessionStart conveniences

The `SessionStart` hook runs `scripts/session-start.py`, which (in order): writes `.ai-runtime/environment.json` via the shared `scripts/ai/detector.py --write`, then `.ai-runtime/env-detect.json` via `scripts/detect-env.py` (mandatory — the stack gates depend on it); seeds `.env` from `.env.example` if `.env` is missing (placeholders only — fill real secrets yourself); and brings services up **only** when you opt in:

```bash
export CLAUDE_DJANGO_AUTO_UP=1   # before launching `claude`: auto `docker compose up -d` on session start
```

Off by default (heavy/stateful) per the project's detect -> propose -> fix-on-confirm philosophy. The hook never aborts the session and never prints secrets.

## Backend (Django in the container)

```bash
docker compose exec backend pytest                       # tests (TDD)
docker compose exec backend ruff check .                 # lint
docker compose exec backend ruff format .                # formatting
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
```

## Staging (VPS <STAGING_HOST>, Debian)

Staging runs **gunicorn in a container** (`docker-compose.staging.yml`, WSGI) behind a host reverse proxy (nginx/Traefik) — never `runserver`.

```bash
ssh <user>@<STAGING_HOST>
cd ~/projects/<project>
git pull

# 1) Pre-deploy gate: catch insecure/misconfigured settings before serving.
docker compose -f docker-compose.staging.yml run --rm backend \
  python manage.py check --deploy

# 2) Build + start (gunicorn behind the reverse proxy).
docker compose -f docker-compose.staging.yml up -d --build

# 3) Apply migrations.
docker compose -f docker-compose.staging.yml exec -T backend python manage.py migrate

# 4) Post-deploy smoke (replace ${STAGING_HOST} with the real subdomain).
curl -fsS https://${STAGING_HOST}/api/v1/health/        # expect {"status":"ok"}
curl -fsS -o /dev/null -w '%{http_code}\n' \
  https://${STAGING_HOST}/api/schema/                   # expect 200
```

> The VPS already runs many projects — `docker-compose.staging.yml` uses a dedicated network and a non-default Postgres host port (`STAGING_DB_PORT`, default `5433`), and `expose`s the backend to the compose network only (no host `publish`). The reverse proxy (nginx/Traefik) terminates TLS on the project's own subdomain (`${STAGING_HOST}`) and forwards `X-Forwarded-*`. Mobile testing — open the subdomain in the phone's browser.
>
> Host-native (non-Docker) deploys can instead run gunicorn under systemd behind nginx — described as an alternative in `docs/guides/admin.md`, deliberately NOT shipped as a template (avoids binding the scaffold to a specific reverse proxy / process manager).
<!-- Last reviewed/updated: 2026-06-03 -->

<!-- END SOURCE docs/ai/rules/docker-commands.md -->


<!-- SOURCE docs/ai/rules/environment.md SHA256 856c0b91cdd24603d526bef0ec8793249d6deef45805e19deb0ae0fcc7f3f9ab -->

# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` reads `.ai-runtime/env-detect.json` (written by the `SessionStart` hook) to pick shell-appropriate checks, never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

The Check column gives bash (Linux / macOS / WSL2 Ubuntu) commands; on native Windows use the PowerShell or Git Bash equivalents. Native Windows is supported — the per-session hooks are cross-platform Python (ADR `0022`, which amends ADR `0005`). The shell is auto-detected by `scripts/detect-env.py` on every session start and stored in `.ai-runtime/env-detect.json`.

| Requirement | Expected | Check (bash) |
|---|---|---|
| **Python (HARD REQUIREMENT)** | 3.13+ on PATH as `python` | `python --version`. On Ubuntu, if only `python3` is installed: `sudo apt install -y python-is-python3`. Without Python the SessionStart hook (`scripts/detect-env.py`) cannot run. |
| OS shell | Native Windows (PowerShell / Git Bash) OR WSL2 (Ubuntu); Linux / macOS bash or zsh. Per-session hooks are cross-platform Python (ADR `0022`). | `python --version` must work; `env-detect.json` shows `platform_supported: true` (it is `false` only on a platform that is neither Windows, Linux, macOS, nor WSL2). |
| Working dir | Any path, **including `/mnt/c`/`/mnt/d` (Windows drive) — fully supported (ADR `0009`); `/doctor` must NOT suggest moving**. Informational `/mnt` caveats only: slower Docker bind-mounts, CRLF, `git index.lock` (run git from the host shell). `~/projects/<slug>` is optional (max bind-mount speed), never required. | `pwd` |
| Docker Desktop | running, with WSL2 integration enabled if WSL2 is used | `docker info` |
| docker compose | v2 available | `docker compose version` |
| Python in container | 3.13.x (separate from the host Python above) | `docker compose exec -T backend python --version` |
| **Node.js (HARD REQUIREMENT)** | 18+ on PATH | `node --version`. Needed only to install the Claude Code CLI via npm (`npm install -g @anthropic-ai/claude-code`); the native Windows installer needs no Node. `detect-env.py` records the derived `node_supported` flag; `/doctor` reports `NO_NODE` if node is absent or < 18. Install via `nvm` if missing. |
| git | present | `git --version` |
| GitHub CLI | present in the shell where `claude` runs. Native Windows: `gh.exe` via `winget install GitHub.cli` is the correct install (ADR `0022`). WSL2: Linux `gh` via `apt` (a Windows `gh.exe` is NOT visible inside WSL2) | `gh --version` |
| **Claude Code CLI** | `claude` on PATH (native Windows installer, or `npm install -g @anthropic-ai/claude-code`) | `claude --version` works. On native Windows, PowerShell / Git Bash are fine. On WSL2, install the Linux-native CLI inside Ubuntu so `which claude` is a `/home/...` or `/usr/...` path (not `/mnt/c/...`). |

### Windows: native or WSL2 (both supported)

Native Windows is a first-class runner (ADR `0022`). Launch `claude` from
PowerShell or Git Bash in the project directory; the `SessionStart` hook runs
`python scripts/session-start.py` (cross-platform — no bash), writes
`.ai-runtime/env-detect.json` with `platform_supported: true`,
`platform: windows`, and `shell: powershell` (or `git-bash`), and `/doctor`
passes the platform gate.

Requirements on native Windows:

- `python` must resolve on PATH (`python --version` in PowerShell) — NOT the
  Microsoft Store alias. The hooks invoke `python …` directly.
- `git`, `gh`, Node 18+ (only if installing the CLI via npm — the native
  installer needs no Node), and Docker Desktop, as on any platform. Docker
  Desktop needs a backend: WSL2 or Hyper-V — so WSL2 may still be installed
  purely as Docker's backend, without ever being used as a shell.
- The `.sh` CI gate scripts (`make gates`) run under Git Bash locally and on the
  Linux CI runner; they are not on the per-session hot path.

WSL2 (Ubuntu) remains fully supported and is the right choice if you prefer a
POSIX shell or faster Docker bind-mounts: install the toolchain inside Ubuntu
(`sudo apt install -y git curl gh python-is-python3 python3-pip`) and the CLI
(`npm install -g @anthropic-ai/claude-code`), then launch `claude` from there.
The earlier "wrong runner" trap (the Windows `claude.exe` shadowing a WSL2 CLI)
no longer applies — both runners are supported (the `wrong_runner_suspected` field was removed
in env-detect schema v6).

## Scope 2 — Claude config & access

| Requirement | Expected | Check |
|---|---|---|
| Plugins (committed baseline) | `superpowers@claude-plugins-official`, `playwright@claude-plugins-official`, `github@claude-plugins-official`, `context7@claude-plugins-official` installed (auto-enabled via `.claude/settings.json` `enabledPlugins`). Personal/global (recommended, NOT committed): `claude-hud@claude-hud` (HUD UI) and `engineering@knowledge-work-plugins` (generic work skills; 6/10 overlap the project-tuned agents and it bundles a second `github` MCP connector — ADR `0024`). `code-review` / `code-simplifier` / `feature-dev` / `pr-review-toolkit` / `commit-commands` are intentionally NOT in the baseline — covered by (or conflicting with) the project-tuned pipeline (ADR `0011`/`0024`). | `/plugin` list; compare with `.claude/settings.json` `enabledPlugins`. See ADR `0011`/`0024`. |
| MCP servers (github + context7) | provided by the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` (recommended, per ADR `0011`). The committed `.mcp.json` + `enabledMcpjsonServers` path is an optional fallback — do NOT enable both at once (double-registers the same MCP). | `/plugin` shows both installed; `.mcp.json` is NOT referenced in `enabledMcpjsonServers` when using plugins |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | set — provide via the project `.env` (parsed literally by `scripts/claude.sh` / `make cc`), **not** a shell-rc export. Still required even with the github plugin: the wrapper copies it into `GH_TOKEN` (which `gh` actually reads — `gh` ignores `GITHUB_PERSONAL_ACCESS_TOKEN`) and drops any stale `GITHUB_TOKEN`. See ADR `0023`. | `[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]` (never print the value) |
| `CONTEXT7_API_KEY` | set — provide via the project `.env` (parsed literally by `scripts/claude.sh` / `make cc`); the context7 plugin (or the `.mcp.json` fallback) needs it for doc lookups. See ADR `0023`. | `[ -n "$CONTEXT7_API_KEY" ]` (never print the value) |
| GitHub auth | `gh` authenticated (via env token OR stored creds — either is fine; if `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` is set, `gh auth login` will refuse to store separate creds and that is EXPECTED) | `gh auth status` |
| `gh` token — repo access | Per ADR `0008`: the repo is created **by hand**, access is a **fine-grained per-repo token**. Fine-grained tokens carry no OAuth scopes, so `scopes` is empty — that is EXPECTED, not a failure. Required repository permissions on the target repo: **Contents** RW, **Metadata** RO (auto), **Pull requests** RW, **Workflows** RW, **Administration** RW (branch protection). | Capability is verified by `gh repo view <owner>/<repo>`, not by scopes. `/bootstrap` and `/doctor` print a template URL: `https://github.com/settings/personal-access-tokens/new?...&contents=write&pull_requests=write&workflows=write&administration=write` (classic PATs still gate on `repo`+`workflow`) |
| `gh` PAT kind | **Fine-grained** (`github_pat_...`) is RECOMMENDED (ADR `0008`) and is NOT a blocker — `FINE_GRAINED_PAT_NOT_SUPPORTED` is retired. A `classic` PAT (`ghp_...`) also works but grants whole-account access (discouraged). | `python -c "import json,pathlib; print(json.loads(pathlib.Path('.ai-runtime/env-detect.json').read_text())['gh']['pat_kind'])"` — either `fine-grained` (preferred) or `classic` is accepted |

### env-detect.json integrity (hard rule)

`.ai-runtime/env-detect.json` is the source of truth for `platform_supported`, `gh.pat_kind`, `gh.scopes`, and tool availability. It is rewritten by `scripts/detect-env.py` via the `SessionStart` hook (`scripts/session-start.py`) on every Claude Code CLI session, right after the shared detector wrote `.ai-runtime/environment.json`. A legacy `.claude/memory/env-detect.json` is moved to `.ai-runtime/` by the probe; two differing copies are reported, never merged. The mechanical gate `python scripts/policy/runtime_gate.py` no longer reads this file at all — it calls the shared detector in-process, so a fabricated report cannot satisfy it.

**Never hand-write or "patch" this file** to skip past a blocker. The file's fields drive `/bootstrap` and `/doctor` hard gates (`UNSUPPORTED_PLATFORM`, `NO_NODE`, `NO_GH_SCOPES`); fabricated values silently bypass safety checks. If the file is missing:

1. Run `python scripts/detect-env.py` manually and verify it writes the file honestly.
2. If the script fails, fix the underlying problem (install Python 3.13+ / fix PATH) — do NOT invent a JSON document with happy-path values.
3. Run the detector explicitly in the actual host environment when no hook exists; a sandbox probe describes only that sandbox, never unmeasured host capabilities.

This rule applies to humans AND to LLM agents executing `/bootstrap` / `/doctor`. An agent that fabricates `env-detect.json` to get past preflight has not satisfied preflight — it has just hidden a real failure.

## Scope 3 — Project state

| Requirement | Expected | Check |
|---|---|---|
| Skeleton | `backend/`, `docs/api/`, `docs/decisions/`, `docs/plans/`, `docs/project-state/` exist | `test -d <dir>` |
| `CONTRACT_VERSION` pin | set in `.env` to the consumed `claude-api-contract` tag (`vX.Y.Z`); raising it is a deliberate PR (ADR `0017`). `CONTRACT_URL` (optional) is a **fetch-only** override — the drift `--check` still validates against the pin (ADR `0025`) | `grep -q '^CONTRACT_VERSION=' .env` |
| External contract vendored | `docs/api/openapi.yml` present, fetched at the pinned version via `scripts/pull_contract.sh` (vendored copy of the external canon, never generated) | `test -f docs/api/openapi.yml` |
| CI drift-gate armed | GitHub Actions repository variable `CONTRACT_VERSION` set and equal to the `.env` pin — `backend-ci.yml` runs the drift gate only `if: vars.CONTRACT_VERSION != ''` (`/bootstrap` sets it; re-set on every pin raise, ADR `0025`) | `gh variable get CONTRACT_VERSION` — non-empty, equals the `.env` value |
| Config files | `CLAUDE.md`, `.claude/`, `docker-compose.yml`, `.env.example` present (committed) | `test -f <file>` |
| `.env.example` | committed canonical key list; new clones use it to seed `.env` | `test -f .env.example` |
| `.env` | local-only (gitignored), copied from `.env.example`; secrets filled | `test -f .env` (never print contents). Missing → `cp .env.example .env && $EDITOR .env` |
| Services | `postgres` + `backend` up and healthy | `docker compose ps` |
| Migrations | applied (no unapplied) | `docker compose exec -T backend python manage.py showmigrations --plan` — output should not contain `[ ]` |
| Tests | pytest green | `docker compose exec -T backend pytest -q` |
| Lint | ruff clean | `docker compose exec -T backend ruff check .` |

> Skeleton/`.env`/services may legitimately be absent in a brand-new repo before Step 3 of the README. `/doctor` reports these as "not set up yet" (info), not as failures, when no Django project exists yet.

## Scope 4 — Git hygiene

| Requirement | Expected | Check |
|---|---|---|
| Current branch | a feature branch, **not** `main` (for active work) | `git branch --show-current` |
| Branch protection | `main` protected on GitHub (PR + status checks). **Requires a public repo or GitHub Pro/Team** — on a **free plan + private repo** the protection API returns 403, so absent protection there is EXPECTED, not a failure (make the repo public or upgrade to enable it, or keep PR-only by discipline). | `gh api repos/{owner}/{repo}/branches/main/protection` — 404 = not protected (or unavailable on free + private) |
| Working tree | clean or only intended changes | `git status -sb` |
| Sync | up to date with `origin` | `git fetch --dry-run` then `git status -sb` |
| No secrets tracked | `.env` ignored, not committed | `git ls-files \| grep -E '(^\|/)\.env$'` (empty = good) |
| Secret scanning & push protection | enabled on the repo so GitHub blocks commits containing known secret patterns **before** they land. **Public repos: free. Private repos: needs GitHub Advanced Security.** On a free plan + private repo this is unavailable — fall back to discipline (`.gitignore` + the `.env` check above). `/doctor` reports absence here as info, not a failure. | `gh api repos/{owner}/{repo}/secret-scanning/alerts` — 403/404 = not enabled (or unavailable on the plan) |
| Dependabot | `.github/dependabot.yml` present (pip + github-actions, weekly) so dependency/security update PRs are raised automatically — through the normal branch → PR flow, never a direct push to `main` | `test -f .github/dependabot.yml` |

## Remediation policy

- **Safe to propose-then-apply (after confirmation):** `docker compose up -d`, `python manage.py migrate`, create missing skeleton dirs, `cp .env.example .env`, `/plugin install ...`, `nvm install`, create a feature branch off fresh `main`.
- **Ask explicitly, never silently:** anything that writes secrets, force operations, deleting files, enabling branch protection (account-level), pushing. For unsetting a leaked token: `unset GITHUB_TOKEN` for the current shell, plus removing the export line from `~/.bashrc` / `~/.profile` (or `~/.zshrc`).
- **Forbidden in `/doctor`:** committing, `git push`, pushing to `main`, printing secret values, editing application source code.

<!-- Last reviewed/updated: 2026-06-03 (Scope 4: added secret scanning/push protection + Dependabot rows) -->

<!-- END SOURCE docs/ai/rules/environment.md -->


<!-- SOURCE docs/ai/rules/git-operations.md SHA256 1c5ea9a41b22e457c687d92cfc18e005be427bdf3345ee79b3431edbecdd3c9b -->

# Git operations

## Iron rule

**NEVER commit or push directly to `main`.**
Only: branch → commits → `push` → Pull Request → review → merge.

### Documented exception (one-shot)

`/bootstrap` in **Mode A (fresh project)** performs the very first commit and `git push -u origin main` because there is no branch protection to bypass yet and there are no reviewers — this is the bootstrap commit that lays down the initial scaffold. After that commit, `/bootstrap` immediately enables branch protection on `main`, and from that moment the iron rule applies again.

All other `/bootstrap` work (Mode B resume) and every other command (`/synthesize-brief`, feature pipelines, `/fix-ci`, etc.) goes through a PR.

## Branches

- Naming: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>`, `test/<slug>`.
- One branch = one logical change.
- The base is always fresh: `git checkout main && git pull` before creating a branch.

## Commits (Conventional Commits)

```
feat: add user registration via email
fix: correctly handle duplicate email (409)
test: add feature tests for /api/v1/auth/register
refactor: extract password validation into the serializer
docs: update docs/api for auth
chore: bump ruff dependency
```

## Workflow

```bash
git checkout main && git pull
git checkout -b feat/<slug>
# ... TDD cycle, small commits ...
git push -u origin feat/<slug>
gh pr create --fill        # or with a description
# review → merge (Squash) on GitHub
git checkout main && git pull   # on BOTH machines before the next task
```

## PR description (template)

```
## What
Short description of the change.

## Why
Context / user story.

## How verified
- [ ] pytest green
- [ ] ruff clean
- [ ] CI passed

## Notes
Edge cases, risks, next steps.
```

## Context sync between machines

At the end of a session, update and commit the context files: `docs/HANDOFF.md` (the rolling "where we are / what's next" snapshot — read first on a new machine), `docs/WORKLOG.md` (the append-only "what we did" chronicle), and if needed `docs/todo.md` (cross-session backlog), `docs/lessons.md`, `docs/project-state/*` and ADRs `docs/decisions/NNNN-*.md`. This is how Claude's work history travels between computers via a plain `git pull`. Regenerate `HANDOFF.md` via `/wrap-up` (or `/handoff` alone).

## Prohibitions

- `git push origin main` — forbidden EXCEPT the documented `/bootstrap` Mode A exception above.
- `git push --force` to shared branches — forbidden.
- Committing secrets/`.env` — forbidden (see `.gitignore`).
<!-- Last reviewed/updated: 2026-05-27 -->

## Shared session policy

Commit/push/draft PR are part of an authorized task. Merge requires a new explicit user command. Preserve unrelated index/worktree changes, refs, stash and worktrees; never reset/clean/stash automatically or stage all files. A failed/unknown network result requires remote-state inspection before retrying. No release/deploy is implied.

<!-- END SOURCE docs/ai/rules/git-operations.md -->


<!-- SOURCE docs/ai/rules/living-plan.md SHA256 2de9e6f8a0fb14d4f17406a37440c5bac39603a83ed2e8e1e0e6a2dfec88f763 -->

# Living plan (agents keep `docs/plans/NNNN-*.md` current as work runs)

A plan is a **living artifact**, not a frozen Plan-Mode snapshot. The orchestrator seeds `docs/plans/NNNN-<slug>.md` at the start of a non-trivial task, and the work's actual course flows back into it — confirmations of what ran, and changes of direction — instead of the plan drifting from reality and duplicating WORKLOG. This stays within Simplicity First: no new tooling, just discipline + one template (`templates/plan.md`) + this rule.

## When a plan is seeded

- **Scope = every non-trivial task** — the same threshold that activates Plan Mode (`docs/ai/rules/workflow.md`): 3+ steps, an architectural decision, or touching >2 files. Trivial tasks (a typo, a single config value) do NOT seed a plan.
- **The orchestrator seeds it**, copying `templates/plan.md` → `docs/plans/NNNN-<slug>.md`. `NNNN` is the next free number in `docs/plans/`, assigned by the orchestrator at seed time — never by agents (avoids number races between parallel agents).

## The three managed sections

Each `docs/plans/NNNN-*.md` carries three managed sections on top of the ordinary plan body:

1. **Status table** (top) — step / state (`pending`/`in_progress`/`done`/`blocked`) / owner-agent. The plan's cursor; updated as steps move.
2. **Execution log** (append-only) — short confirmations of execution facts: "step N green (pytest)", "contract recorded in endpoints.json", "gate: 1×🟡 → back to django-developer". Appended, never edited retroactively.
3. **Amendments** (append-only) — changes of direction. If a plan decision changes, the original paragraph is **not deleted**; instead add an Amendments entry plus an inline pointer next to the original (`> ⚠️ Changed — see Amendment #k`). The decision history stays transparent. An Amendment that changes the contract or the agreed approach also gets a `docs/reviews/` deviation entry — see `docs/ai/rules/deviation-register.md` (loaded by `tester`/`reviewer`; the orchestrator reads it on demand).

## Who updates what

- **Orchestrator** — seeds the plan; owns the Status table; records gate outcomes into the Execution log (gate agents report to it, see below); appends Amendments when a body decision changes.
- **Executor agents** (`ba`, `api-architect`, `django-developer`, `tester`, `docs-writer`) — after finishing their phase, **append** a one-line confirmation to the active plan's Execution log (via an append-only file update, never a full-file rewrite).
- **Gate agents** (`reviewer`, `security-scanner`, `dba`) — do NOT edit the plan; they stay read-only over both code and plan. They **report the gate result to the orchestrator**, which records the Execution log entry. This preserves the "gate agents only read and report" invariant.

## Boundary with WORKLOG

**Execution log ≠ WORKLOG.** The Execution log is an in-plan journal of confirmations during one task. `docs/WORKLOG.md` is the cross-session chronicle, single owner `/wrap-up`. They do not duplicate: the plan records the course of one task, WORKLOG the session summary.

## Binds these agents (rule is auto-loaded)

- `ba`, `api-architect`, `django-developer`, `tester`, `docs-writer` — append an Execution log confirmation at the end of their phase (need `Edit` to append).
- `reviewer`, `security-scanner`, `dba` — never edit the plan; report the gate result to the orchestrator.

## Out of scope (v1)

- A CI gate "plan updated in the same PR" (like `check_app_readmes.sh`) — only after the discipline is hand-proven. Tracked in HANDOFF open questions.
- A machine-readable Status format (JSON) — markdown tables suffice for now (Simplicity First).

> Goal: at any point in a non-trivial task, the plan shows where we are (Status), what has actually run (Execution log), and why decisions changed (Amendments) — without drifting from reality or duplicating WORKLOG.

<!-- END SOURCE docs/ai/rules/living-plan.md -->


<!-- SOURCE docs/ai/rules/mcp-stack.md SHA256 9ed71f1488604dfc9b050ee730867d53ebed857b1891cb7414f0b061e82de41a -->

# MCP Stack — Tool Usage Guide

Configured in `.mcp.json`, enabled in `.claude/settings.json` (`enabledMcpjsonServers`). Set the env vars before use.

> **Recommended mechanism (ADR `0011`):** `github` and `context7` are provided by the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` (auto-enabled via `enabledPlugins`). The `.mcp.json` + `enabledMcpjsonServers` setup below is the **optional committed fallback** — do NOT enable both at once (the same MCP would be registered twice). Either way the **tool names are identical**, so everything below applies unchanged. Tokens are still required: `GITHUB_PERSONAL_ACCESS_TOKEN` (also used by the `gh` CLI) and `CONTEXT7_API_KEY`.

## GitHub MCP (`github`) — env `GITHUB_PERSONAL_ACCESS_TOKEN`

PR data and review automation. Prefer these over scraping or `curl`.

| Tool | When to use |
|------|-------------|
| `pull_request_read` | Read PR details (review, fix-ci) |
| `list_pull_requests` | List open PRs |
| `pull_request_review_write` | Create/submit a review |
| `add_comment_to_pending_review` | Post inline review comments |
| `create_pull_request` | Open a PR (`docs-writer` only) |

For GitHub Actions data (run logs, job status) use the `gh` CLI (`gh run list/view`, `gh pr checks`), not the MCP.

## Context7 (`context7`) — env `CONTEXT7_API_KEY`

Up-to-date library docs.

| Tool | When to use |
|------|-------------|
| `resolve-library-id` | Find the library id first |
| `get-library-docs` | Current docs for Django, DRF, PostgreSQL when knowledge may be stale |

## Notes

- Web/CI data restrictions: do not bypass blocked fetches via `curl`/scripts.
- Secrets (tokens/keys) only via env — never commit them.
- Vet third-party MCP servers/skills before enabling: check what they run, where (local `npx`/Docker), and what they can access (keys, repo, filesystem). Prefer audited, well-known sources.

## Binds these agents (referenced from each agent's prompt)

- `docs-writer` — opens the PR (`create_pull_request` / `gh pr create`).
- `reviewer` — reads PR details via `pull_request_read` at the Quality Gate.
- `api-architect`, `django-developer` — verify current Django/DRF/PostgreSQL APIs via context7 (`resolve-library-id` → `get-library-docs`) before designing/implementing.

> Loaded per-agent via `docs/ai/rules/mcp-stack.md` in each agent's prompt, not via the global CLAUDE.md import block (the orchestrator rarely calls MCP directly).
<!-- Last reviewed/updated: 2026-06-01 (github/context7 via official plugins; .mcp.json is fallback — ADR 0011) -->

<!-- END SOURCE docs/ai/rules/mcp-stack.md -->


<!-- SOURCE docs/ai/rules/migrations-tasks.md SHA256 9e3dc81e26782de61bd81a2dc04857bba014a0b89428efccef1fb4b59af7a7a3 -->

# Migrations & Background Tasks (Celery)

## Migration conventions

- Generate with `makemigrations`; review before committing. One logical change per migration.
- **Never edit an already-applied/committed migration** — create a new one.
- Migrations must be reversible. For `RunPython`, always provide a reverse callable (or `noop` deliberately).
- **Data migrations** are separate from schema migrations and are tested.
- Integrity at the DB level: `constraints`, `unique`, indexes — not only in code.

### Safe changes on large tables

Avoid long locks. Add a column in steps:

1. Add the column **nullable** (fast).
2. Backfill in a data migration (batched if huge).
3. Add the `NOT NULL`/constraint in a follow-up migration.

```python
from django.db import migrations, models

def backfill_slug(apps, schema_editor):
    Post = apps.get_model("blog", "Post")
    for post in Post.objects.filter(slug="").iterator():
        post.slug = slugify(post.title)
        post.save(update_fields=["slug"])

class Migration(migrations.Migration):
    dependencies = [("blog", "0002_post_slug")]
    operations = [
        migrations.RunPython(backfill_slug, migrations.RunPython.noop),
    ]
```

## Background tasks (Celery)

Tasks live in `apps/<domain>/tasks.py`. Broker URL via env. Keep tasks thin — heavy logic in services/models.

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def process_post_analytics(self, post_id: int) -> None:
    # must be idempotent
    PostAnalytics.objects.update_or_create(
        post_id=post_id, defaults={"processed_at": timezone.now()},
    )
```

- **Idempotency**: a task run twice must yield the same result (`update_or_create`, dedupe keys).
- **Retries**: bounded `max_retries` with backoff; set `time_limit` for long tasks.
- **Triggering**: dispatch from signals/services deliberately; do not do guaranteed work inline in the request cycle.
- **Periodic**: schedule via `celery beat`.

## Testing (mandatory)

- Migrations with data logic: test the transform and its reverse.
- Tasks: run synchronously with `CELERY_TASK_ALWAYS_EAGER=True`; test idempotency and that the trigger enqueues the task. See docs/ai/rules/testing.md and docs/ai/rules/tdd.md.
<!-- Last reviewed/updated: 2026-05-27 -->

<!-- END SOURCE docs/ai/rules/migrations-tasks.md -->


<!-- SOURCE docs/ai/rules/no-stubs.md SHA256 c94ca8fe8aefc26de3ba8267e4cfda3d09bee6fd6b5f75c784f3b842553bfb8b -->

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
| apps/ranking/services.py:42 | fixed score until ranking lands | test_ranking_orders_by_score | @your-handle | 2026-05-27 |
```

CI fails if a STUB exists in `apps/` whose file is not listed in `docs/STUBS.md` (see Enforcement). This is what *forces* recording it — unlogged stubs do not merge.

> **Ledger initialization.** On `/bootstrap`, `docs/STUBS.md` is initialized as an **empty ledger for this project** — the header row + the column definitions, with the example/template row removed. A project must never ship the untouched template (an example row referencing `apps/ranking/services.py` that does not exist signals the ledger was never adopted).

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

<!-- END SOURCE docs/ai/rules/no-stubs.md -->


<!-- SOURCE docs/ai/rules/output-language.md SHA256 9de049efae88c3cdf8938fff0f0dcb957b7c20c6e41ac2daad0c391a3852a0ea -->

# Output language

Honor the user's current language preference. Read an existing project-owned
`.claude/rules/output-language.md` when present; never overwrite it on update.
If neither the session nor project declares a preference, ask once.

<!-- END SOURCE docs/ai/rules/output-language.md -->


<!-- SOURCE docs/ai/rules/preflight.md SHA256 bbda44d9ba504352a2e56f98daf753067f357bc05dfa3f6c0998e4807e677386 -->

# Project kickoff preflight (hard gate)

Before agents start work on a (new) project — and before the first feature pipeline — verify that the inputs and access needed to build correctly are present. This is a **hard gate**: if a critical item is missing, agents do NOT start coding; the orchestrator stops and either asks the user or fixes access. Runs automatically at project kickoff and on demand via `/preflight`.

## What to verify (all CRITICAL)

1. **Project brief / description.** A clear statement of what we are building: goals, scope, domain, key requirements. Source: `docs/PROJECT.md`, a README brief, or a description the user provided. If absent or vague → STOP and ask the user for a brief — `ba` cannot write meaningful user stories without it.
2. **Tech stack.** The stack is declared (CLAUDE.md / README: Django 6 · DRF · PostgreSQL 18 · Docker) and dependencies are resolvable (`backend/pyproject.toml` present; versions consistent). If undeclared or contradictory → STOP and confirm with the user.
3. **Library docs access — Context7.** The `context7` MCP is reachable so agents can check current Django/DRF APIs before implementing (`resolve-library-id` works; `CONTEXT7_API_KEY` set). If down → STOP, or proceed only on explicit user override (noting that APIs will be unverified against current docs).
4. **GitHub project access.** `gh auth status` is authenticated AND the project repo is reachable (`gh repo view`), so PRs, CI, and history work. `github` MCP env (`GITHUB_PERSONAL_ACCESS_TOKEN`) set. If no access → STOP.
5. **Maturity stage.** `docs/PROJECT.md` declares a stage (`demo / prototype / PoC / MVP / production`). If absent → ask the user via the runtime's question interface (options: demo / prototype / PoC / MVP / production / other) before dispatching `ba` — the pipeline depth depends on it (`docs/ai/rules/project-maturity.md`). "Other" is treated as MVP until clarified.
6. **API contract link.** `CONTRACT_VERSION` is set in `.env` to a specific `claude-api-contract` tag (e.g. `v0.2.0`) AND `docs/api/openapi.yml` exists and is non-empty. Check: `grep -q '^CONTRACT_VERSION=' .env && test -s docs/api/openapi.yml`. If absent → STOP; run `bash scripts/pull_contract.sh` after setting the version. Without a contract pin, `api-architect` cannot read the schema, `tester` cannot write conformance tests, and CI will fail.

## Gate behavior

- All six are blockers. If any is ❌ → report the readiness checklist and STOP before dispatching `ba` / the feature pipeline.
- Context7 (item 3) may be waived only on **explicit** user override; record that implementation will rely on the agent's training knowledge (knowledge cutoff), not current docs.
- Contract pin (item 6) may be waived only if the project is in `demo` or `prototype` stage AND the user explicitly confirms no conformance testing is needed for this session.
- Never start writing code, schemas, or migrations while a CRITICAL item is ❌.

## Who runs it

- The **orchestrator** runs the preflight at project kickoff (the first feature on a fresh project), delegating access checks (Context7, GitHub, stack deps) to `devops` and brief/stack comprehension to `ba`.
- `ba` confirms it has a usable brief + declared stack + maturity stage BEFORE producing user stories.
- The `/preflight` command runs the same check on demand.

## Relation to `/doctor`

`/doctor` checks the **environment** (tools, services, git hygiene). Preflight checks the **inputs to build** (brief, stack, docs/GitHub access, maturity stage, contract pin). On a fresh machine run `/doctor` first, then preflight before the first feature.

<!-- Last reviewed/updated: 2026-06-08 -->

<!-- END SOURCE docs/ai/rules/preflight.md -->


<!-- SOURCE docs/ai/rules/project-maturity.md SHA256 b5c40dff3d342c9670852ba9c4100cba7b8e00a01fa9489bf250c243defbd7af -->

# Project maturity stage (process scaler)

Declare the project's maturity stage before any feature work starts. The stage scales
**process depth** — pipeline completeness, `devil` usage, review rigour, test coverage
expectations. It does **not** gate-skip or relax TDD, security, or contract-conformance
invariants.

## Taxonomy

| Stage | One-line definition |
|---|---|
| **demo** | Throwaway proof-of-concept; disposable after the meeting. |
| **prototype** | Exploratory; no real users, may break freely. |
| **PoC** | Validates a specific technical hypothesis; short-lived. |
| **MVP** | First real release; real users approaching; the API is a promise. |
| **production** | Live API consumed by real clients; every change has cost. |
| **other** | Treated as **MVP** until clarified. |

## Process matrix (TDD + CI gates always ON)

| Stage | Pipeline depth | `devil` | Quality Gate | Tests expected | Breaking-change attention |
|---|---|---|---|---|---|
| **demo** | ba → api-architect → tester → django-developer → docs-writer | skip | reviewer only | happy path + 401 | low |
| **prototype** | + security-scanner | skip | reviewer + security | + key errors (400/403) | low |
| **PoC** | full | optional | full parallel | + typical errors | medium |
| **MVP** | full | recommended | full (max 2 cycles) | all declared codes | high |
| **production** | full, `devil` first | mandatory | full + adversarial | exhaustive (every code in contract) | strict; breaking → ADR |
| **other** | as MVP until clarified | — | — | — | — |

## Invariants — NEVER overridden by stage

**TDD (Red → Green → Refactor), the CI gates (ruff · stub ledger · contract conformance ·
app README · file-size · pytest), and `permission_classes` on every endpoint are ALWAYS ON,
regardless of stage.**

A stage modulates process depth and completeness — it does not relax:
- the failing test requirement before any production code (docs/ai/rules/tdd.md),
- the no-stub rule (docs/ai/rules/no-stubs.md),
- contract conformance (`scripts/check_contract_conformance.sh`),
- security checks at the Quality Gate (docs/ai/rules/serializers-permissions.md).

## Where the stage lives

Recorded in `docs/PROJECT.md` (**Maturity stage** field). If `PROJECT.md` does not state a
stage, `ba` / `brief-synthesizer` emits an **Open Question**; the orchestrator asks via
the runtime's question interface (options: demo / prototype / PoC / MVP / production / other).
Never assume a stage — "other" is the explicit fallback, not the default silence.

## How to read the matrix

- **Pipeline depth:** agents listed are the minimum; add more if complexity warrants it.
- **`devil`:** "skip" means the orchestrator may omit it by default; the user may invoke it at any stage.
- **Tests expected:** a floor, not a ceiling — add tests for every error code the contract declares.
- **Breaking-change:** "low" relaxes urgency of semver review, not the contract conformance gate.

> First action on any feature: read `PROJECT.md` for the declared stage. No stage → Open
> Question before proceeding. Scale the pipeline against the matrix; never silently skip an
> invariant (docs/ai/rules/workflow.md, docs/ai/rules/preflight.md).

<!-- Last reviewed/updated: 2026-06-08 -->

<!-- END SOURCE docs/ai/rules/project-maturity.md -->


<!-- SOURCE docs/ai/rules/serializers-permissions.md SHA256 f0f3fe42050083f0327cedc51c455a5b5e3e68b1fe441508842010a115bc893c -->

# Serializers & Permissions (DRF)

Validation lives in **serializers**. Authorization lives in **permission classes**. Views stay thin and orchestrate only.

## Serializer validation

Never validate in the view body. Use field- and object-level validators.

```python
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "body", "author", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def validate_title(self, value: str) -> str:
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value

    def validate(self, attrs):
        # cross-field checks here
        return attrs
```

- Split read/write serializers when shapes differ. Use `read_only`/`write_only`.
- Never expose sensitive fields (password, hashes, tokens).
- Set the owner from `request.user` in the view (`perform_create`), not from client input.

## Permission classes

Authorization is separate, testable classes in `apps/<domain>/permissions.py`.

```python
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
```

Wire on the view explicitly:

```python
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

## Rules

- Every endpoint declares `permission_classes` explicitly — never rely on defaults by accident.
- Anonymous → **401**; authenticated-but-not-allowed → **403**.
- Prevent **IDOR**: object-level checks (`has_object_permission`) for anything addressed by id; never trust client-supplied owner/ids.
- Validation errors → **400** with field-keyed messages; conflicts (e.g. duplicate unique) → **409**.
- Throttle sensitive endpoints (login, registration) via `throttle_classes`.

## Authentication (Bearer/JWT + service-flow)

The API is **token-based, not session/cookie** — the primary client profile is
service-to-service (ADR `0018`, D5). `DEFAULT_AUTHENTICATION_CLASSES` is
`rest_framework_simplejwt.authentication.JWTAuthentication`; clients send
`Authorization: Bearer <access>`. Endpoints, codes and bodies are defined by the
external contract (`docs/ai/rules/api-docs.md`); this section is the
implementation doctrine.

**User-flow endpoints** (contract `claude-api-contract`, D1):

| Method + path | Security | Returns |
|---|---|---|
| `POST /api/v1/auth/register` | public | user (+ optional tokens) |
| `POST /api/v1/auth/login` | public | `access` + `refresh` (refresh in the response **body**, D2/ADR `0019`) |
| `POST /api/v1/auth/refresh` | public | new `access` (+ optional rotated `refresh`) |
| `POST /api/v1/auth/logout` | bearer | 204; blacklists the refresh token |

**Service-flow endpoint** (machine-to-machine, D5):

| Method + path | Security | Request | Returns |
|---|---|---|---|
| `POST /api/v1/auth/token` | public | `grant_type=client_credentials`, `client_id`, `client_secret` (+ optional `scope`) | scoped `access` (+ `expires_in`, `scope`) |

- **JWT library:** `djangorestframework-simplejwt` for the user-flow (access +
  refresh-in-body) with `rest_framework_simplejwt.token_blacklist` for
  revocation. The service-flow `/auth/token` is a small custom view that
  authenticates a stored service credential (`client_id`/`client_secret`) and
  issues a JWT whose `scope` claim lists the granted scopes. **Upgrade path:**
  `django-oauth-toolkit` when a project needs standards-compliant OAuth2
  (external client registration, introspection) — record the switch in an ADR.
- **Scopes, not roles, for services.** Non-public endpoints declare the scopes
  they need and enforce them with `apps.common.permissions.HasScope` (reads the
  token's space-delimited `scope` claim), stacked on `IsAuthenticated`:

  ```python
  class OrderViewSet(viewsets.ModelViewSet):
      permission_classes = [permissions.IsAuthenticated, HasScope]
      required_scopes = ["orders:write"]
  ```

- **Short access + revocation.** Keep access lifetimes short (minutes) and rotate
  refresh tokens; blacklist on logout/rotation — a leaked service secret must not
  grant broad, long-lived access.
- **Rate limiting.** Throttle sensitive endpoints (login, register, token) via
  `throttle_classes`; a throttled request returns **429** with a `Retry-After`
  header and the `{"detail": ...}` envelope. Services hit the API harder than
  humans, so the limit must be explicit and predictable.

## Default permission policy (project-wide)

The scaffold sets `DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.IsAuthenticated"]`
in `config/settings/base.py` (`REST_FRAMEWORK`), so **every endpoint is
authenticated by default**. A view that should be public opts OUT explicitly with
`permission_classes = [permissions.AllowAny]` — never by relying on a missing
default. This makes "forgot to set permissions" fail closed (401), not open.
Stack `IsAuthenticated` with object-level classes (e.g. `IsOwnerOrReadOnly`) as
shown above; authenticated-but-not-allowed still returns **403**.

## Error envelope (project-wide contract)

Every non-2xx response uses the external contract's envelope (ADR `0020`),
produced by `apps.common.exceptions.exception_handler` (wired via
`REST_FRAMEWORK["EXCEPTION_HANDLER"]` — see `apps/common/`). Two shapes:

- **Validation errors (400):**

  ```json
  {"errors": [{"field": "<name|null>", "code": "<machine>", "message": "<human>"}]}
  ```

- **Every other handled error (401/403/404/409/429/5xx):**

  ```json
  {"detail": "<human>"}
  ```

- For 400, each entry maps one offending field to its DRF error `code` and
  message; non-field (cross-field) errors use `field: null`; nested serializer
  fields are dotted (`address.zip`).
- `detail` is a single human-readable sentence with no per-field structure (a
  `404`/`NotFound` serializes `{"detail": ...}`, never a loose string or a field
  map).
- Raise `apps.common.exceptions.Conflict` (409) for uniqueness/version clashes —
  do NOT mirror a model's unique constraint as a DRF `UniqueValidator` if you
  want a 409 instead of a 400.
- **429** responses carry a `Retry-After` header alongside the `{"detail": ...}`
  body, per the S2S rate-limit contract (see *Authentication* above).

Do not hand-build per-view error bodies; raise the appropriate DRF exception (or
`Conflict`) and let the handler render the envelope. The convention tests live in
`apps/common/tests/` (pagination, default permission, envelope, throttling).

## Testing (mandatory)

Per endpoint test: success, 400 (validation), 401 (anonymous), 403 (other user), 404, and IDOR (user A cannot touch user B's object). See docs/ai/rules/testing.md.
<!-- Last reviewed/updated: 2026-05-27 -->

<!-- END SOURCE docs/ai/rules/serializers-permissions.md -->


<!-- SOURCE docs/ai/rules/simplicity-surgical.md SHA256 ba7142b621b9cf458bae4006beaa1a8d24449d52c63495f6caf8d08595a4a9b6 -->

# Simplicity First & Surgical Changes

Two behavioral guardrails against the most common LLM-coding failure modes:
over-engineering and collateral edits. They complement `tdd.md` (minimal GREEN),
`no-stubs.md` (no speculative placeholders), `code-style.md` (small functions),
and `git-operations.md` (one branch = one logical change).

## Simplicity First

**The minimum code that solves the stated problem. Nothing speculative.**

- No features beyond what was asked; no "while I'm here" extras.
- No abstraction for single-use code — a model method or a plain function beats a
  service/strategy/factory until a second caller actually exists. Honour
  `architecture.md`: thin views, rich models, no layers introduced ahead of need.
- No "flexibility"/configurability (extra params, settings, hooks) that nobody requested.
- No error handling for impossible scenarios — guard real inputs, not imagined ones.
- If you wrote 200 lines and 50 would do, rewrite it.

The test: *would a senior engineer call this overcomplicated?* If yes, simplify.
This rule applies to the config itself — keep rules and docs terse, not bloated.

## Surgical Changes

**Touch only what the task requires. Every changed line traces to the request.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting that the task didn't touch.
- Don't refactor what isn't broken. Refactoring is its own task — route it through
  `/structure-audit` or `django-refactoring-expert` under green tests, not as a drive-by.
- Match the surrounding style even if you'd personally do it differently.
- If you notice unrelated dead code, *mention* it — don't delete it.

When your own change creates orphans:

- Remove imports/variables/functions that **your** edit made unused.
- Do not remove pre-existing dead code unless explicitly asked.

The test: *can every line of the diff be traced directly to the user's request?*
If a hunk can't, it doesn't belong in this change.

<!-- END SOURCE docs/ai/rules/simplicity-surgical.md -->


<!-- SOURCE docs/ai/rules/tdd.md SHA256 1d610e093d0b0910dfadb84f66d3e66eb3e53566ff38a7ae7c1287b3f0dceb6c -->

# TDD in Python (mandatory)

## Iron rule

**No line of production code without a failing test first.**

Cycle for each unit of functionality:

1. **RED** — write a test describing the expected behavior. Run it — it must fail for the expected reason (not due to an import/syntax error).
2. **GREEN** — write the MINIMAL code to make the test pass. No premature generalization.
3. **REFACTOR** — clean up the code and tests, tests stay green.

Repeat in small steps. One test → a bit of code → green → refactor.

> GREEN may use a temporary stub / hardcoded return to go green fast — but every stub must be marked `# STUB:` and recorded in `docs/STUBS.md`, and must never reach `main` unlogged. Rules and the CI gate: docs/ai/rules/no-stubs.md.

## Double-loop TDD — outside-in at the API boundary

Our adaptation of Harry Percival's *Test-Driven Development with Python* ("Obey the Testing Goat"). We keep his discipline — test-first, Red-Green-Refactor, minimal code, **test behavior not implementation** — but the **outer loop is an API feature test, not a browser functional test**, because for a DRF backend the user-facing boundary is the HTTP endpoint.

- **Outer loop (acceptance / functional):** a failing DRF `APIClient` test for the endpoint. It is our functional test — it drives the feature and goes green only when the whole slice works end to end (status code, response shape, DB state, authorization).
- **Inner loop (unit):** fast RED → GREEN → REFACTOR cycles on model methods, serializer validators, permissions, and services — the small steps that make the outer test pass.

Flow per feature: **outer API test RED → run the inner unit loop (RED→GREEN→REFACTOR) until the outer test is GREEN → refactor.** This maps directly onto the pipeline below (`api-architect` sets the contract → `tester` writes the failing outer test → `django-developer` greens it via inner loops).

Why not the literal browser-driven double-loop here: browser/E2E tests are slow and flaky, so they make a poor tight RED driver — especially for an automated agent that iterates on test output and needs fast, deterministic signals; the backend ships before the frontend (separate PRs), so a browser FT cannot even go red first; and the endpoint, not the rendered page, is the real contract boundary. Browser E2E (`qa`, tooling from the `playwright` plugin) stays a **thin top layer** for genuine cross-stack journeys and post-deploy smoke on staging — never the inner-loop driver. Rationale recorded in `docs/decisions/0001-tdd-outside-in-at-api-boundary.md`.

## Order for a backend feature

1. `api-architect` fixes the endpoint contract (method, path, body, response, codes, permissions).
2. `tester` writes a feature test via DRF `APIClient` that hits the endpoint and checks:
   - status code,
   - response shape (fields, types),
   - DB state after the request,
   - authorization (anonymous / other user → 401/403).
   The test FAILS (the endpoint does not exist yet).
3. `django-developer` adds the model/serializer/view/route — just enough to green the test. Any stub used to go green is marked + logged per docs/ai/rules/no-stubs.md.
4. Refactor + `ruff`.

## What to test / what to skip

**Always test:**
- custom business logic, model methods, serializer validators;
- every endpoint: all response codes, access rights (incl. IDOR — user A cannot touch user B's object), pagination/filters/throttling;
- edge cases and errors (400/401/403/404/409);
- signals, celery tasks, complex queries.

**Can skip:**
- trivial CRUD fully covered by standard DRF with no customization;
- auto-generated migrations without data logic;
- trivial `__str__`.

## Triangulation

Assert behavior from at least 2–3 distinct cases (different inputs → different outputs), not a single example, so a hardcoded/stub return cannot stay green. See docs/ai/rules/no-stubs.md.

## Tools

- `pytest` + `pytest-django` (fixtures, `@pytest.mark.django_db`).
- `factory_boy` for factories instead of manual object creation.

<!-- END SOURCE docs/ai/rules/tdd.md -->


<!-- SOURCE docs/ai/rules/testing.md SHA256 a637acb85daae8f9c6476a4d1df4ae52164acba49262d83e1b6f018300a492ca -->

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

## Commands

```bash
docker compose exec backend pytest
docker compose exec backend pytest --cov=apps --cov-report=term-missing
docker compose exec backend ruff check .
```
<!-- Last reviewed/updated: 2026-07-07 (what-to-test delegated to tdd.md — audit batch B) -->

<!-- END SOURCE docs/ai/rules/testing.md -->


<!-- SOURCE docs/ai/rules/user-guides.md SHA256 d1614042e1ae92d2849b9eb8941639d7fefef5cd733ae17797f6a902a19fbd55 -->

# User-facing guides (mandatory, enforced at the Quality Gate)

The OpenAPI schema and `docs/verify/<feature>.md` prove the contract is correct for a *developer*. They do NOT tell a **human operator** how to actually start using the system. This rule mandates two living guides that grow with the project, so that at any commit a newcomer can stand the system up and drive it end to end:

1. **`docs/guides/admin.md`** — for the **administrator/operator** (the person who runs the service): first start, environment, loading initial data, creating the superuser, the Django admin, day-2 operations (backups, migrations, common troubleshooting).
2. **`docs/guides/api-consumer.md`** — for the **REST API consumer** (a developer integrating against the API): base URL, obtaining auth, a first end-to-end request, pagination/filtering conventions, error format, where the full contract lives (Swagger/OpenAPI).

These are **narrative onboarding documents**, not a contract dump. The contract is OpenAPI (`docs/ai/rules/api-docs.md`); the per-endpoint manual smoke test is `docs/verify/` (`docs/ai/rules/verification.md`). The guides are the **"how do I get started"** layer that sits above both and references them, never duplicating field tables.

## Required sections

### `docs/guides/admin.md` (in order)

1. **Overview** — one paragraph: what the service does, who operates it.
2. **First start** — prerequisites, `cp .env.example .env` + which secrets to fill, `docker compose up -d`, `migrate`, `createsuperuser`. Copy-paste runnable, dev base URL `http://localhost:8000`.
3. **Loading initial data** — how to seed the system: management commands, fixtures (`loaddata`), or the admin import path. Name the real commands the project ships; if none exist yet, say so explicitly (no invented commands).
4. **Django admin** — URL (`/admin/`), what can be managed there, which models are registered.
5. **Day-2 operations** — applying new migrations, backups/restore, reading logs, common failure modes and fixes.
6. **Where to go next** — links to `docs/guides/api-consumer.md`, Swagger UI, `docs/api/INDEX.md`.

### `docs/guides/api-consumer.md` (in order)

1. **Overview** — one paragraph: what the API offers, versioning (`/api/v1/`).
2. **Base URL & schema** — dev URL, link to Swagger UI (`/api/schema/swagger/`), Redoc, and `docs/api/openapi.yml` as the authoritative contract.
3. **Authentication** — how to obtain and send credentials (token/session), with a copy-paste `curl` that gets a token. Placeholders only (`$TOKEN`), never real secrets.
4. **First request, end to end** — one realistic happy-path call (`curl`) against a real shipped endpoint and the expected response shape, so the reader gets a 2xx on their first try.
5. **Conventions** — pagination, filtering/ordering, the standard error/validation body shape, and the status codes the API uses (401/403/400/404/409).
6. **Where to go next** — Swagger UI for the full endpoint list, `docs/verify/<feature>.md` for per-endpoint smoke tests.

Keep both guides copy-paste runnable and **derived from what the project actually ships** — real management commands, real endpoints, real auth flow. Never invent a command or endpoint the code does not have; if a capability is not built yet, write "not yet available" rather than a plausible fiction.

## Source of truth & reconciliation

The guides reference, never restate, the machine-checked sources:

- **Endpoints / auth** mentioned in `api-consumer.md` MUST exist in `docs/api/openapi.yml` (the vendored external contract) and `docs/project-state/endpoints.json`. The contract is the source of truth; if the guide names an endpoint or auth scheme the schema lacks, the guide is wrong.
- **Management commands / data-loading** in `admin.md` MUST correspond to real commands in `backend/apps/**/management/commands/` or documented fixtures. `guide-writer` verifies these against the code before declaring the guide ready.

This is the same anti-drift discipline as `app-readme.md` and `verification.md`: the human narrative is allowed to add *prose and ordering*, but every concrete command, route, and code it names must trace back to the code or schema.

## Lifecycle (grows with the project)

1. **Born at bootstrap.** `/bootstrap` Mode A copies `templates/guides_admin.md` -> `docs/guides/admin.md` and `templates/guides_api_consumer.md` -> `docs/guides/api-consumer.md` as skeletons with `{TODO}` markers. A brand-new project ships the skeletons, not invented content.
2. **Updated in the same PR as user-visible surface changes.** When a feature adds a new way to start, a new data-loading command, a new auth flow, or a new top-level resource, the guide section it affects is updated in that PR — by `guide-writer` in the Documentation phase. The most volatile sections are *Loading initial data* (admin) and *Authentication* + *First request* (api-consumer).
3. **Verified on demand** via `/guides` (regenerate/refresh) — see `.claude/commands/guides.md`.

## Enforcement (Quality Gate, not a CI script)

There is **no standalone shell gate** for the guides (unlike `check_app_readmes.sh`); their quality is narrative and judged by `reviewer` at the Quality Gate plus `guide-writer` in the docs phase:

- `reviewer` blocks a PR that changes user-visible surface — a new/changed **auth flow**, **data-loading command**, **first-start step**, or a new **top-level API resource** — without a corresponding update to the relevant guide. Treat a stale "First start" or "Authentication" section as 🟡 Important.
- `guide-writer` runs the reconciliation above (every command/endpoint the guide names traces to code/schema) before declaring the PR ready, and flags invented or removed references.

## Binds these agents (loaded per-agent via `@`-reference)

- `guide-writer` — owns `docs/guides/admin.md` and `docs/guides/api-consumer.md`; creates them from the templates, keeps them in sync with the shipped surface, and runs the code/schema reconciliation. The dedicated agent for this rule.
- `api-architect` — when a contract change adds/removes an auth flow or a top-level resource, notes that `api-consumer.md` needs the corresponding section update.
- `django-developer` — when adding a management command or data-loading path, flags that `admin.md` *Loading initial data* needs updating.
- `docs-writer` — coordinates with `guide-writer` in the Documentation phase so guides, `docs/api/`, and `docs/verify/` are consistent.
- `reviewer` — at the Quality Gate, blocks PRs that change first-start / data-loading / auth / top-level resources without a guide update.

> Goal: at every commit, an operator can start the system and a developer can make their first successful API call by reading two short, always-current guides — never by reverse-engineering the code.
<!-- Last reviewed/updated: 2026-06-02 (new rule: user-facing admin + api-consumer guides, owned by guide-writer) -->

<!-- END SOURCE docs/ai/rules/user-guides.md -->


<!-- SOURCE docs/ai/rules/verification.md SHA256 b21c21796a10f975b6cc90c4bdff6f6d27afd8feb9066ae4f74bb2b1dff8fe6a -->

# Endpoint verification handoff (mandatory, automatic block)

Every feature that adds or changes an endpoint MUST ship a **human-facing verification guide** so the user (or a reviewer) can confirm the slice works by hitting the live API — via **Swagger UI** and ready-to-paste **`curl` / `httpie`** commands. The automated conformance suite (schemathesis + django-contract-tester, see `docs/ai/rules/api-docs.md`) proves the implementation matches the external contract for CI; this guide is the manual, copy-paste smoke test a person runs against a running server. It is generated automatically at the end of the feature pipeline (this is "Варіант 1" — the automatic verification block) and on demand via `/verify`.

> Why this exists: tests are green inside the container, but the user still wants a quick, concrete "open this URL / run this command / expect this status" checklist to trust the endpoint by hand. The guide is derived from the contract, never hand-invented, so it cannot drift from the real routes.

## The deliverable — `docs/verify/<feature>.md`

One markdown file per feature (slug matches the branch / feature name), written by `docs-writer` in the **Documentation** phase (phase 6) of the pipeline, BEFORE the PR opens. Required sections, in order:

1. **Scope** — one line: which endpoints this feature covers (the same slice the PR ships).
2. **Prerequisites** — base URL (`http://localhost:8000` in dev), how to bring the stack up (`docker compose up -d`), and how to obtain auth (token/session) if the endpoints require it.
3. **Per endpoint** — for each `method path`:
   - **Swagger UI step**: which operation to expand at `/api/schema/swagger/` and what to fill in.
   - **`curl` example**: full command with method, headers, and a realistic request body (no secrets — use placeholders like `$TOKEN`).
   - **Expected**: success status code + the key response fields to look for.
   - **Auth / error cases**: the negative checks that matter — anonymous -> **401**, other user -> **403**, bad body -> **400**, missing -> **404**, conflict -> **409** — each as a one-line `curl` + expected code. Only list the codes the contract actually declares.
4. **Done when** — a short checklist the user ticks: every success case returns its code, every auth/error case returns its code.

Keep it copy-paste runnable. Bodies and codes come from `docs/project-state/endpoints.json` and `docs/api/openapi.yml` (see below) — do not invent fields the schema does not have.

## Source of truth — `docs/project-state/endpoints.json` + the OpenAPI schema

The verification guide is generated from a machine-readable route registry plus the committed (vendored external) OpenAPI schema, so it always matches the real contract:

- **`docs/project-state/endpoints.json`** — the route registry. `api-architect` writes/updates an entry the moment it fixes a contract (phase 2), so the registry is the early, authoritative list of what the feature will expose. Schema per entry:

  ```json
  {
    "method": "POST",
    "path": "/api/v1/articles",
    "app": "articles",
    "feature": "article-crud",
    "auth": "authenticated",
    "statuses": [201, 400, 401],
    "notes": "owner set from request.user"
  }
  ```

  `auth` is one of `anonymous` | `authenticated` | `owner` | `admin`. `path` is the full versioned path (no trailing slash — ADR `0025`). The file is a JSON array of such objects. **Mapping to the contract-side registry:** the contract repo keeps its own committed `docs/project-state/endpoints.json` with a different schema (`operationId`, `scopes`, `auth: "bearerAuth"`, `surface`); this backend registry is derived from the contract in phase 2, not shared with it — `auth` here collapses the contract's `security` + `scopes` into four DRF-permission buckets, and `operationId`/`surface` are intentionally dropped (they matter to codegen/frontends, not to DRF tests).

- **`docs/api/openapi.yml`** — the **external contract** vendored from `claude-api-contract` (pulled via `scripts/pull_contract.sh`, pinned by `CONTRACT_VERSION`). The source of truth for field shapes and the final code set. The backend does not generate it.

### Three-way reconciliation (enforced like `app-readme.md`)

After GREEN, before the PR opens, `docs-writer` reconciles the routes across **three** sources and they MUST agree:

```
docs/project-state/endpoints.json  <->  docs/api/openapi.yml  <->  docs/api/INDEX.md
```

`openapi.yml` (the external contract) is the **source of truth**. If `endpoints.json` or `INDEX.md` disagree (a renamed path, a dropped endpoint, a changed status code), they are wrong and get corrected to match the schema. Stale entries for endpoints no longer in the schema are removed from `endpoints.json`. This is the same discipline the README *Endpoints* section follows — `endpoints.json` simply makes it machine-checkable and feeds `/verify`.

## Lifecycle (per feature)

1. **Phase 2 — contract.** `api-architect` appends/updates the feature's endpoints in `docs/project-state/endpoints.json` as part of fixing the contract (the contract is incomplete until the registry entry exists).
2. **Phases 3-4 — RED/GREEN.** No verification work; the registry entry already exists.
3. **Phase 6 — docs.** `docs-writer`:
   - runs the three-way reconciliation above;
   - generates/refreshes `docs/verify/<feature>.md` from `endpoints.json` + `openapi.yml`;
   - includes the verify file in the PR.
4. **On demand.** `/verify` regenerates `docs/verify/<feature>.md` from the same sources; with `--run` it additionally executes the guide against the live server and reports pass/fail (see `.claude/commands/verify.md`).

## Binds these agents (loaded per-agent via `@`-reference)

- `api-architect` — the contract is incomplete until the feature's routes are recorded in `docs/project-state/endpoints.json` (method, path, app, auth, declared statuses).
- `docs-writer` — owns `docs/verify/<feature>.md`; runs the three-way reconciliation (`endpoints.json <-> openapi.yml <-> INDEX.md`) and generates the guide before declaring the PR ready.
- `reviewer` — at the Quality Gate, flags a PR that adds/changes an endpoint without a matching `docs/verify/<feature>.md` or whose `endpoints.json` disagrees with the schema.
- `tester` — the negative cases listed in the guide (401/403/400/404/409) must each correspond to a real test; the guide is the manual mirror of those tests, never a superset of what is tested.

> Goal: the moment a feature is green, the user has a concrete, contract-derived "hit these routes, expect these codes" guide — generated, never guessed, and impossible to drift from the real API.
<!-- Last reviewed/updated: 2026-06-01 -->

<!-- END SOURCE docs/ai/rules/verification.md -->


<!-- END ROLE PACK tester -->
