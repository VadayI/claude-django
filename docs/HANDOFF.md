# HANDOFF — claude-django

> Поточний знімок репозиторію-шаблону конфігу. Читай першим при під'єднанні; онови наприкінці сесії.
>
> Maintainer · Останнє торкання: 2026-06-04

## Поточний стан

На `main`, tip `d91ba4a` — **запушено** (`origin/main == d91ba4a`). ADR 0015 staging-робота **вже на main** (видалені nginx/systemd-шаблони, доданий `0015-production-ready-staging.md`, `INSTALL_EXTRA=prod` у `backend.Dockerfile`, `check-deploy` у Makefile). Гілка `chore/staging-refine-adr-0015` (`297ebb5`) була дублем цього changeset — видалена локально й на remote; PR #7 закрито.

**Незакомічені правки в робочому дереві** (language-gate цієї сесії, на `main`): новий `.claude/rules/output-language.md` (Українська) + дописаний імпорт у `CLAUDE.md` + оновлені `docs/HANDOFF.md`, `docs/WORKLOG.md`, `docs/lessons.md`. Закомітити в `main` (template-repo дозволяє напряму) — команди в розділі «Наступні кроки».

**Два інциденти середовища цієї сесії (обидва — /mnt 9p):**
- `.git/config` пошкодився (рядки 1–13 цілі, далі NUL-байти) → git падав `fatal: bad config line 14`, через що впав `git commit` (+ git identity не була задана). Лагодиться перезаписом config.
- `docs/HANDOFF.md` **обрізало** MCP-інструментом Edit/Write (4515 B замість повного) — довелося перебудувати через bash heredoc `/tmp`→`cp`→звірка байтів.

## Останнє завершене

- **ADR 0015 «Production-ready staging».** Звірено з паралельним дублем (PR #7): лишено повнішу базу main (`gunicorn.conf.py`, `settings/test.py`), перейнято `INSTALL_EXTRA=prod` (тонкий dev-образ) + Makefile `check-deploy`; прибрано nginx/systemd-шаблони (лишились прозою в admin-гайді). Тепер на `main` (`d91ba4a`).
- **План 0007 (кошик B) — завершено.** Окремий `config/settings/test.py` + production-ready staging (gunicorn-у-контейнері, health-route `/api/v1/health/`).
- **Кошик A deep-research рапорту.** `--reuse-db` + branch coverage, `concurrency` + job summary в CI, Dependabot, governance-рядки.
- **Language-gate.** Зафіксовано українську як мову відповідей проекту (`output-language.md` + імпорт у `CLAUDE.md`).

## Наступні кроки

1. **Закомітити language-gate + wrap-up правки в `main`** (після лагодження `.git/config` + identity, з хост-шела/PowerShell):
   ```
   git add .claude/rules/output-language.md CLAUDE.md docs/HANDOFF.md docs/WORKLOG.md docs/lessons.md
   git commit -m "docs: wrap-up session — Ukrainian output language, HANDOFF/WORKLOG refresh, /mnt truncation lesson"
   git push origin main
   ```

2. **Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті** (НЕ в цьому репо) — головний змістовний крок, бо обидва кошики (A+B) рапорту вичерпано: `pytest` зелений на `config.settings.test`; `ruff check .` чистий (нові `apps/common`); `docker compose -f docker-compose.staging.yml config -q` валідний; `python manage.py check --deploy` на `staging` без критичних ворнінгів; `curl /api/v1/health/` → 200.

3. **Допрацювати похідний `carlsberg-ir-data-service`** (синкнуто вручну, `052ae15`): реєстрація нових агентів у його `CLAUDE.md` + імпорт `@.claude/rules/user-guides.md`, крок file-size-гейту в живому `backend-ci.yml`, запустити `/guides`, переконатись що `bash scripts/check_file_size.sh` проходить перед наступним PR.

4. **Пріоритезувати pre-commit/CI-гард на обрізаний хвіст файлу** — цей інцидент (HANDOFF обрізало, `.git/config` забило NUL) уже втретє за історію кусає на /mnt; перевести з «відкритого питання» в задачу.

5. Після валідації — нова фіча через стандартний пайплайн або наповнення backlog (`templates/todo.md`).

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] **Pre-commit/CI-гард, що падає на обрізаному хвості/NUL-байтах у файлі** (кусало вже кілька сесій на /mnt-mount) — підвищено до кроку №4 вище.
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **У Cowork-сесії Write/Edit заблоковані на `.claude/**`** (protected) — ті файли редагуються через bash + `python pathlib`/`sed`.
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено цією сесією (HANDOFF обрізало до 4515 B; `.git/config` забило NUL). А bash-sandbox іноді віддає **застарілий кеш-інод**. Тому ВСІ правки робимо через **bash heredoc → `/tmp` → `cp` → звірка `wc -c`/`tail`/no-NUL з диска**; ніколи не довіряти return-у самого write-виклику; ніколи не писати в `.git/**` з /mnt-боку.
- **Видалення файлів на mount потребує явного дозволу** (rm дає "Operation not permitted", поки не надано); створення/перезапис працює.
- **git/верифікацію ганяти з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях. `origin/main` — джерело правди.
- **git identity має бути в тому ж шелі, де комітиш**: WSL `~/.gitconfig` і Windows-`%USERPROFILE%\.gitconfig` РІЗНІ — для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private повертає 403; відсутність захисту там очікувана.
- **GitHub-доступ = fine-grained per-repo токен** (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow лікується `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.

> Кореневий `HANDOFF.md` (детальний, 41 КБ) теж відстає (датований 2026-06-01) — його «Остання сесія» вказує на ADR 0007/секрети; за потреби освіжити окремо.

---

> Каденція оновлення: наприкінці сесії, вручну або через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
