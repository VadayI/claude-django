# План 0009 — Доробка 🟡-беклогу: консистентність конфігу шаблону

> Статус: ✅ ВИКОНАНО (2026-06-05) — Коміти A/B/C/D застосовані, 3 відкриті питання закриті · Driver: пункти 5–12 з `docs/todo.md`
> Тип: правки конфіг-шаблону (агенти / команди / скіли / правила / CLAUDE.md). Коду немає → feature-pipeline не застосовується.

## Мета

Закрити 8 🟡-розбіжностей, виявлених аудитом колізій (2026-06-05). Усі — точкові доку/конфіг-правки без логіки. Принцип: **звірити історією/grep → мінімальна правка → grep-верифікація**. Жодних нових абстракцій (Simplicity First).

## Спосіб виконання (важливо для цього mount)

- Усі правки — через **bash heredoc → `/tmp` → `cp` → звірка `wc -c`/`tail`/no-NUL**. MCP Edit/Write на /mnt обрізають хвіст — не використовувати.
- `git add/commit/push` — з **host-шела**, не з sandbox (9p ламає index/config). Template-repo дозволяє прямий push у `main`, але групуємо по логічних комітах.
- Жодних записів у `.git/**` з /mnt-боку.

## Згрупування у 4 логічні коміти

Вісім пунктів природно лягають у 4 теми. Кожна тема = окремий коміт (одна гілка = одна логічна зміна).

---

### Коміт A — Консистентність агентів (пункти 5, 6, 9)

**5. `brief-synthesizer` без `SendMessage`.**
- Файл: `.claude/agents/brief-synthesizer.md`, рядок 6 `tools: [Read, Glob, Grep, Write, Bash]`.
- Дія: додати `SendMessage` у масив `tools` → `[Read, Glob, Grep, Write, Bash, SendMessage]`. Уніфікує з рештою командних агентів (`template-sync`/`guide-writer`/`auditor` його мають).
- Ризик: нульовий — лише розширення можливостей агента.

**6. Скіли-сироти `architecture-designer`, `test-master`.**
- Підтверджено grep: на них не посилається жоден агент (лише власний SKILL.md).
- Патерн прив'язки в репо: агент додає рядок-виноску `> ... Skill: <name>.` (як `tester`→`pytest-tdd`, `api-architect`→`drf-api-design`, `domain-architect`→`ddd-strategic-design`).
- Дія:
  - `.claude/agents/tester.md` — додати `test-master` поряд із `pytest-tdd` (виноска наприкінці).
  - `.claude/agents/api-architect.md` — додати `architecture-designer` поряд із `drf-api-design`.
  - (опц.) `.claude/agents/domain-architect.md` — згадати `architecture-designer`, якщо його зміст про bounded contexts/структуру перетинається з DDD.
- ⚠️ **Перед прив'язкою — звірити зміст на дублювання.** Якщо `test-master` ≈ `pytest-tdd`, а `architecture-designer` ≈ `drf-api-design`/`ddd-strategic-design`, то правильна дія — **видалити сироту**, а не прив'язати дубль (прецедент: `react-vite-client` видалено цієї серії). Рішення приймаємо після читання двох SKILL.md. → див. «Відкриті питання» нижче.

**9. `dba` ↔ `django-refactoring-expert` — односторонній крос-ref.**
- Зараз: `refactoring-expert` згадує `dba` («coordinate with dba», «Overlaps with dba»), але `dba.md` не згадує refactoring-expert при спільному тригері `N+1`/`optimize query`.
- Дія: у `.claude/agents/dba.md` додати один рядок-виноску: для рефакторингу заради чистоти коду (не лише запитів) → `django-refactoring-expert`. Робить розмежування двостороннім.
- Ризик: нульовий.

---

### Коміт B — Дедуплікація команд контексту (пункти 7, 8)

