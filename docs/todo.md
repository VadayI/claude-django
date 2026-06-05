# Project backlog

Long-term, cross-session backlog for this template repo — items that survive between `claude` sessions (unlike in-conversation `TaskCreate`/`TaskUpdate`). The `auditor` agent (`/audit`) reads this alongside `.claude/memory/command-log.jsonl`.

## To do — 🟡 from collision audit (2026-06-05)

- [ ] **brief-synthesizer без `SendMessage`** — єдиний не-read-only агент без нього; решта командних агентів (template-sync/guide-writer/auditor) мають. Уніфікувати: додати SendMessage у `.claude/agents/brief-synthesizer.md` (або задокументувати виняток).
- [ ] **Orphaned-скіли** — `architecture-designer` і `test-master` не активує жоден агент. Прив'язати: `test-master` → `tester.md`, `architecture-designer` → `api-architect.md`/`domain-architect.md`.
- [ ] **Дубль WORKLOG/ADR/lessons** між `/update-docs` і `/wrap-up` (обидва через `docs-writer`) — ризик дубльованих записів. Звузити WORKLOG лише до `/wrap-up` або явно розмежувати в `update-docs.md`.
- [ ] **HANDOFF регенерується двічі** — `wrap-up` «run the /handoff logic» замість виклику. Зробити `/wrap-up` викликом `/handoff` (єдине джерело генерації).
- [ ] **dba ↔ django-refactoring-expert** — спільний тригер `N+1`/`optimize query`, розмежування одностороннє. Додати зустрічну згадку в `dba.md`.
- [ ] **code-reviewer ↔ security-reviewer** — `code-reviewer` skill дублює security-блок (IDOR/401/403/секрети) і відстав від тіла агента `reviewer` (немає 800-рядків, silent-failure). Прибрати дубль + синхронізувати з агентом.
- [ ] **Реєстрація команд у CLAUDE.md** — `/plugins`, `/handoff`, `/set-language` ніде не згадані (доповнюють процеси плагінів/контексту/мови).
- [ ] **mcp-stack.md — orphan-rule** — жодного посилання ніде. Підключити (через агентів docs-writer/reviewer або в import-блок) чи свідомо лишити поза контекстом оркестратора.

## To do — гігієна

- [ ] Прибрати `templates/__pycache__` з git (скомпільований Python потрапив у каталог шаблонів).
- [ ] (опц.) `ba`/`api-architect`/`domain-architect` мають `Write` без `Edit` — для append у `endpoints.json` доречніший `Edit`.

## Done

- [x] **4×🔴 з аудиту** — `config.md` baseline, фантом-скіл `api-architect`, уточнення `debugger`, формат помилок `drf-api-design`, orphaned HANDOFF/todo в CLAUDE.md+git-operations.md · 2026-06-05
