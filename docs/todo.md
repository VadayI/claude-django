# Project backlog

Long-term, cross-session backlog for this template repo — items that survive between `claude` sessions (unlike in-conversation `TaskCreate`/`TaskUpdate`). The `auditor` agent (`/audit`) reads this alongside `.claude/memory/command-log.jsonl`.

## To do — нове (2026-06-05)

- [ ] **п.13 — `ba` не споживає `docs/PROJECT.md` явно.** Вихід `/synthesize-brief` прив'язаний лише на рівні preflight; агент `ba` згадує абстрактний «brief», не названий читати `docs/PROJECT.md` першим. Зробити прив'язку явною в `ba.md` (Read `docs/PROJECT.md` як основне джерело вимог, якщо існує).
- [ ] **«Живий план» — впровадити план `docs/plans/0010-living-plan-workflow.md`** (кроки 1–8: шаблон `templates/plan.md` → правило `living-plan.md` → CLAUDE.md/workflow → промпти агентів → tools `Edit` для ba/api-architect → верифікація). Дизайн затверджено, 3 відкриті питання закриті.

## To do — гігієна

- [ ] Прибрати `templates/__pycache__` з git (скомпільований Python потрапив у каталог шаблонів).

## Done

- [x] **4×🔴 з аудиту** — `config.md` baseline, фантом-скіл `api-architect`, уточнення `debugger`, формат помилок `drf-api-design`, orphaned HANDOFF/todo в CLAUDE.md+git-operations.md · 2026-06-05
- [x] **8×🟡 з аудиту (п.5–12)** — Коміти A/B/C/D: SendMessage brief-synthesizer; скіли-сироти прив'язано; dba↔refactoring; WORKLOG→wrap-up; HANDOFF→/handoff; code-reviewer dedup+sync; /plugins,/set-language; mcp-stack orphan-rule. Деталі — `docs/plans/0009-*.md`, WORKLOG 2026-06-05 · 2026-06-05
- [x] **ba/api-architect `Edit`** — згорнуто в план 0010 (Крок 7), не окремий пункт · 2026-06-05
