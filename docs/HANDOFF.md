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
