# HANDOFF — claude-django

> Читай ПЕРШИМ на початку нової сесії. Оновлюється `/handoff` наприкінці кожної сесії.
> Хроніка — `docs/WORKLOG.md`; беклог — `docs/todo.md`.

## Поточний стан

На `main`, working tree DIRTY (uncommitted changes: `docs/WORKLOG.md`, `docs/HANDOFF.md` — wrap-up doc-зміни). Синхронізовано з `origin/main` (0 ahead / 0 behind). Останній коміт: `3952357 docs: resolve 5 open architecture questions + clean merged branches`.

## Останнє завершене

- PR #22: chore: ADR 0021 — contract pin form (tag + vendored copy + CI drift-gate) — merged 2026-06-09 ([link](https://github.com/VadayI/claude-django/pull/22))

## В процесі

- (нічого у flight — на `main`, без відкритих PR)

## Наступний крок

Закомітити незакомічені doc-зміни (`docs/WORKLOG.md` + `docs/HANDOFF.md`) перед переключенням контексту (з хост-шела WSL2).

## Відкриті питання

_(всі питання вирішено 2026-06-09)_

- [x] `template-sync` — 3-way merge чи additive-diff? **Рішення: лишити additive-diff + surface-conflicts.** Безпечніший підхід, не ризикує затерти локальні кастомізації.
- [x] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`)? **Рішення: ТАК.** Дає базу для `git diff` при першому `/update-from-template`. _(реалізація — окрема задача)_
- [x] При апгрейді до Pro/Team — rulesets чи classic branch protection? **Рішення: classic як дефолт; rulesets — тільки коли repo Public або Pro/Team підтверджено в `env-detect.json`. Не міняти поведінку зараз.**
- [x] Чи `/wrap-up` сам комітить doc-зміни? **Рішення: «propose, user commits» — поточна поведінка зберігається.** Git-операції — з хост-шела, свідомо.
- [~] **«Живий план»: CI-гард «план оновлено в тому ж PR»** — dogfood пройдено (план 0010); **відкладено** до ручної обкатки на кількох реальних задачах (поза скоупом v1).

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
