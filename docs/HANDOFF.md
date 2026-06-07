# HANDOFF — claude-django template repo

> Read this first when joining the project. Updated by `/handoff` at the end of each session.
> Canonical chronicle → `docs/WORKLOG.md`. Task backlog → `docs/todo.md`.

---

## Поточний стан

На гілці `chore/update-contract-pin-v0.2.0`, PR [#17](https://github.com/VadayI/claude-django/pull/17) відкритий, CI у стані `pending`. 1 коміт попереду `origin/main`. Робоче дерево **DIRTY** — несзакомічені зміни до `docs/WORKLOG.md`, `docs/HANDOFF.md`, `docs/plans/0011-contract-inversion.md` (результат поточного `/wrap-up`).

Попередній коміт: `2b6bbb7 chore: bump CONTRACT_VERSION to v0.2.0`

**Що зроблено в цій сесії:**
- Проведено аналіз готовності шаблону до споживання `claude-api-contract` → всі компоненти (pull_contract.sh, check_contract_conformance.sh, schemathesis + django-contract-tester, CI gate) присутні й закомічені.
- Виявлено й виправлено gap #1: auth-шляхи в контракті `v0.1.1` (`/auth/...`) розходилися з доктриною claude-django (`/api/v1/auth/...`). Контракт виправлено (`v0.2.0`), тут підняли пін.
- Upstream-блокер план 0011 крок 0 знятий — `claude-api-contract` має теги `v0.1.0`, `v0.1.1`, `v0.2.0`.

## Останнє завершене

- PR [#16](https://github.com/VadayI/claude-django/pull/16): docs/contract inversion readme claude md — merged 2026-06-07

## В роботі

- PR [#17](https://github.com/VadayI/claude-django/pull/17): `chore: bump CONTRACT_VERSION to v0.2.0` — open, CI pending
- `docs/plans/0011-contract-inversion.md` — план інверсії контракту, PR1–PR5 внесено до working tree, але не замержено окремими гілками/PR (крок 0 → `done`, решта `in_progress`)

## Наступний крок

**Закомітити зміни поточного wrap-up і замержити PR #17.**

З host-шела (WSL2):
```bash
cd /mnt/d/Dev/My/claude-django
git add docs/WORKLOG.md docs/HANDOFF.md docs/plans/0011-contract-inversion.md
git commit -m "docs: wrap-up — bump CONTRACT_VERSION to v0.2.0, refresh HANDOFF/WORKLOG"
git push origin chore/update-contract-pin-v0.2.0
# потім: gh pr merge 17 --squash (або через UI)
```

Після мерджу — `git checkout main && git pull`, потім визначитися з наступним пріоритетом: замержити план 0011 PR1–PR5 або перейти до реальної валідації bootstrap-проєкту.

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] **Pre-commit/CI-гард, що падає на обрізаному хвості/NUL-байтах у файлі** (кусало вже кілька сесій на /mnt-mount).
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — dogfood пройдено (план 0010); лишити рішення після ручної обкатки на кількох реальних задачах (поза скоупом v1).
- [ ] Plan 0011 PR1–PR5 — внесені до working tree, потребують окремих гілок/PR/мерджів з host-шела.

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено сесіями. Всі правки — через **bash heredoc → `/dev/shm` → `cp` → звірка `git diff`**; ніколи не довіряти return-у write-виклику.
- **git commit/push — з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях.
- **git identity** — WSL `~/.gitconfig` і Windows `%USERPROFILE%\.gitconfig` РІЗНІ: для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private → 403; очікувана поведінка.
- **GitHub-доступ** = fine-grained per-repo токен (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow → `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.

---

> Каденція оновлення: наприкінці сесії через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
