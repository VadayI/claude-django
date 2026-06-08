# HANDOFF — claude-django template repo

> Read this first when joining the project. Updated by `/handoff` at the end of each session.
> Canonical chronicle → `docs/WORKLOG.md`. Task backlog → `docs/todo.md`.

---

## Поточний стан

На `main`, робоче дерево **DIRTY** (`docs/plans/0012-nul-guard.md` untracked; `docs/WORKLOG.md`, `docs/HANDOFF.md` — зміни wrap-up). Синхронізовано з `origin/main`. Останній коміт: `82287d6 chore: NUL-byte + conflict-marker guard`.

## Останнє завершене

- PR [#19](https://github.com/VadayI/claude-django/pull/19): `chore: NUL-byte + conflict-marker guard` — merged 2026-06-08.

## В роботі

- (нічого в польоті — `main` чистий, немає відкритих PR)

## Наступний крок

**Закомітити незакомічені зміни перед перемиканням контексту.** `docs/plans/0012-nul-guard.md`, `docs/WORKLOG.md`, `docs/HANDOFF.md` оновлено у поточному wrap-up — треба закомітити й запушити.

З хост-шела (WSL2):
```bash
git add docs/plans/0012-nul-guard.md docs/WORKLOG.md docs/HANDOFF.md
git commit -m "docs: wrap-up 2026-06-08 — ba explicit PROJECT.md + plan 0012 NUL-guard"
git push origin main
```

## Наступні кроки (черга)

1. **Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті** (НЕ в цьому репо) —
   обидва кошики (A+B): `pytest` зелений; `ruff check .` чистий; `docker compose -f
   docker-compose.staging.yml config -q` валідний; `python manage.py check --deploy` без
   критичних ворнінгів; `curl /api/v1/health/` → 200.
2. **Допрацювати похідний `example-service`** (синкнуто вручну, `052ae15`): реєстрація
   нових агентів у його `CLAUDE.md` + імпорт `@.claude/rules/user-guides.md`, крок
   file-size-гейту в живому `backend-ci.yml`, запустити `/guides`, переконатись що
   `bash scripts/check_file_size.sh` проходить перед наступним PR.
3. (опц.) Спостерігати дисципліну живого плану на наступних реальних задачах; розглянути
   CI-гард «план оновлено в тому ж PR» (поза скоупом v1).
4. Після валідації — нова фіча через стандартний пайплайн або наповнення backlog
   (`templates/todo.md`).

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — dogfood пройдено (план 0010); лишити рішення після ручної обкатки на кількох реальних задачах (поза скоупом v1).
- [ ] Plan 0011 open question — точна форма пінування контракту: лише `CONTRACT_VERSION=vX.Y.Z` + raw URL, чи додатково контрольна сума `openapi.yml`?

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено сесіями. Всі правки — через **bash heredoc → `/dev/shm` → `cp` → звірка `git diff`**; ніколи не довіряти return-у write-виклику.
- **git commit/push — з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях.
- **git identity** — WSL `~/.gitconfig` і Windows `%USERPROFILE%\.gitconfig` РІЗНІ: для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private → 403; очікувана поведінка.
- **GitHub-доступ** = fine-grained per-repo токен (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow → `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.
- **`check_nul_bytes.sh`** — тепер у CI (шаблон `backend-ci.yml`) та доступний локально: `bash scripts/check_nul_bytes.sh`. Захист від /mnt 9p-корупції (NUL-байти + conflict-маркери).

---

> Каденція оновлення: наприкінці сесії через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
