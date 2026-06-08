# Plan 0013 — project-maturity + DoD + contract-link

> Status: ✅ DONE · seeded 2026-06-08 · Driver: user request — maturity stage / DoD / contract-link відсутні в claude-django
> Type: config-template change. Немає production Django-коду — тільки правила, шаблони, команди, агенти.

## Status

| Step | State | Owner |
|---|---|---|
| 1. Створити `.claude/rules/project-maturity.md` | done | orchestrator |
| 2. Оновити `templates/PROJECT.md` (maturity + contract + DoD) | done | orchestrator |
| 3. Оновити `.claude/commands/synthesize-brief.md` | done | orchestrator |
| 4. Оновити `.claude/agents/brief-synthesizer.md` | done | orchestrator |
| 5. Оновити `.claude/rules/preflight.md` | done | orchestrator |
| 6. Оновити `CLAUDE.md` (додати global import) | done | orchestrator |

## Goal

Додати до claude-django три відсутніх механізми, наявних у claude-api-contract:
1. Таксономія зрілості проєкту (demo/PoC/MVP/production) + process matrix.
2. Checklist Definition of Done (standard CI gates + project-specific criteria).
3. Явна прив'язка backend до `claude-api-contract` (`CONTRACT_VERSION`) як hard gate у `/preflight`.

## Approach

- `project-maturity.md` — адаптація contract-repo версії для Django: ті ж stage-назви, process matrix на основі django-pipeline (глибина TDD, Quality Gate, `devil`).
- `templates/PROJECT.md` — додати поля Maturity stage + Contract + §7 DoD перед Open questions.
- `synthesize-brief.md` — у Step 2 явно вимагати stage + DoD + CONTRACT_VERSION; якщо відсутній — AskUserQuestion.
- `brief-synthesizer.md` — зробити ці три поля required (ніколи не blank, не {TODO}).
- `preflight.md` — додати пункти 5 (maturity stage) і 6 (contract pin) як CRITICAL.
- `CLAUDE.md` — додати `@.claude/rules/project-maturity.md` до global import block.

## Verification

- `grep -r "project-maturity" .claude/` → hits у CLAUDE.md + preflight.md.
- `grep "Maturity stage\|Definition of Done\|CONTRACT_VERSION" templates/PROJECT.md` → всі три є.
- `grep "AskUserQuestion\|maturity\|CONTRACT_VERSION" .claude/commands/synthesize-brief.md` → є.
- `grep "Maturity stage\|CONTRACT_VERSION\|Definition of Done" .claude/rules/preflight.md` → є.
- `tr -dc '\000' < <file> | wc -c` → 0 NUL bytes на всіх змінених файлах.

## Execution log

> Append-only.
- Step 1 ✓ `.claude/rules/project-maturity.md` створено (60 рядків, 0 NUL).
- Step 2 ✓ `templates/PROJECT.md` оновлено: Maturity stage + Contract + §7 DoD (94 рядки).
- Step 3 ✓ `.claude/commands/synthesize-brief.md` оновлено: required fields + AskUserQuestion logic.
- Step 4 ✓ `.claude/agents/brief-synthesizer.md` оновлено: Required fields секція (110 рядків).
- Step 5 ✓ `.claude/rules/preflight.md` оновлено: пункти 5 (maturity) + 6 (contract pin).
- Step 6 ✓ `CLAUDE.md` оновлено: `@.claude/rules/project-maturity.md` в global import block.
- Всі файли: 0 NUL bytes, cmp clean.
