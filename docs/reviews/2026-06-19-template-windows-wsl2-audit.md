# Аудит шаблону claude-django — Windows/WSL2 та цілісність конфігу

- **Дата:** 2026-06-19
- **Тип:** аудит шаблону (template meta), не feature-PR
- **Тригер:** «шаблон вимагає WSL2 — чи можуть агенти Claude працювати напряму на Windows?»
- **Метод:** web-search (офіційні докси Claude Code + GitHub issues) + статичний аналіз `scripts/`, `.claude/`, `docs/`

## 1. Чи працюють агенти Claude напряму на Windows?

Треба розділити два рівні.

**Раннер Claude Code — так.** Офіційні докси (`code.claude.com/docs/en/setup`) перелічують Windows 10+ з «WSL, WSL 2, **or** Git for Windows»; є нативний PowerShell-tool. Тобто факт, на якому неявно стоїть ADR 0005 («PowerShell-native — не реальний раннер»), частково застарів: сам раннер тепер працює на Windows без WSL2.

**Toolchain цього шаблону — ні (на практиці).** Шаблон збудований навколо bash: SessionStart-хук `bash scripts/session-start.sh`, три policy-хуки на bash, `.sh` gate-скрипти, Docker bind-mounts. А bash-form хуки на нативному Windows мають задокументовані невирішені баги — резолвляться у WSL-стаб `C:\Windows\System32\bash.exe` і зависають (#37634) або тихо падають на backslash-шляхах (#18610, #24097). Плюс шаблон самоблокується: `detect-env.py` ставить `platform_supported=false` на Windows-native.

**Вердикт:** вимога WSL2 для шаблону як він є — досі чесна. Раннер може, toolchain — ні.

## 2. Git Bash як шлях для нативного Windows

Оцінка по компонентах:

- **`.sh` gate-скрипти** (`check_stubs.sh`, `check_app_readmes.sh`, `check_file_size.sh`, `check_nul_bytes.sh`, `check_contract_conformance.sh`, `pull_contract.sh`): сумісні з Git Bash — використовують bash + GNU coreutils (`grep -E`, `find`, `mapfile`, `mktemp`, `diff`), що постачаються з Git for Windows. CI це не стосується (там Linux-раннер).
- **`setup-wsl.sh` / `install.sh`:** НЕ сумісні — `uname`, `/proc/version`, `apt-get`, `nvm`, `~/.bashrc`. Це Linux/WSL2-only онбординг.
- **Hard-блокер №1 — `detect-env.py`.** Гейт (`scripts/detect-env.py:211-213`): `platform_supported = platform.system() in ("Linux","Darwin") or is_wsl2()`. Під Windows+Git Bash `platform.system()=="Windows"`, а `is_wsl2()` читає `/proc/version` і не бачить там `microsoft/wsl` → `platform_supported=False`. Додатково `wrong_runner_suspected` (`:219-220`) = True, бо `wsl` зазвичай у PATH. Отже `/doctor` робить HARD STOP `UNSUPPORTED_PLATFORM` навіть під Git Bash.
- **Hard-блокер №2 — bash-хуки.** SessionStart `bash scripts/session-start.sh` + 3 policy-хуки (`.claude/settings.json`). На нативному Windows Claude Code може резолвити `bash` у WSL-стаб і зависнути (#37634) або тихо впасти (#18610). Це **емпіричний ризик**, який треба перевіряти на реальній машині.
- **Docker.** Без WSL2-бекенду потрібен Hyper-V бекенд Docker Desktop; bind-mount шляхи Windows-style, повільніші. ADR 0009 уже допускає `/mnt`.

**Що треба, щоб уможливити Windows+Git Bash (мінімум):** (1) змінити `detect-env.py` — трактувати Windows із доступним bash як підтримуваний і зняти `wrong_runner_suspected` для цього кейсу; (2) ЕМПІРИЧНО перевірити, що SessionStart/policy-хуки реально стартують під Git Bash, а не зависають на WSL-стабі; (3) задокументувати Docker без WSL2-бекенду. Пункт (2) — головний невідомий ризик.

**Вердикт:** технічно більшість `.sh`-скриптів Git-Bash-сумісні, але два hard-блокери (гейт `detect-env.py` і крихкість bash-хуків) означають, що це НЕ «просто ввімкнути». WSL2 лишається єдиним перевіреним раннером; розумний перший крок до Windows — PoC саме хуків під Git Bash, а не перехід на PowerShell.

## 3. Hard-блокери Windows-native (мапа)

| # | Місце | Що блокує |
|---|---|---|
| 1 | `scripts/detect-env.py:211-220` | `platform_supported=false` + `wrong_runner_suspected` → `/doctor` STOP |
| 2 | `.claude/settings.json` (SessionStart) | `bash scripts/session-start.sh` — потребує bash; ризик WSL-стабу/зависання |
| 3 | `.claude/settings.json` (policy-хуки) | `block_protected_edits.sh`, `check_command_gate.sh`, `check_plan_execution_log.sh` на bash |
| 4 | `scripts/setup-wsl.sh`, `scripts/install.sh` | падають на `uname`/`apt`/`/proc/version` |

## 4. Цілісність wiring та ADR

Загалом — здоровий стан. 16 `@`-import правил присутні; 5 правил другого рівня (`architecture`, `serializers-permissions`, `migrations-tasks`, `testing`, `mcp-stack`) заведені в агентів; **orphan-правил немає**. 23 агенти, 20 команд, усі `templates/` на місці. ADR 0001–0021 — усі Accepted, без виявлених суперечностей.

**Нотатка про `check_openapi_drift.sh`.** Перший прохід позначив згадки скрипта як «застарілі». Перевірка точних рядків показала: більшість — КОРЕКТНИЙ історичний запис, не баг:

- `docs/plans/0011-contract-inversion.md` — це сам план, що ВИДАЛИВ скрипт; його лог правильно фіксує видалення (рядок 74: «check_openapi_drift.sh відсутній», «План ЗАКРИТО»). Не чіпати.
- `docs/plans/0001-doctor-bootstrap-refactor.md:26,186` — закритий план; згадки були коректні на момент написання. Переписувати історію закритого плану суперечить append-only/Surgical-духу.
- `docs/decisions/0005-drop-windows-native-shell.md:20` — ЄДИНЕ місце, де скрипт поданий як поточний факт (у Context ADR). Виправлення — не правка тіла рішення, а дописана датована Update note.

Єдина внесена правка по цьому пункту: Update note у ADR 0005 (цей самий PR).

## 5. Рекомендації

1. **(зроблено)** ADR 0005 — Update note: нативний Windows тепер реальний раннер; `check_openapi_drift.sh` прибрано за ADR 0017.
2. **(за бажанням)** Якщо колись треба нативний Windows — почати з PoC хуків під Git Bash (блокер №2), а не з PowerShell.
3. **(дрібниця)** CLAUDE.md рядок 48 — додати `@`-префікс до імен правил другого рівня для візуальної консистентності.
4. **(дрібниця)** Інвентаризувати `.claude/skills/` у CLAUDE.md або явно позначити як зовнішні.

## Джерела

- Claude Code setup — https://code.claude.com/docs/en/setup
- Claude Code hooks — https://code.claude.com/docs/en/hooks-guide
- anthropics/claude-code#37634 — bash hooks resolve to WSL stub on Windows
- anthropics/claude-code#18610 — plugin hook path resolution on Windows
- anthropics/claude-code#24097 — shell hooks do not execute (Windows desktop app)

<!-- Аудит згенеровано 2026-06-19 -->

## Update — 2026-06-19 (рішення: реалізувати нативний Windows)

Після цього аудиту вирішено зробити шаблон робочим без WSL. Жорстку вимогу WSL2 знято: хуки портовано на кросплатформний Python, а `detect-env.py` тепер дає `platform_supported: true` на Windows. Зафіксовано в ADR `0022` (amends ADR `0005`); виконання — `docs/plans/0014-native-windows-runner.md` (PR1 runtime + PR2 gates + PR3 rules/README + PR4 ADR, усе в робочому дереві). Вирішальна перевірка — що Claude Code на нативному Windows запускає `python scripts/session-start.py` без зависання — лишається per-machine кроком валідації (plan 0014, крок V).
