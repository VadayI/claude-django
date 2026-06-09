# HANDOFF — claude-django

> Читай ПЕРШИМ на початку нової сесії. Оновлюється `/handoff` наприкінці кожної сесії.
> Хроніка — `docs/WORKLOG.md`; беклог — `docs/todo.md`.

## Поточний стан

На `main`, working tree DIRTY (uncommitted changes: `docs/WORKLOG.md` — незакомічений append після wrap-up). Синхронізовано з `origin/main` (0 ahead / 0 behind). Останній коміт: `898c6aa chore: ADR 0021 — contract pin form (tag + vendored copy + CI drift-gate)`.

## Останнє завершене

- PR #22: chore: ADR 0021 — contract pin form (tag + vendored copy + CI drift-gate) — merged 2026-06-09 ([link](https://github.com/VadayI/claude-django/pull/22))

## В процесі

- (нічого у flight — на `main`, без відкритих PR)

## Наступний крок

Закомітити незакомічені doc-зміни (`docs/WORKLOG.md` + `docs/HANDOFF.md`) перед переключенням контексту.

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — dogfood пройдено (план 0010); лишити рішення після ручної обкатки на кількох реальних задачах (поза скоупом v1).

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено сесіями. Всі правки — через **bash heredoc → scratch в `/dev/shm` → `cp` → звірка `git diff`**; ніколи не довіряти return-у write-виклику. `/dev/shm` scratch НЕ персистує між bash-викликами — write + cp + verify в **одному** виклику.
- **git commit/push — з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях.
- **git identity** — WSL `~/.gitconfig` і Windows `%USERPROFILE%\.gitconfig` РІЗНІ: для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private → 403; очікувана поведінка.
- **GitHub-доступ** = fine-grained per-repo токен (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow → `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.
- **`check_nul_bytes.sh`** — тепер у CI (шаблон `backend-ci.yml`) та доступний локально: `bash scripts/check_nul_bytes.sh`. Захист від /mnt 9p-корупції (NUL-байти + conflict-маркери).
- **Контекст після компакції може «застрягти» в задачах іншого проєкту** — явно перепідтверджуй `cwd` (`/mnt/d/Dev/My/claude-django`) на старті сесії після компакції.

---

> Каденція оновлення: наприкінці сесії через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
