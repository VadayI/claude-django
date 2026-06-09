# HANDOFF — claude-django

> Каденція оновлення: наприкінці сесії через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.

## Поточний стан

На `main`, working tree **DIRTY** (uncommitted: `docs/WORKLOG.md`, `docs/HANDOFF.md` — wrap-up 2026-06-09). Синхронізовано з `origin/main` (0 ahead / 0 behind). Останній коміт: `516ee68 docs: clear todo backlog — move 3 completed items to Done (#21)`.

## Останнє завершене

- PR #21: docs: clear todo backlog — 3 пункти → Done — merged 2026-06-09 ([link](https://github.com/VadayI/claude-django/pull/21))
- PR #20: chore: ignore `.claude/*.lock` runtime lock files — merged 2026-06-09 ([link](https://github.com/VadayI/claude-django/pull/20))

## В процесі

- (нічого у flight — на `main`, без відкритих PR)

## Наступний крок

**Закомітити wrap-up doc-зміни** (template-repo: прямий коміт у `main` дозволено політикою цього репо).

```bash
# з хост-шела (не з sandbox — 9p-правило):
git add docs/WORKLOG.md docs/HANDOFF.md
git commit -m "docs: wrap-up 2026-06-09 — /audit hygiene (.gitignore lock + todo cleanup)"
```

Після коміту — наступна черга:
1. `/doctor` — аудит середовища (відсутній у command-log за останні 14 днів).
2. Опційно: cross-repo note у `claude-api-contract/templates/verify_TEMPLATE.md` (PR у тому репо).
3. Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті.

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — dogfood пройдено (план 0010); лишити рішення після ручної обкатки на кількох реальних задачах (поза скоупом v1).
- [ ] Plan 0011 open question — точна форма пінування контракту: лише `CONTRACT_VERSION=vX.Y.Z` + raw URL, чи додатково контрольна сума `openapi.yml`?

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
