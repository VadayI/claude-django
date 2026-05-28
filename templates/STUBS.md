# Stub ledger

Every `# STUB:` / `NotImplementedError("STUB: …")` in `backend/apps/` must be listed here, or the CI stub-gate (`scripts/check_stubs.sh`) fails the PR. Remove the row when the stub is replaced by real logic. Policy: `.claude/rules/no-stubs.md`.

Paths are relative to `backend/` (e.g. `apps/ranking/services.py:42`).

| File:line | Reason | Test that must force real impl | Owner | Date |
|---|---|---|---|---|
| _(example)_ apps/ranking/services.py:42 | fixed score until ranking service lands | test_ranking_orders_by_score | @VadayI | 2026-05-27 |

> Place this as `docs/STUBS.md` in a real project (created with the skeleton in README Step 2).

<!-- Last reviewed/updated: 2026-05-27 -->