**7. `update-docs` ↔ `wrap-up` — дубль WORKLOG/lessons/ADR.**
- Обидві команди (через `docs-writer`) пишуть `docs/WORKLOG.md` + `lessons.md` + ADR. Запуск обох в одній сесії → дубльовані записи.
- `update-docs.md` зараз НЕ згадує `wrap-up` і не розмежовує ролі (підтверджено grep — 0 збігів).
- **Рекомендований розподіл ролей** (на затвердження):
  - `wrap-up` = **кінець сесії**: канонічний власник підсумкового WORKLOG-запису сесії + HANDOFF + commit-пропозиція.
  - `update-docs` = **середина сесії**: інкрементальне освіження доків (api/INDEX, README, ADR за потреби), БЕЗ підсумкового WORKLOG-запису сесії.
- Дія: у `update-docs.md` додати явну ремарку «WORKLOG session-summary належить `/wrap-up`; тут — лише точкові доку-оновлення, не дублюй підсумок сесії». Зустрічно — у `wrap-up.md` лишити WORKLOG за собою (вже так).
- ⚠️ Це політичне рішення → винесено в «Відкриті питання».

**8. HANDOFF регенерується двома командами.**
- `handoff.md` — **канонічний генератор** (підтверджено: «Pairs with /wrap-up… /handoff ONLY touches HANDOFF.md»).
- `wrap-up.md` рядок 41: «Regenerate HANDOFF.md by running the `/handoff` logic (or delegating to docs-writer)» — **переказує** логіку замість делегувати → ризик дрейфу двох генераторів.
- Дія: переписати крок 41 `wrap-up.md` на однозначне делегування: «виконай `/handoff` (єдине джерело генерації HANDOFF) — не дублюй його логіку тут», зберігши post-check `grep -c '{TODO}'`.
- Ризик: нульовий, лише прибирає дубль інструкції.

---

### Коміт C — Дедуплікація скілів рев'ю (пункт 10)

**10. `code-reviewer` skill дублює security-блок `security-reviewer` і відстав від агента `reviewer`.**
- Факти: `code-reviewer/SKILL.md` (32 р.) містить security-перевірки (IDOR/401/403/секрети) — дубль `security-reviewer/SKILL.md` (38 р.). До того ж `reviewer.md` (тіло агента) вже має **800-рядків** і **silent-failure** гейти, яких у скілі нема (відстав).
- Розмежування агентів: `reviewer` (Skill: `code-reviewer`) і `security-scanner` (Skill: `security-reviewer`) працюють паралельно в Quality Gate.
- Дія:
  - Прибрати з `code-reviewer/SKILL.md` security-блок (рядки про IDOR/401/403/секрети) — лишити його власнику `security-reviewer`; натомість дописати коротке посилання «security-аспекти → security-reviewer skill».
  - Синхронізувати `code-reviewer/SKILL.md` із тілом `reviewer.md`: додати 800-рядків ліміт + silent-failure (запис у БД без валідації формату) + simplicity/surgical.
- Ризик: низький; перевірити, що жоден агент окрім `reviewer` не активує `code-reviewer`.

---

### Коміт D — Реєстрація команд і підключення orphan-rule (пункти 11, 12)

**11. `/plugins`, `/handoff`, `/set-language` не зареєстровані в CLAUDE.md.**
- Команди існують (`.claude/commands/{plugins,handoff,set-language}.md`), але CLAUDE.md їх не згадує, хоча документує суміжні процеси (плагіни Scope 2, context-sync п.5, output-language §0).
- Дія, точково:
  - `/handoff` — у п.5 «Context in Git» вже згадано (рядок 39: «`/handoff` refreshes HANDOFF.md alone») ✅ → перевірити, можливо вже покрито, тоді пропустити.
  - `/set-language` — додати згадку в IMPORTANT §0 (output-language gate): «змінити мову згодом — `/set-language`».
  - `/plugins` — додати короткий рядок у секцію про baseline плагінів / Stack або в «Available agents/commands» хвіст, що `/plugins` керує встановленням.
- Ризик: нульовий (доку-доповнення).

