# HANDOFF — claude-django

> Поточний знімок репозиторію-шаблону конфігу. Читай першим при під'єднанні; онови наприкінці сесії.
>
> Maintainer · Останнє торкання: 2026-06-05

## Поточний стан

На `main`. **Незакомічені правки цієї сесії** (🟢-беклог + README + закриття п.2) — 9 файлів:

- **Агенти (7):** `api-architect` (+`Edit`), `auditor` (тригер `workflow audit`), `brief-synthesizer` (color→purple), `template-sync` (color→gray), `dba` (+migrations-tasks rule), `django-developer` (+migrations-tasks rule), `debugger` (drop phantom `systematic-debugging`).
- **`CLAUDE.md`** — примітка «Rule scoping» (6 agent/command-scoped правил задокументовано).
- **`README.md`** — Rules 17 → 19 (+`simplicity-surgical`, `output-language`).

> Цілісність звірено: **0 NUL, 0 обрізаних**. Раніша примітка про false-positive `output-language.md` неактуальна (його немає в `git status`).

## Останнє завершене

- **🟢-беклог аудиту** закрито: `Edit` для `api-architect`; тригер `auditor` `audit`→`workflow audit`; cyan розведено (brief-synthesizer→purple, template-sync→gray; cyan = пара архітекторів); orphan-rule `migrations-tasks.md` прив'язано до `dba`+`django-developer`; «Rule scoping» у CLAUDE.md.
- **п.2 (биті скіл-прив'язки)** закрито повністю: `systematic-debugging` (фантом) у `debugger` → наявний Bug Fix Pipeline + `tdd.md`; `api-design-principles` прибрано раніше.
- **README** звірено з фактом: єдина застарілість — лічильник правил (виправлено); agents 22 / skills 12 / commands 20 коректні.

## Наступні кроки

1. **Закомітити правки цієї сесії в `main`** (host-шел, template-repo дозволяє прямий push). Merge-послідовність (4 логічні коміти):
   ```bash
   git checkout main && git pull
   # 1) green-backlog config cleanup
   git add .claude/agents/api-architect.md .claude/agents/auditor.md .claude/agents/brief-synthesizer.md .claude/agents/template-sync.md .claude/agents/dba.md .claude/agents/django-developer.md CLAUDE.md
   git commit -m "fix(config): green-backlog — Edit tool, audit trigger, agent colors, migrations-tasks wiring, rule-scoping doc"
   # 2) debugger (closes item 2 — broken skill refs)
   git add .claude/agents/debugger.md
   git commit -m "fix(debugger): drop phantom systematic-debugging skill, reference Bug Fix Pipeline + tdd rule"
   # 3) README
   git add README.md
   git commit -m "docs(readme): rules count 17 -> 19 (simplicity-surgical, output-language)"
   # 4) context
   git add docs/WORKLOG.md docs/HANDOFF.md
   git commit -m "docs(context): wrap-up — WORKLOG/HANDOFF refresh"
   git push origin main
   ```
   > Лише явні шляхи (НЕ `git add .`).
2. **Впровадити «живий план»** — `docs/plans/0010-living-plan-workflow.md`, кроки 1–8 (з минулої сесії, ще не зроблено).
3. **п.13** — зробити `ba` явним споживачем `docs/PROJECT.md` (`ba.md`).
4. (з минулих сесій) Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті (НЕ в цьому репо).
5. (з минулих сесій) Pre-commit/CI-гард на обрізаний хвіст/NUL файлу.

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] **Pre-commit/CI-гард, що падає на обрізаному хвості/NUL-байтах у файлі** (кусало вже кілька сесій на /mnt-mount) — крок №5 вище.
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — після ручної обкатки дисципліни (план 0010, поза скоупом v1).

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **У Cowork-сесії Write/Edit заблоковані на `.claude/**`** (protected) — ті файли редагуються через bash + `python pathlib`/`sed`.
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено сесіями. Тому ВСІ правки робимо через **bash heredoc → `/tmp` → `cp` → звірка `wc -c`/`tail`/no-NUL з диска** (NUL перевіряти `LC_ALL=C grep -c -P '\x00'`, а НЕ `$'\x00'` — той матчить усе); ніколи не довіряти return-у самого write-виклику; ніколи не писати в `.git/**` з /mnt-боку.
- **Видалення файлів на mount потребує явного дозволу** (rm дає "Operation not permitted", поки не надано); створення/перезапис працює.
- **git/верифікацію ганяти з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях. `origin/main` — джерело правди.
- **git identity має бути в тому ж шелі, де комітиш**: WSL `~/.gitconfig` і Windows-`%USERPROFILE%\.gitconfig` РІЗНІ — для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private повертає 403; відсутність захисту там очікувана.
- **GitHub-доступ = fine-grained per-repo токен** (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow лікується `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.

> Кореневий `HANDOFF.md` (детальний, 41 КБ) теж відстає (датований 2026-06-01); за потреби освіжити окремо.

---

> Каденція оновлення: наприкінці сесії, вручну або через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
