# 8. Ручне створення репозиторію + fine-grained per-repo PAT

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** Project maintainer
- **Tags:** security, bootstrap, github, pat, access

## Контекст

Початкова модель доступу `/bootstrap` (Mode A) була максимально автоматизована: вона сама викликала `gh repo create`, робила перший `push`, реєструвала `backend-ci` як status-check і вмикала branch protection. Для цього потрібен був **classic PAT** з широкими скоупами (`repo`, `workflow`, `admin:repo_hook`, `delete_repo`) — фактично токен, що бачить **усі** репозиторії користувача. Fine-grained PAT (`github_pat_...`) був **жорстко заблокований** (`FINE_GRAINED_PAT_NOT_SUPPORTED`), бо він не віддає OAuth-скоупи через `X-OAuth-Scopes` і не має `createRepository`.

Maintainer вважає вимогу класичного «адмін-ключа на весь акаунт» надмірною для соло-розробки: один скомпрометований токен відкриває всі репозиторії. Бажана модель — **мінімальний доступ під конкретний проект**.

Окремий факт, що зробив рішення можливим: з серпня 2025 GitHub підтримує **template URLs для fine-grained токенів** (changelog `2025-08-26-template-urls-for-fine-grained-pats`) — назву, опис і дозволи репозиторію (`contents`, `pull_requests`, `workflows`, `administration`, ...) можна пре-заповнити через query-параметри сторінки `https://github.com/settings/personal-access-tokens/new`. Вибір конкретного репозиторію («Only select repositories») лишається ручним кроком в UI. Тобто інструмент може згенерувати лінк створення токена **під конкретний проект**.

## Рішення

Повна заміна моделі доступу. `/bootstrap` більше **не створює репозиторій автоматично** і не вимагає classic PAT.

1. **Репозиторій створює людина вручну** на GitHub (порожній — без README/`.gitignore`/ліцензії, щоб перший push був чистим), і дає `/bootstrap` посилання/`owner/slug`.
2. **Доступ — fine-grained per-repo токен.** `/bootstrap` і `/doctor` генерують template-URL під конкретний `OWNER/SLUG` з мінімальними дозволами репозиторію:
   - `Contents: Read and write` (`contents=write`) — клон і push коду;
   - `Metadata: Read-only` — обов'язковий, додається автоматично;
   - `Pull requests: Read and write` (`pull_requests=write`) — PR-флоу (Mode B + feature pipeline);
   - `Workflows: Read and write` (`workflows=write`) — коміт/оновлення `.github/workflows/backend-ci.yml`;
   - `Administration: Read and write` (`administration=write`) — branch protection (Step 5).
   Згенерований лінк (приклад під `OWNER/SLUG`):
   ```
   https://github.com/settings/personal-access-tokens/new?name=claude-django+SLUG&description=Scaffold+and+maintain+OWNER/SLUG+via+claude-django&contents=write&pull_requests=write&workflows=write&administration=write
   ```
   Користувач довибирає Resource owner = `OWNER` і Repository access → **Only select repositories** → `OWNER/SLUG`, виставляє expiration і генерує токен.
3. **Branch protection лишається автоматичним** завдяки `Administration: write` у токені (рішення maintainer: один вузький admin-дозвіл **на конкретний репо** прийнятний; ключ на весь акаунт — ні). Якщо дозволу немає — `/bootstrap` падає в ручний UI-fallback, як і раніше.
4. **Fine-grained перестає бути блокером.** `FINE_GRAINED_PAT_NOT_SUPPORTED` прибрано з `/bootstrap` і `/doctor`. Оскільки fine-grained токени не віддають OAuth-скоупи через headers, перевірка `has_*_scope` для них **не застосовується**: capability підтверджується пробою репо (`gh repo view OWNER/SLUG`) і явними помилками конкретних операцій (push / branch-protection PUT) з підказками, а не скоуп-гейтом.

`scripts/detect-env.py` далі класифікує `pat_kind` (corisно для діагностики), але consumers більше не трактують `fine-grained` як hard-блокер.

## Наслідки

**Плюси.** Мінімальний доступ: один токен бачить рівно один репозиторій з рівно потрібними дозволами; компрометація не відкриває весь акаунт. Відповідає рекомендації самого GitHub (fine-grained > classic). Лінк створення токена згенерований під проект — менше ручного клікання й помилок із дозволами.

**Мінуси.** Втрачено повну «одну-командну» автоматизацію: користувач робить два ручні кроки (створити репо + згенерувати токен і довибрати репо в UI). Вибір конкретного репозиторію в токені не можна пре-заповнити URL-ом (обмеження GitHub) — лишається ручним. Capability вже не верифікується наперед скоуп-гейтом, тож деякі помилки прав випливають під час операції (push/protection), а не на preflight; пом'якшено явними remediation-повідомленнями і пробою `gh repo view`.

**Відкинуті альтернативи.** Залишити classic-PAT + auto-create як default — відхилено: широкий «ключ на весь акаунт» суперечить меті. Прибрати branch protection заради токена без admin — відхилено: protection потрібна для PR-only гарантій, а вузький per-repo `administration` дозвіл прийнятний. Тримати fine-grained заблокованим — відхилено: це і є кореневий біль.

## Наслідки для файлів

- `scripts/detect-env.py` — `pat_kind` лишається; docstring оновлено (fine-grained не блокер).
- `.claude/commands/bootstrap.md` — mode detection (репо вже існує), preflight без `FINE_GRAINED_PAT_NOT_SUPPORTED` і без scope-гейту, нова GitHub-access секція з template-URL, prompt на repo URL, Mode A Step 1 лінкує існуючий репо, branch-protection 403 → додати `administration=write`.
- `.claude/commands/doctor.md` — PAT-аудит приймає fine-grained; `FINE_GRAINED_PAT_NOT_SUPPORTED` прибрано з hard-STOP.
- `.claude/rules/environment.md` — Scope 2 PAT-рядки під fine-grained per-repo.
- `README.md` — секція доступу, Quick start (створити+клонувати репо), Troubleshooting.
