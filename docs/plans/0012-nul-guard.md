# Plan 0012 — NUL-guard у CI

> Status: ✅ DONE · seeded 2026-06-08 · Driver: відкрите питання з HANDOFF + черга /audit
> Type: infra / CI-template change. Немає production-коду Django; пайплайн `ci-cd-engineer → reviewer`.
>
> **Living plan** — дисципліна в `.claude/rules/living-plan.md`. Оркестратор сіє цей файл на початку нетривіальної задачі й тримає **Status table** + **Execution log** актуальними. Рішення ніколи не переписуються — зміни йдуть в **Amendments** з inline-покажчиком.

## Status

| Step | State | Owner |
|---|---|---|
| 1. Написати `scripts/check_nul_bytes.sh` | done | ci-cd-engineer |
| 2. Додати крок у `.github/workflows/backend-ci.yml` | done | ci-cd-engineer |
| 3. Code review | done | reviewer |
| 4. PR відкрити й злити | done | ci-cd-engineer |

## Goal

Захистити репо від тихого 9p-пошкодження (файл із NUL-байтами або обрізаним хвостом), що вже двічі призводило до `0-byte` блобів у `main` (інциденти `e0ae693`, `0de247b`). Одночасно ловити незавершені merge-conflict-маркери (`<<<<<<<`, `=======`, `>>>>>>>`), які також ламають агентні файли.

## Approach

Один bash-скрипт `scripts/check_nul_bytes.sh`:
- ітерує всі tracked-файли (`git ls-files`) в переданих шляхах або в `.claude/` + `scripts/` + `templates/` за замовчуванням,
- перевіряє кожен файл на NUL-байти (`tr -dc '\000' | wc -c`),
- перевіряє на merge-conflict-маркери (`git grep -lE '^(<<<<<<<|=======|>>>>>>>)'`),
- виводить імена проблемних файлів і завершується `exit 1` за будь-якої знахідки.

Крок у CI (`backend-ci.yml`) — окремий job або step `nul-guard`, що запускає скрипт ПЕРЕД lint/tests, бо пошкоджений файл ламає всі подальші кроки некоректним чином.

**Scope:** лише `.claude/`, `scripts/`, `templates/`. Файли `backend/` (Python) уже захищені ruff-парсером, який упаде на будь-якій бінарній бяці. Шлях може бути розширений пізніше.

## Steps

1. Написати `scripts/check_nul_bytes.sh` (bash, ≤40 рядків, перевірка NUL + merge-маркери, справляється з пробілами в іменах, виводить інструкцію з відновлення).
2. Додати крок `nul-guard` у `.github/workflows/backend-ci.yml` (або окремий job на початку).
3. Verify локально: запустити скрипт на чистому репо → `exit 0`; впровадити тестовий NUL-файл → `exit 1`.
4. PR через `ci-cd-engineer` → code review через `reviewer`.

## Verification

- `bash scripts/check_nul_bytes.sh` на чистому репо → `exit 0`.
- `printf '\x00' >> .claude/agents/ba.md && bash scripts/check_nul_bytes.sh` → `exit 1` + повідомлення про ba.md; прибрати NUL потім.
- CI Job `nul-guard` проходить на PR із чистими файлами.
- Merge-conflict-маркер у тимчасовому файлі → `exit 1`.

## Open questions

- [ ] Чи вмикати скрипт як pre-commit hook (через `.git/hooks/pre-commit`) на додачу до CI? (Не в скоупі v1 — CI достатньо; hook можна додати вручну локально.)
- [ ] Розширити scope на `backend/` теж? (ruff-парсер вже захищає Python; лишити поки `.claude/` + `scripts/` + `templates/`.)

## Execution log

> Append-only.

- 2026-06-08 — план сіяний оркестратором (задача з відкритого питання HANDOFF).
- 2026-06-08 — reviewer: gate 2×🟡 Important → назад до ci-cd-engineer (=======regex + root workflow scope).
- 2026-06-08 — reviewer (pass 2): ✅ gate passed; PR #19 mergeable.
- 2026-06-08 — PR #19 merged (squash) → 0012 DONE.
- 2026-06-08 — ci-cd-engineer: `check_nul_bytes.sh` + CI step written; PR #19 opened (chore/nul-guard-ci).
- 2026-06-08 — ci-cd-engineer: reviewer findings fixed — dropped ambiguous `={7}$` arm from conflict-marker regex (only `^<{7} ` and `^>{7} ` are unambiguous git markers); removed out-of-scope `.github/workflows/backend-ci.yml`; pushed 35565fb.

## Amendments

_(none yet)_
