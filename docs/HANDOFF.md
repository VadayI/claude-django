# 2026-09-25 — P07 integrated: core pinned to contract main `db342b7`

Branch `feat/p07-shared-memory` (PR #46): `main` merged in after fix PR #45 (`2bc0d76`), then the integrated repin. Contract PR #66 is merged as `db342b7`; PR #46 merges on the user's command of 2026-09-25 (D01).

- `docs/ai/core-source.json`: `pin_status: integrated`, `source_commit` = `observed_upstream_main` = `db342b78ee8d085b6f5b854cabd217d69176d99c`; the payload is unchanged from the development pin `f8e3162` (same manifest digest). `tests/test_ai_delivery.py` asserts the integrated pin again.
- This session: `docs/sessions/20260925T090423Z-claude-2757a2.md` (task, checks, limitations, next step).
- Next: P08 (Git lifecycle G0–G9). The P07 runtime acceptance run (docs/ai/session-continuity.md) is still NOT_VERIFIED.

# 2026-09-25 — P07 shared output-language preference (development core)

Branch `feat/p07-shared-memory` (draft PR #46); commit `2f74f7f` on top of `1fa8fbc`, development pin `f8e3162`. Nothing is merged (D01).

- Output language: `python scripts/ai/project_state.py --root . --language` reports it; `--apply` moves a legacy `.claude/rules/output-language.md` to `docs/ai/overrides/output-language.md` (pointer left behind). Runtime acceptance run: docs/ai/session-continuity.md.
- This session: `docs/sessions/20260925T081415Z-claude-98b041.md` (task, checks, limitations, next step).
- Next: After contract #66 is merged on the user's command: repin to the integrated core and restore «Tymczasowy pin deweloperski»; then #45 → #46. The runtime acceptance run follows docs/ai/session-continuity.md.

# 2026-09-25 — P07 session continuity (development core)

Branch `feat/p07-shared-memory` (draft PR #46); commit `f564a08` on top of `769ad91`, development pin `6fb703a`. Nothing is merged (D01).

- Start every session with `python scripts/ai/session_context.py --root .` (branch/HEAD, settings, documentation map, latest record, snapshot diff; no `.ai-runtime` needed). End with `--new-record --agent <runtime>` and, after the commit, `--check` (docs/ai/session-continuity.md).
- This session: `docs/sessions/20260925T075805Z-claude-615ac5.md` (task, checks, limitations, next step).
- Next: After contract #66 is merged on the user's command: `core_sync.py --integrated-pin` to the integrated core, restore the assertions marked «Tymczasowy pin deweloperski» in `tests/test_ai_delivery.py`, then merge #45 → #46. After that, P08.

# 2026-09-24 — P07 consumers adopted (draft PR #46, development core)

Branch `feat/p07-shared-memory` on top of `fix/p06-django-consistency` (PR #45).
The vendored core is the contract `feat/p07-shared-memory` head recorded in
`docs/ai/core-source.json` (`pin_status: development`); repin to integrated after
the contract P07 PR merges and restore the assertions marked «Tymczasowy pin
deweloperski» in `tests/test_ai_delivery.py`.

- A2 closed: `scripts/policy/runtime_gate.py` calls the shared detector
  in-process (no hook-written JSON can satisfy or fake it); `NO_ENV_DETECT` now
  means the shared detector is missing/broken. `scripts/session-start.py` runs
  `scripts/ai/detector.py --write` (`.ai-runtime/environment.json`) and then
  `scripts/detect-env.py` (`.ai-runtime/env-detect.json`).
- Runtime writers (`detect-env.py`, `policy/log_command.py`) migrate their own
  legacy `.claude/memory` records via `project_state.migrate_runtime()` and refuse
  on a conflict; `backend_policy.py` and `templates/.github/workflows/backend-policy.yml`
  accept `docs/project-state/endpoints.json` or the legacy path; `seed_preflight.py`
  rejects `docs/project-state/` and `.ai-runtime/` as seed paths.
- Rules/workflows/agents/commands/README/templates use `docs/project-state/`
  and `.ai-runtime/`; role packs and instruction manifest regenerated.
- Verified on Linux Python 3.13.7: `core_sync --check`, `generate_adapters --check`,
  `build_instruction_manifest --check` PASS; `tests/` 38 OK; SessionStart smoke
  moved a legacy `env-detect.json` and wrote both reports.
- Next: merge fix PR #45, contract P07, then repin here; P08. Merge only on the
  user's command.

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
