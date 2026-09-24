# 2026-09-24 — P07 core delivered with a development pin

Branch `feat/p07-shared-memory` on top of `fix/p06-django-consistency`. The
rebased P07 core (contract `feat/p07-shared-memory` head
`1235a23f8f77d7dff4e91e039cf60877ae794ce9`, manifest digest `512798fc…`) is
vendored with `pin_status: development`: `scripts/ai/project_state.py`,
`docs/ai/project-state-migration.md`, updated `docs/ai/{schemas,launchers}.md`.
Do not call this integrated. After the contract P07 PR merges, repin with
`core_sync.py --integrated-pin` and restore the integrated assertions in
`tests/test_ai_delivery.py`. Consumer adoption (registry checks, env/log
writers, seed/update ownership, docs) is the remaining P07 work; no legacy
migration has been run against project data.

# 2026-09-24 — post-P06 consistency, integrated core 9db26a0

Branch `fix/p06-django-consistency` on top of `main` `9b7b867` (P06 merged via
PR #42, hosted conformance closeout via #43/#44). Integrated so far: P04
instruction seed, P05 detector/exact-candidate runner, P06 explicit CI mode
(`scripts/ci_mode.py`), owned Git hooks and the derived backend catalog with one
representative hosted PASS (run 36040082142, 13/13). Not delivered: P07 shared
project state, P08 Git lifecycle, P10/P11 roles, P12 full Codex role/command
parity, P13 acceptance.

- Core receipt repinned from `pin_status: development` / `90fdafd` (a branch
  commit already merged through contract PR #62) to integrated contract main
  `9db26a0c65b970c223ab034750f3019ac59c5e2e`; payload bytes unchanged
  (manifest digest `131f17e9…`).
- `.gitignore` now excludes `/.ai-runtime/`, where `scripts/ai/runner.py`
  writes results; derived projects seeded from this file no longer risk
  committing runner evidence.
- `docs/ai/workflows/bootstrap.md`, `docs/ai/production-structure.md` and
  `README.md` no longer describe the CI choice as future P05/P06 work.
- Verified on Linux Python 3.13.15: `core_sync --check`,
  `generate_adapters --check`, `build_instruction_manifest --check` PASS;
  `tests/` 36 OK, `scripts/ai/test_git_hooks.py` 5 OK.
- Next: P07 delivery of the rebased shared-state core (development pin until
  the contract P07 PR is merged), then P08. Merge only on the user's command.

Earlier handoffs follow as historical context.

# 2026-09-20 — P04 family runtime checkpoint

Base: 7adc1d154978628b08b8a472c05b243f0a74adee; task branch
feat/shared-runtime-delivery in an isolated clone. Original checkout untouched.
Integrated contract core b6d1b3d is vendored autonomously; source receipt checks,
Windows Python 3.14 and Linux Python 3.13 fresh/repeat/conflict fixtures passed.
Installer and both Makefiles expose the shared runtime. Core update preserves
project docs/settings and rejects custom files; no app code/models/migrations changed.
This is component delivery, not runnable Django or full Codex role acceptance.
Next: legacy launcher/bootstrap migration and P05–P13. Merge requires user command.

Earlier handoff follows as historical context:
# HANDOFF — claude-django

> Read this first when joining the project in a new session.
> Regenerated: 2026-07-07 (після батчів F–L аудиту v2)

---

## Current state

На `main` @ `985e01d`. Робоче дерево: ~51 незакомічений файл — повний результат аудиту v2: звіт + батчі **F, G, I, H, J, K, L** + ADR `0024`/`0025`/`0026` + нова команда `/adopt`. Усі 5 рішень мейнтейнера прийняті й реалізовані. Чекає 3 комітів з host shell.

## Last finished

- Аудит v1: батчі A–E (`4f89c22..985e01d`).
- Аудит v2: звіт `docs/reviews/2026-07-07-deep-audit-v2.md` + батчі F–L реалізовані й верифіковані локально (повний перелік — WORKLOG 2026-07-07): контракт-дефолти і дисципліна (ADR `0025`), Windows gh (ADR `0022` пропагований), плагін-базлайн v2 (ADR `0024`), контекст-дієта (import-блок 16→7), `/adopt` (ADR `0026`), гігієна.

## In progress

- Коміт + пуш з host shell (сендбокс не комітить — 9p ламає `.git` index): 3 коміти — звіт / конфіг F–K / docs L.

## Next step

1. **Host shell** (PowerShell / Git Bash): 3 коміти + `git push` (команди — у чаті сесії 2026-07-07; склад — за WORKLOG-переліком).
2. **Перша CLI-сесія** — верифікації з `docs/todo.md`: log-hook пише `command-log.jsonl`; MCP-інструменти видимі агентам (reviewer → `pull_request_read`); демоція правил не зламала агентів (django-developer бачить api-docs/code-style/simplicity-surgical); заодно `/doctor`.
3. **Плагіни в UI**: `/plugin install superpowers@claude-plugins-official`; видалити стару інсталяцію superpowers@superpowers-marketplace; engineering — особисто за бажанням (ADR `0024`).
4. **Батч M**: окремий PR у `claude-api-contract` — README Status (v0.3.0+ = template releases), consumer-секція (реальний механізм піна: pull_contract --check, НЕ check_contract_sync.sh/lock.json), форма `CONTRACT_REPO` (slug).
5. Опційно далі: справжній контрактний реліз (v0.5.0 з openapi.yml) у contract-репо → підняти пін тут через PR + `gh variable set CONTRACT_VERSION`.

## Open questions

- [ ] (немає — рішення 1–5 аудиту v2 прийняті 2026-07-07 і зафіксовані в ADR `0024`–`0026`)

## Environment notes

- Cowork на /mnt (9p): правки лише bash+python через /dev/shm→cp з cmp/NUL-верифікацією; `git commit`/`push` — тільки host shell (див. `docs/lessons.md`).
- Хроніка H1 2026 — `docs/WORKLOG-2026-H1.md`; сесії 2026-06-10…2026-07-06 без WORKLOG-записів (джерело — git log).

## 2026-09-20 — safe legacy launcher checkpoint

Shared compatibility source: integrated contract commit 485bb7ae64e5c09ce046ea5cae6e92fd641a7ffe.
Contract core tests: Windows 43 PASS + 1 symlink SKIP; Linux all 44 PASS.
Django/React pins reference merged contract PR #57 at integrated commit 485bb7ae64e5c09ce046ea5cae6e92fd641a7ffe.
Legacy .env is parsed as selected literal data, never executed; credentials affect
only the child, preserving blank fallback and PAT precedence. Known legacy wrappers
migrate by exact hash; custom wrappers conflict before writes. Windows PowerShell
and Git Bash version probes passed. These are not model-session acceptance.
React actual main-to-candidate upgrade/generator check passed; Django old-seed
component upgrade/repeat passed. Full bootstrap, CI-choice and P05+ remain pending.
All PRs remain unmerged; a new explicit user command is required for merge.