**12. `mcp-stack.md` — справжній orphan-rule.**
- Підтверджено: на правило не посилається ні CLAUDE.md import-блок, ні агенти — лише ADR 0011 / план 0001 / todo / WORKLOG (історичні згадки, не активне підключення).
- Зміст релевантний агентам (`github`/`context7` MCP-інструменти, заборона curl-обходу).
- **Два варіанти** (на затвердження):
  - (A) Підключити в import-блок CLAUDE.md (після `mcp`-суміжних правил) — стане частиною контексту оркестратора завжди.
  - (B) Прив'язати точково через агентів, що користуються MCP (`api-architect`/`django-developer`/`reviewer` → context7/github), як виноску-Skill-подібне посилання.
- Рекомендація: **(B)** — оркестратор сам MCP-інструменти майже не зве; правило потрібне виконавчим агентам. Менше роздуття глобального контексту (Simplicity First для самого конфігу).
- ⚠️ → «Відкриті питання».

---

## Порядок виконання

1. Коміт A (агенти) — найшвидший, нульовий ризик. Перед п.6 прочитати 2 orphan-SKILL.md → рішення bind vs delete.
2. Коміт D (реєстрація/orphan-rule) — доку-доповнення.
3. Коміт B (команди контексту) — після узгодження розподілу ролей update-docs/wrap-up.
4. Коміт C (скіли рев'ю) — найбільш змістовний; синхронізація з тілом агента.
5. **Верифікація** (нижче) → оновити `docs/todo.md` (перенести в Done) + WORKLOG + HANDOFF → коміти з host-шела.

## Верифікація (обов'язковий крок)

Grep-based, після кожного коміту:
- п.5: `grep SendMessage .claude/agents/brief-synthesizer.md` → є.
- п.6: `grep -rl "test-master\|architecture-designer" .claude/agents/` → ≥1 агент кожен (або скіл видалено й немає згадок-сиріт).
- п.9: `grep "django-refactoring-expert" .claude/agents/dba.md` → є.
- п.7: `grep -i "wrap-up\|session-summary" .claude/commands/update-docs.md` → є розмежування.
- п.8: `grep -n "/handoff" .claude/commands/wrap-up.md` → делегування, без переказу логіки.
- п.10: `grep -i "IDOR\|secret" .claude/skills/code-reviewer/SKILL.md` → прибрано; `grep "800\|silent" ...` → додано.
- п.11: `grep "/set-language\|/plugins" CLAUDE.md` → є.
- п.12: import-блок CLAUDE.md АБО агенти посилаються на `mcp-stack`.
- Цілісність файлів: `wc -c` + `tail -3` + перевірка на NUL (`grep -c $'\\x00'`) кожного зміненого файла перед комітом.

## Відкриті питання (потребують рішення до/під час виконання)

1. **п.6 bind vs delete** — після читання `test-master`/`architecture-designer` SKILL.md: прив'язати чи видалити як дубль? (Рекомендація: видалити, якщо зміст ≈ наявних `pytest-tdd`/`drf-api-design`.)
2. ~~**п.7 розподіл WORKLOG**~~ — ✅ ВИРІШЕНО (2026-06-05): `wrap-up` = єдиний власник WORKLOG + lessons; `update-docs` синкає лише api/README + ADR. Застосовано в `update-docs.md`.
3. ~~**п.12 mcp-stack підключення**~~ — ✅ ВИРІШЕНО (2026-06-05): варіант **B** — хвіст «Binds these agents» у `mcp-stack.md` + посилання `@.claude/rules/mcp-stack.md` у 4 агентах (api-architect, django-developer, docs-writer, reviewer). Не в global import-блоці.

## Поза скоупом

- Пункти гігієни з `docs/todo.md` (прибрати `templates/__pycache__`, `Write`→`Edit` у ba/api-architect) — окремий дрібний коміт, не частина цього плану.
- Реальна staging-валідація на bootstrap-проєкті (крок 3 HANDOFF) — окрема сесія, не тут.
