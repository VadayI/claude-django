# User-facing guides (mandatory, enforced at the Quality Gate)

The OpenAPI schema and `docs/verify/<feature>.md` prove the contract is correct for a *developer*. They do NOT tell a **human operator** how to actually start using the system. This rule mandates two living guides that grow with the project, so that at any commit a newcomer can stand the system up and drive it end to end:

1. **`docs/guides/admin.md`** — for the **administrator/operator** (the person who runs the service): first start, environment, loading initial data, creating the superuser, the Django admin, day-2 operations (backups, migrations, common troubleshooting).
2. **`docs/guides/api-consumer.md`** — for the **REST API consumer** (a developer integrating against the API): base URL, obtaining auth, a first end-to-end request, pagination/filtering conventions, error format, where the full contract lives (Swagger/OpenAPI).

These are **narrative onboarding documents**, not a contract dump. The contract is OpenAPI (`@.claude/rules/api-docs.md`); the per-endpoint manual smoke test is `docs/verify/` (`@.claude/rules/verification.md`). The guides are the **"how do I get started"** layer that sits above both and references them, never duplicating field tables.

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

- **Endpoints / auth** mentioned in `api-consumer.md` MUST exist in `docs/api/openapi.yml` (the re-derived contract) and `.claude/memory/endpoints.json`. The schema is the source of truth; if the guide names an endpoint or auth scheme the schema lacks, the guide is wrong.
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

## Binds these agents (rule is auto-loaded)

- `guide-writer` — owns `docs/guides/admin.md` and `docs/guides/api-consumer.md`; creates them from the templates, keeps them in sync with the shipped surface, and runs the code/schema reconciliation. The dedicated agent for this rule.
- `api-architect` — when a contract change adds/removes an auth flow or a top-level resource, notes that `api-consumer.md` needs the corresponding section update.
- `django-developer` — when adding a management command or data-loading path, flags that `admin.md` *Loading initial data* needs updating.
- `docs-writer` — coordinates with `guide-writer` in the Documentation phase so guides, `docs/api/`, and `docs/verify/` are consistent.
- `reviewer` — at the Quality Gate, blocks PRs that change first-start / data-loading / auth / top-level resources without a guide update.

> Goal: at every commit, an operator can start the system and a developer can make their first successful API call by reading two short, always-current guides — never by reverse-engineering the code.
<!-- Last reviewed/updated: 2026-06-02 (new rule: user-facing admin + api-consumer guides, owned by guide-writer) -->
