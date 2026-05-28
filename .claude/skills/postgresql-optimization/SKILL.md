---
name: postgresql-optimization
description: PostgreSQL and Django ORM optimization — N+1 elimination, indexes, select_related/prefetch_related, EXPLAIN, safe migrations. Activate when working with the DB / slow queries.
---

# PostgreSQL + ORM Optimization

## N+1
- `select_related` (FK/OneToOne, JOIN), `prefetch_related` (M2M/reverse FK).
- `only()`/`defer()` to narrow the selection; `annotate()`/`aggregate()` instead of Python loops.

## Indexes
- Index fields used in filters/sorting/joins; composite indexes ordered by condition.
- `Meta.indexes`, `db_index=True`, unique constraints.

## Diagnostics
- `EXPLAIN ANALYZE` for slow queries; `django-debug-toolbar` locally; query counter in tests (`assertNumQueries`).

## Safe migrations
- Reversible; data migrations separately and with tests.
- On large tables avoid long locks (add nullable, then backfill, then constraint).
<!-- Last reviewed/updated: 2026-05-27 -->
