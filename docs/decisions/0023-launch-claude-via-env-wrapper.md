# 23. Запуск Claude Code через .env-wrapper (scripts/claude.{sh,ps1})

- **Status:** Accepted
- **Date:** 2026-06-21
- **Deciders:** Project maintainer
- **Tags:** environment, mcp, github, gh, secrets, developer-experience
- **Amends:** ADR 0011 (база плагінів/MCP); relates ADR 0008 (fine-grained PAT), ADR 0022 (native Windows runner)

## Контекст

MCP-сервери (github/context7 — через офіційні плагіни за ADR 0011 або через `.mcp.json` fallback) і `gh` CLI читають креди з **оточення процесу, що запустив `claude`**: `${VAR}` у `.mcp.json` та плагіни резолвляться саме з нього. Claude Code **НЕ** авто-завантажує проєктний `.env`.

Раніше єдиний задокументований шлях наповнити це оточення — `export` змінних у `~/.bashrc` / `~/.bash_profile`. У нього три вади:

1. **Глобальне протікання й змішування між проєктами.** Один токен експортується на всі shell-сесії, секрет лежить у dotfile далеко від репо, і паралельні проєкти мимоволі ділять ті самі креди.
2. **Застарілий `GITHUB_TOKEN` мовчки затіняє.** `gh` бере токен у порядку `GH_TOKEN` → `GITHUB_TOKEN`, а `GITHUB_PERSONAL_ACCESS_TOKEN` не читає взагалі. Тож стале (часто **системне** на Windows) `GITHUB_TOKEN` тихо виграє над правильним PAT і дає `gh` 401 — діагностувати важко, бо у `.bashrc` усе ніби «виставлено».
3. **Ручне налаштування на кожній машині.** `/doctor` ловить відсутність токена лише постфактум; сам сетап лишається ручним кроком, який легко забути на новій машині.

## Рішення

**Запускати `claude` через тонкий wrapper, який сорсить проєктний `.env`**, а не через `export` у shell rc:

1. `scripts/claude.sh` (bash / Git Bash / WSL2) і `scripts/claude.ps1` (native PowerShell) сорсять `$ROOT/.env`, експортують усі змінні в процес `claude` і **ніколи не друкують секрети**. Так `CONTRACT_REPO`, `CONTRACT_VERSION`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `CONTEXT7_API_KEY` потрапляють у MCP-сервери, `gh` і тулінг **без** жодного запису в shell rc чи user-environment.
2. **PAT з `.env` авторитетний для `gh`.** Wrapper копіює `GITHUB_PERSONAL_ACCESS_TOKEN` → `GH_TOKEN` (перекриваючи будь-який успадкований, часто стале системне `GH_TOKEN`) і робить `unset GITHUB_TOKEN` — прибирає застарілий токен, що раніше спричиняв `gh` 401. Якщо PAT у `.env` порожній, креди `gh` з оточення лишаються недоторканими (можна й далі користуватися `gh auth login` keyring).
3. **Порожній placeholder у `.env` не затирає значення з shell.** Wrapper робить snapshot credential/contract-змінних до сорсингу і відновлює їх, якщо `.env` лишив поле порожнім — тож «.env виграє, коли заповнений; інакше — те, що вже було в оточенні».
4. **Ергономіка.** Кореневий `Makefile` (+ `templates/Makefile`) дає алиас `make cc`, а кореневий `.env.example` несе повний набір змінних; `.env` лишається gitignored.

## Наслідки

- (+) Рекомендований запуск — `bash scripts/claude.sh` / `make cc` (native PowerShell: `pwsh scripts/claude.ps1`), не голий `claude`. Токени живуть у `.env`, не в shell rc.
- (+) **Ізоляція токенів per-project**: кожен проєкт сорсить власний `.env` у власний процес `claude`, паралельні проєкти не ділять кред.
- (+) Ремедіація сталого `GITHUB_TOKEN` тепер **автоматична** для процесу `claude`, запущеного через wrapper (раніше — ручне чищення `.bashrc`, яке `/doctor` лише пропонував).
- (+) Перевірки `/doctor` (`[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]`, `gh auth status`) працюють як раніше: при запуску через wrapper оточення вже наповнене з `.env`.
- (+) Scaffolded-проєкти успадковують wrapper + `make cc` із `templates/`, тож флоу однаковий на похідних проєктах.
- (−) Голий `claude` поза wrapper не отримає змінних із `.env` — користувач має пам'ятати про `scripts/claude.sh` / `make cc` (документовано в README, Scope 2 environment, `/doctor`, `/bootstrap`).
- Зачіпає: `scripts/claude.sh`, `scripts/claude.ps1`, кореневий `Makefile` + `templates/Makefile` (`cc`), кореневий `.env.example`; уточнює доктрину токенів ADR 0008/0011; узгоджено з native-Windows runner ADR 0022.

<!-- Last reviewed/updated: 2026-06-21 -->
