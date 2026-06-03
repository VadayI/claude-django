# common

> Cross-cutting infrastructure shared by every domain app. Copied into a new
> project as `backend/apps/common/` by `/bootstrap` (Mode A). Convention:
> `.claude/rules/app-readme.md`.

## Purpose

`common` owns the project-wide REST conventions that every other app inherits
**by configuration, not by copy-paste**: the single error envelope
(`{"error": {"code", "message", "details"}}`) applied via DRF's
`EXCEPTION_HANDLER`, the `Conflict` (409) exception, and the OpenAPI
documentation of that envelope. It deliberately owns **no domain data** — it has
no production models, no business resources, and no public REST endpoints of its
own. Domain apps depend on it; it depends on no domain app.

## Models

None in production. A throwaway `SampleItem` model lives under
`apps/common/tests/models.py` and exists **only** to exercise the shared
conventions (pagination, default permission, error envelope, throttling) in the
test suite. It is given a table at test time via `MIGRATION_MODULES` redirected
to `apps.common.tests.migrations` (see `config/settings/dev.py`); it never ships
a migration into the production `common` app.

## Endpoints

None. `common` exposes no routes. The sample endpoints used by the convention
tests are mounted only inside an override `ROOT_URLCONF`
(`apps/common/tests/urls_sample.py`) during those tests — never in
`config/urls.py`.

Schema detail for real endpoints lives in `docs/api/openapi.yml` (single source
of truth, see `.claude/rules/api-docs.md`).

## Signals / Celery tasks

None.

## Cross-app dependencies

- Read by: every domain app (indirectly, via the project `REST_FRAMEWORK`
  settings — default permission, pagination, throttling, and `EXCEPTION_HANDLER`
  all point here).
- Reads from / writes to: nothing.

## Decisions

- `docs/decisions/` — the ADR introducing project-wide DRF conventions in the
  scaffold (error envelope + default permission policy). See
  `.claude/rules/serializers-permissions.md` for the runtime contract.

## How to extend

To add another cross-cutting concern (e.g. a base pagination class with a larger
page size, a custom renderer, a shared mixin), add it here and wire it through
`config/settings/base.py` so all apps inherit it uniformly — do not duplicate
the behaviour in individual domain apps. New error codes go in
`_STATUS_TO_CODE` inside `exceptions.py` and the documented shape in `schema.py`.

<!-- Last reviewed/updated: 2026-06-03 -->
