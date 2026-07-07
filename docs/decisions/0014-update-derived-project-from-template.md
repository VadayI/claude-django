# 14. Оновлення похідного проєкту з шаблону — /update-from-template + агент template-sync

- **Status:** Accepted
- **Date:** 2026-06-02
- **Deciders:** Project maintainer
- **Tags:** template, upgrade, sync, agents, commands, derived-projects

## Контекст

За ADR `0002` похідні проєкти «carry their own pinned copy from when the template was forked»: конфіг (`.claude/`, `scripts/`, `CLAUDE.md`, `templates/`) копіюється один раз під час прикріплення/бутстрапу і далі не має каналу зворотного оновлення. Коли шаблон отримує нові агенти/правила/команди/скіли/CI-гейти (як-от гайди й ліміт 800 рядків з ADR 0012/0013), уже створений проєкт не може їх підхопити інакше, ніж ручним копіюванням. `/bootstrap` Mode B лише **дозавершує незавершений** бутстрап (додає відсутні шматки), але **не оновлює** наявні файли до новіших версій. Maintainer попросив зробити з цього першокласну фічу: команда + агент(и) + інструкція в README.

Складність — наосліп перезаписати `.claude/` не можна: там перемішані файли, що належать **шаблону** (безпечно оновлювати), і файли, **специфічні для проєкту** (правлений `CLAUDE.md`, `settings.json`, `.claude/memory/*`, локальний `output-language.md`, `docs/`, `backend/`). Окремий нюанс: derived-проєкти видаляють `templates/` після бутстрапу (`/bootstrap` Step 4), тож нові гейт-скрипти доводиться брати з апстрім-клону й класти в **живі** шляхи + дописувати крок у живий `backend-ci.yml`.

## Рішення

1. **Окремий агент** `template-sync` (sonnet) з явною **класифікацією власності файлів**:
   - *Template-owned* (безпечно перезаписати): `.claude/agents/`, `.claude/commands/`, `.claude/skills/`, `.claude/rules/*.md` крім `output-language.md`, `scripts/detect-env.py`/`log-cmd.py`/`session-start.sh`/`setup-wsl.sh`.
   - *Merge-by-hand* (лише адитивний дифф, без повної заміни): `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`, живий `.github/workflows/*.yml`, за потреби `pyproject.toml`/`docker-compose.yml`/`Makefile`.
   - *Project-owned* (не чіпати): `.claude/memory/*`, `output-language.md`, `docs/**`, `backend/**`, `.env`.
2. **Нові гейт-скрипти** з апстрім-`templates/scripts/`, відсутні в живому `scripts/`, копіюються в живі шляхи (+chmod), а їхній крок і path-тригер дописуються в живий `backend-ci.yml` (адитивно).
3. **Команда** `/update-from-template [url|ref] [--dry-run]`: клонує апстрім (за замовчуванням `VadayI/claude-django`, або URL власного форку), створює feature-гілку, диспетчить `template-sync`, і відкриває **PR**. `--dry-run` — лише звіт без змін.
4. **PR-only.** На відміну від `/bootstrap` Mode A, оновлення похідного проєкту йде звичайним PR-флоу (`git-operations.md`) — це не bootstrap-виняток.
5. **Маркер версії** `.claude/memory/template-sync.json` (`upstream`, `synced_sha`, `synced_at`, `previous_sha`) — щоб наступний запуск звітував лише про зміни з минулого синку.

## Наслідки

**Плюси.** Закрито реальну прогалину: похідні проєкти можуть підхоплювати покращення шаблону однією командою, не втрачаючи кастомізацій. Класифікація власності робить операцію безпечною; merge-by-hand-файли не затираються мовчки. Підтримка власних форків через параметр URL.

**Мінуси.** Merge-by-hand-частина (`CLAUDE.md`/`settings.json`/CI) лишається напівручною — повністю автоматичний 3-way merge свідомо не робимо (ризик мовчки зламати проєктні налаштування). Агент покладається на евристику «це шаблон vs похідний проєкт», щоб не синкати шаблон сам у себе.

**Відкинуті альтернативи.**
- *Розширити `/bootstrap` Mode B на «оновлення»* — відхилено: Mode B про відсутні шматки незавершеного бутстрапу, змішувати з апгрейдом наявних файлів небезпечно й заплутано.
- *Git-submodule / subtree для `.claude/`* — відхилено: важче для соло-флоу, конфліктує з проєктними правками в тих самих файлах, ламає «один `git pull`».
- *Повний автоматичний overwrite `.claude/`* — відхилено: знищив би `output-language.md`, `memory/`, правлений `CLAUDE.md`, `settings.json`.
- *Окремий standalone-скрипт замість агента* — відхилено: merge-by-hand і вирішення власності потребують судження, що краще лягає на агента, ніж на bash.

## Наслідки для файлів

- `.claude/agents/template-sync.md` — новий агент.
- `.claude/commands/update-from-template.md` — нова команда.
- `CLAUDE.md`, `.claude/rules/workflow.md` — реєстрація агента (опціональні агенти/таблиця).
- `README.md` — нова секція «Updating an existing project from the template» + пункт команди + рядок агента + лічильники.
- `templates/PROJECT_README.md` — вказівник у «Useful commands».
- (runtime, у похідному проєкті) `.claude/memory/template-sync.json` — маркер синку.

> **Примітка (2026-07-07, аудит v2, батч G):** перелік template-owned у п.1 містить
> історичні імена `log-cmd.py` / `session-start.sh`; актуальні — `scripts/policy/log_command.py`
> та `scripts/session-start.py` (перейменовано батчами A/D аудиту 2026-07-07). Поточний
> авторитетний ownership-перелік підтримується в `.claude/agents/template-sync.md`.
