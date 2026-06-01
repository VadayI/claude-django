# WORKLOG — claude-django

## 2026-06-01 — Config baseline з реального сетапу maintainer'а (ADR 0011)

Maintainer надав свій перевірений сетап (глобальні + проектні налаштування, плагіни, hooks, дозволи) як основу рекомендацій. Оновлено committed-базу плагінів і механізм MCP. Рішення зафіксовані опитуванням.

**enabledPlugins (нова committed-база).** Додано `playwright`, `github`, `context7` (з `claude-plugins-official`) до `superpowers` + `engineering`. `playwright` зв'язано з агентом `qa` (browser-інструменти). `code-review` і `code-simplifier` спершу розглянуто, але **виключено** після аудиту перетинів (нижче).

**Аудит перетинів MCP/плагіни/команди/агенти (Варіант A).** Перевірено, чи поверхні не дублюють роботу. Висновок: команда->агент — навмисне шарування; github/context7 не реєструються двічі (прибрано `enabledMcpjsonServers`). Реальне дублювання дали проєктно-агностичні плагіни: `code-review` (скіли `/review`, `/security-review`) конкурує з `reviewer`/`security-scanner` + `/review-pr`/`/security-check`; `code-simplifier` конкурує з `/simplify` + `django-refactoring-expert`. Обидва **прибрано з бази** — проєктні агенти знають правила (TDD, no-stubs, api-docs, app-readme, verification, IDOR/OWASP). `playwright` лишено (це шарування, не дублювання). Канонічні шляхи: `/review-pr`, `/security-check`, `/simplify`.

**github + context7 -> офіційні плагіни.** Прибрано `enabledMcpjsonServers` із `.claude/settings.json`. `.mcp.json` лишено як опційний committed-fallback (`_note` + `mcp-stack.md`). Імена інструментів ідентичні — `mcp-stack.md` чинний.

**Нюанс із токенами (важливо).** `GITHUB_PERSONAL_ACCESS_TOKEN` потрібен незалежно від механізму — його використовує `gh` CLI (push/PR/branch-protection), плагін міняє лише транспорт MCP. `CONTEXT7_API_KEY` потрібен плагіну context7. Перевірки env-ключів лишено.

**Не в базі.** `claude-hud` — рекомендований, але персональний/глобальний (HUD UI). `frontend-design` (окремий frontend-репо, ADR 0007) і `mongodb` (проект на PostgreSQL) — не входять у backend-only базу.

**Файли.** `.claude/settings.json`, `.claude/rules/environment.md` (Scope 2), `.claude/rules/mcp-stack.md`, `.mcp.json`, `.claude/commands/bootstrap.md` (Step 6), `.claude/commands/plugins.md`, `.claude/commands/config.md`, `.claude/agents/qa.md`, `README.md`, ADR 0011.

## 2026-06-01 — Verification handoff + /verify, /config, /plugins (ADR 0010)

Додано контракт-деривований артефакт ручної перевірки ендпоінтів і пам'ять маршрутів. Драйвер — maintainer хоче «відкрий URL / встав curl / очікуй статус» чеклист на додачу до зелених pytest.

**Ask #1 (git-токен) — перевірено, вже реалізовано.** `/bootstrap` і `/doctor` уже не створюють репо й видають URL fine-grained per-repo токена (ADR 0008). «admin key» — це лише `administration=write` на один репо (опційне).

**Правило `verification.md` (Варіант 1 — авто-блок).** `docs-writer` у фазі 6 генерує `docs/verify/<feature>.md` (Swagger + `curl` з тілами й кодами 401/403/400/404/409) із `.claude/memory/endpoints.json` + `docs/api/openapi.yml`. Прив'язано до `api-architect`/`docs-writer`/`reviewer`/`tester`.

**Пам'ять маршрутів `endpoints.json` (ask #3).** Реєстр `{method, path, app, feature, auth, statuses[], notes}`; `api-architect` пише на фазі 2. Тристороння звірка `endpoints.json <-> openapi.yml <-> INDEX.md` (схема — джерело правди), як у `app-readme.md`.

**Команда `/verify [feature] [--run]` (обидва режими).** Дефолт — регенерує файл; `--run` — ганяє curl проти dev-сервера, pass/fail, ніколи не проти staging/prod.

**`/config` і `/plugins` (тонкі обгортки над /doctor `claude`-scope).** `/plugins` друкує paste-ready блок встановлення плагінів.

**Шаблони + bootstrap.** `templates/endpoints.json`, `templates/verify_TEMPLATE.md`; `/bootstrap` Step 2 копіює seed + `mkdir docs/verify`, Mode B probe №9.

**Дотичні правки.** `CLAUDE.md`, `workflow.md` (фази 2/6), `api-architect.md`, `docs-writer.md`, `bootstrap.md`, `README.md` (Rules 15->16, Commands 14->17, Templates, таблиця команд).

## 2026-06-01 — GitHub access model (ADR 0008) + /mnt working-dir policy (ADR 0009)

Two related policy reversals driven by the `carlsberg-ir-data-service` bring-up.

**Access model — manual repo + fine-grained per-repo PAT (ADR 0008; shipped in `a9185b3`).** Replaced the classic-PAT / auto-`gh repo create` model with: the user creates the empty repo by hand, and `/bootstrap` + `/doctor` emit a per-repo **fine-grained token template URL**. Verified live (GitHub changelog 2025-08-26) that fine-grained PAT template URLs are supported — `name`/`description`/permissions prefill via query params (`contents`/`pull_requests`/`workflows`/`administration`); the specific-repo selection stays a manual UI toggle. `FINE_GRAINED_PAT_NOT_SUPPORTED` retired across `bootstrap.md`/`doctor.md`/`environment.md`/`detect-env.py`; fine-grained is now the recommended credential, capability verified by `gh repo view` + per-operation errors instead of OAuth-scope headers. Mode A links `origin` to the user-created repo (`REPO_NOT_FOUND` remediation) instead of creating it; branch protection uses `administration=write` in the token.

**Working dir — `/mnt` fully supported (ADR 0009; pending commit).** Stopped recommending that users move the project off `/mnt/c`/`/mnt/d` into `~/projects`. `/doctor` now reports `/mnt` as ✅ and never proposes moving; one neutral caveats note remains (slower bind-mounts, CRLF, run git from the host shell to avoid `index.lock`). Removed all "Do NOT work from /mnt" language from `environment.md`, `doctor.md`, `docker-commands.md`, README. `~/projects` is optional, not required.

**Branch protection on the free plan (pending commit).** Verified via GitHub Docs that branch protection AND rulesets are unavailable for **private** repos on the free plan (public repos get them free; private needs Pro/Team/Enterprise). `bootstrap.md` Step 5 403 handler now distinguishes (a) plan limit (free + private) from (b) missing token `Administration` permission, and makes "skip & keep private" a documented choice. `doctor.md` no longer flags absent protection on a free private repo as `existing-incomplete`; `environment.md` Scope 4 records the limitation.

**Verification.** `detect-env.py` compiles; `FINE_GRAINED` as an active gate = 0 (only "retired" mentions remain); no residual "Do NOT work from /mnt" / move recommendations; template URL consistent across files; all writes via `python pathlib` + `assert` anchors + tail/line checks (Edit/Write mount-truncation guard). `a9185b3` pushed; the ADR 0009 + branch-protection batch + this WORKLOG/HANDOFF update is the pending commit.

## 2026-06-01 — Onboarding clarity + mandatory Node gate + npm-shadow trap

Session driven by a live bring-up on `carlsberg-ir-data-service`: the maintainer kept hitting `UNSUPPORTED_PLATFORM` / `wrong_runner_suspected`, and the documented wrong-runner PATH fix did not take. Root cause uncovered live: a Linux `node` (`/usr/bin/node`, v22) was present but Linux `npm` was **missing**, so `npm` resolved through PATH interop to the Windows npm (`/mnt/c/Program Files/nodejs/npm`), `npm config get prefix` returned a `C:\...` path, and `npm install -g @anthropic-ai/claude-code` therefore installed `claude` into the **Windows** prefix — so `which claude` stayed `/mnt/c/...` no matter how the `$(npm config get prefix)/bin` trick was applied. Documented the whole failure chain and turned Node into a real gate.

**Docs clarity (README).** New prominent startup happy-path in the launch step (`which claude` must be a `/home` path, not `/mnt/c`, before launching; a backslash banner = `claude.exe`), a "type fixes in the bash shell, not the `❯` prompt" note, a `which claude` check inside the Quick-start clone snippet, and a new **"Troubleshooting startup & /doctor hard-stops"** section: a symptom/code → cause → fix table covering `UNSUPPORTED_PLATFORM` (wrong-runner vs genuine Windows), `NO_ENV_DETECT`, `NO_PYTHON_OR_HOOK`, `FINE_GRAINED_PAT_NOT_SUPPORTED`, `NO_GH_SCOPES`, REPL-vs-shell, `wsl2`-vs-`wsl`, slow `/mnt` mounts, and the npm-shadow case.

**Mandatory Node gate.** `scripts/detect-env.py` now derives `node_supported` (node on PATH AND major >= 18), schema bumped v4->v5, with a defensive parser (missing node -> false; present-but-unparseable -> true so a quirk never falsely blocks) and a `NO_NODE` stderr hint. `.claude/commands/doctor.md` gained a **Node audit** bullet (reports `NO_NODE`, blocks `/bootstrap`) and added `NO_NODE` to the hard-STOP flag list. `.claude/rules/environment.md` Scope 1: Node.js promoted from optional to **HARD REQUIREMENT (18+)** with rationale, plus a new **Claude Code CLI (WSL2-native)** row. README Prerequisites updated to match; the Context7 Node note de-conflicted.

**npm-shadow trap.** Added the "Linux node present but Linux npm missing -> Windows npm installs claude to the Windows prefix" sub-case to `.claude/rules/environment.md` (with the `nvm install --lts` fix + `setup-wsl.sh` pointer), a dedicated row in the README Troubleshooting table, and a sentence in the `doctor.md` `wrong_runner_suspected` remedy.

**Verification.** `detect-env.py` AST-compiles; `_node_supported()` unit-checked across v14/v16 (false) and v18/v20/v22/`V18`/garbage/empty (true) plus node-absent (false) — all pass. Every `.claude/**`, README, and `scripts/` write applied via `python pathlib` with `assert count==1` anchors + tail/line-count verification, because the Edit/Write MCP tools truncated README and detect-env.py mid-session again (rebuilt from `git show HEAD:<path>` + re-apply). Commit + push to `main` performed by the maintainer from the host shell.


## 2026-06-01 — Secrets deny hardening + lesson_youtube_2 audit

Звірка шаблону з особистим конспектом `LOCAL/lesson_youtube_2.txt`. Проект відповідає майже всім практикам конспекту; знайдено один предметний пробіл — покриття секретів.

**Зміна.** Розширено `permissions.deny` у `.claude/settings.json`: додано блокування читання вкладених `.env` (`**/.env`, `**/.env.*`), приватних ключів/сховищ (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.kdbx`), SSH-ключів (`id_rsa`, `id_ed25519`), `credentials*`, теки `secrets/**` і локальних дампів `*.sqlite3`. Раніше deny покривав лише кореневі `.env`/`.env.*` і `settings.local.json`. Уточнення: `.claudeignore` у Claude Code не існує як фіча — правильний механізм це `permissions.deny`, тому файл не створювався. `_last_reviewed` оновлено на 2026-06-01.

**Документ.** `docs/reviews/lesson-youtube-2-audit.md` — повна таблиця відповідності, закритий пробіл, свідомі розбіжності (Playwright MCP / output-language / QA-модель), відкрите питання про React+MUI (monorepo vs окремий стек-шаблон) як кандидат на ADR.

**Verification:** `settings.json` ревалідовано як JSON (17 deny-записів); зміни в `.claude/**` застосовано через python pathlib з anchor-assert (Cowork mount-truncation guard з `docs/lessons.md`). Push + PR — за межами пісочниці (gh/PAT недоступні), виконує maintainer зі свого терміналу.


## 2026-06-01 — Cross-platform onboarding automation (4 batches; ADR 0006)

Follow-up to the Desktop-not-a-runner work. The maintainer asked whether claude-django could "work on both Windows and Debian with more automation". Framing: it already runs on both (Debian native, Windows via WSL2) — the lever is WSL2 *onboarding friction*, not portability. ADR 0005 (WSL2-only, no PowerShell) is explicitly **kept**; PowerShell was NOT reintroduced. Decision recorded in `docs/decisions/0006-cross-platform-onboarding-automation.md`. Shipped in four commits:

**Batch 1 — the wrong-runner trap.** `scripts/detect-env.py` now emits `wrong_runner_suspected` (schema v3->v4): `true` when `platform == "windows"` AND `wsl` is present — i.e. the user launched the Windows `claude` from a WSL2 shell (PATH interop -> `claude.exe` -> Windows-Python -> `platform: windows`). It also prints a targeted stderr hint. `.claude/commands/doctor.md` (Step 0.5 + Platform audit) branches the `UNSUPPORTED_PLATFORM` remedy on the flag: `true` -> install/launch the WSL2-native `claude`; `false` -> install WSL2. Documented in `.claude/rules/environment.md` (new subsection + `~/.bashrc` PATH fix) and a second README "Symptom #2" callout. `platform_supported` logic is unchanged — the flag is advisory only.

**Batch 2 — one-shot setup.** New `scripts/setup-wsl.sh`: idempotent installer for `python-is-python3`, Node (via nvm), `@anthropic-ai/claude-code`, and `gh`, plus the `~/.bashrc` PATH export so the WSL2 npm-bin beats interop. Platform-guarded (Linux/WSL2 only; clear macOS/Windows messages). README gained a one-liner.

**Batch 3 — Makefile wrappers.** New `templates/Makefile` (scaffolded into derived projects like `docker-compose.yml`) with targets identical on Debian and WSL2: `up`/`dev`/`down`/`ps`/`logs`/`build`/`test`/`cov`/`lint`/`fmt`/`migrate`/`makemigrations`/`superuser`/`shell`/`schema`/`gates`/`doctor-deps`, plus `setup`. Wired into `bootstrap.md` Mode A scaffolding list, README Quick start copy block, and a `docker-commands.md` "Make wrappers" section.

**Batch 4 — SessionStart automation.** New `scripts/session-start.sh` wrapper: mandatory `detect-env.py` first (writes `env-detect.json` — the gates depend on it), then a safe `.env` seed from `.env.example` when missing, then `docker compose up -d` **only** when `CLAUDE_DJANGO_AUTO_UP=1` (off by default per detect->propose->fix-on-confirm). `.claude/settings.json` SessionStart now calls the wrapper; `CLAUDE.md` and `docker-commands.md` updated.

**Verification:** `detect-env.py` py_compiled and exercised in both branches (Linux -> `false`; mocked Windows+wsl -> `true` + warning). `setup-wsl.sh`/`session-start.sh` pass `bash -n`; the SessionStart wrapper was run in a temp repo mock (env-detect written, `.env` seeded once/idempotent, AUTO_UP off by default skips compose). `Makefile` parsed via `make help` + `make -n` for `test`/`dev`/`gates`; `doctor-deps` run for real. `settings.json` re-validated as JSON. All edits to `.claude/**` files applied via python pathlib with `assert count==1` anchors (Cowork mount-truncation guard from `docs/lessons.md`); every touched file re-checked for 0 NUL bytes. Note: shellcheck unavailable in the authoring sandbox — `setup-wsl.sh` should get one real `shellcheck` + end-to-end run on a clean WSL2 machine before being relied on.

## 2026-05-31 — README: Desktop-not-a-runner warning + "Using Claude Code CLI" section

Triggered by a real `/doctor` run from Claude Desktop (Code mode) on the test project `carlsberg-ir-data-service`: it correctly issued `HARD STOP: UNSUPPORTED_PLATFORM` because the desktop app runs the SessionStart hook with Windows-Python (`is_wsl2: false`, `platform_supported: false`) even though the files were copied from inside a WSL2 shell. Not a `/doctor` bug — the config was simply run from an unsupported runner.

**Changes (README.md only, no behavior change):**

- Strengthened the "Where this runs" Desktop bullet — now "Claude Desktop — including Cowork / Code mode" and spells out the three reasons it can't run the methodology: `.claude/agents/` pipeline not loaded, no access to your Docker/PostgreSQL for the TDD loop + CI gates, and the env gates can't fire honestly.
- Added a ⚠️ symptom callout describing the exact Windows-Python → `UNSUPPORTED_PLATFORM` chain and clarifying the fix is "launch the terminal `claude` from inside WSL2", not "install WSL2 again".
- Added a "Can I use Claude Desktop at all?" mini-FAQ (partly — as a companion, not the runner).
- Added a new top-level section "Using Claude Code CLI (the only supported runner)": install CLI inside WSL2, keep the project in `~/projects` (not `/mnt/...`), launch from project root, the `/doctor` → `/preflight` → feature → `/wrap-up` cycle, and the classic-vs-fine-grained PAT note as the next gate.

**Verification:** entry written via python pathlib (mount-truncation guard); README re-checked — 0 NUL bytes, 7 `##` headings (no dups), tail intact.


## 2026-05-31 — Fix root cause of NO_ENV_DETECT: Quick start never copied root `scripts/`

Follow-up to the earlier NO_ENV_DETECT hardening batch. That batch made `/doctor`/`/bootstrap`/`/preflight` STOP cleanly when `env-detect.json` is absent, but it never fixed *why* the file was absent on a correctly-followed setup. Real cause found on a fresh `carlsberg-ir-data-service` clone: the README Quick start `cp` block copies `.claude/`, `CLAUDE.md`, `.mcp.json`, `.gitignore`, `.gitattributes`, `templates/`, `docker-compose.yml`, `.github/workflows/` — but **never the root `scripts/` directory**. The `SessionStart` hook runs `python scripts/detect-env.py`; with `scripts/detect-env.py` missing the hook fails silently, `env-detect.json` is never written, and `/doctor` fires `NO_ENV_DETECT` with a misleading diagnosis (blamed Python/runtime, never the missing file). `detect-env.py` + `log-cmd.py` live in root `scripts/`, separate from `templates/scripts/` (which holds only the three CI `check_*.sh` gates), so a full `templates/` copy does not bring them along.

**Fixes:**

- `README.md` — Quick start clone block now copies `scripts/` (`cp -r /tmp/claude-django/scripts ./`) with an inline note that the SessionStart hook fails silently without it; the NEW-project prose list adds `scripts/`.
- `.claude/commands/doctor.md` — Step 0.5 `NO_ENV_DETECT` now lists **three** causes, with "scripts/detect-env.py missing (root scripts/ not copied)" as cause #1 + the `cp -r /tmp/claude-django/scripts ./` fix; gate now checks `test -f scripts/detect-env.py` first and only suggests running the diagnostic when the file exists.

**Verification:** both edits applied via `assert count==1` anchor matching through python pathlib (Windows-mount truncation guard from `docs/lessons.md`); file tails confirmed intact after write.


## 2026-05-31 — Remove Russian everywhere + retire stale mini-frontend/React references

Two cleanups after the command-hardening batch.

**Language — Russian removed everywhere (owner mandate "no Russian anywhere").** Canonical option set is now **English / Українська / Polski** (+ harness "Other"), aligned across `.claude/commands/doctor.md`, `.claude/commands/bootstrap.md`, `.claude/commands/set-language.md` and `CLAUDE.md`. Also dropped the stray `Німецька`/`de` that existed only in `set-language.md` (Deutsch is still reachable via "Other"), and scrubbed the Russian mention in the historical plan `docs/plans/0001-*.md`. Zero `русский|russian|німецьк` matches remain in the repo.

**Backend-only — stale in-repo frontend debt retired.** The repo has been backend-only since the mini-frontend was replaced by Swagger UI (`api-docs.md`), but leftover references implied an in-repo Vite+React mini-client. Reframed to "separate production-frontend repo / staging" (never deleted `qa`/`playwright-e2e`, which `workflow.md`/`tdd.md` keep as an optional top layer):
- agents: `qa.md` (scope + `cd frontend` commands -> staging / separate repo), `reviewer.md` ("thin frontend" -> "separation of concerns"), `tester.md` (`frontend` agent -> `qa`), `ci-cd-engineer.md` ("backend/frontend jobs" -> "independent jobs").
- commands: `fix-ci.md` (dropped the frontend-build failure category + `cd frontend && npm run build`).
- rules: `docker-commands.md` (removed the whole "Frontend (mini-client)" npm/Vite section), `workflow.md` (dropped "React component in the mini-client" pipeline trigger), `preflight.md` (stack no longer lists "Vite+React"; "Django/DRF/React" -> "Django/DRF"), `mcp-stack.md` ("React/Vite" docs -> "PostgreSQL"), `git-operations.md` (dropped "Backend and frontend — separate PRs").
- skills: `code-reviewer` (removed React mini-client checklist; desc backend-only), `github-actions-django` (desc/title drop Vite+React), `playwright-e2e` (reframed to separate repo / staging), `security-reviewer` (CORS line).

Intentionally kept: `api-docs.md` / `architecture.md` statements that explicitly say there is NO in-repo mini-frontend (Swagger UI replaced it; frontend lives in a separate repo) — these are the correct policy, not debt.

**Audit note:** false positives from the sweep were rejected — handoff.md `json.load` is guarded; `security-check.md` 🔴🟡🟢 markers are the repo-wide severity convention (the "no emojis" rule is GitHub-PR-comment-only); `brief-synthesizer` ТЗ/техзавдання triggers are intentional Ukrainian triggers.

**Verification:** every edit applied via `assert count==1` anchor matching; post-grep confirms 0 Russian/German matches and that all remaining frontend mentions are the legitimate "separate repo / Swagger UI" ones.


## 2026-05-31 — Harden `/doctor` + `/bootstrap` + `/preflight` against the non-CLI runtime (NO_ENV_DETECT)

Real-run audit: a `/doctor` invocation on the `carlsberg-ir-data-service` test project (run without a `SessionStart` hook, so `env-detect.json` was absent) produced a partly-fabricated report — it downgraded the missing WSL2 to ⚠️ instead of a hard stop, invented a `docker compose v5.1.3` version that does not exist, and recommended `/bootstrap` despite a fine-grained PAT and no WSL2. Root cause: `env-detect.json` is the source of truth, but the SessionStart hook only writes it in Claude Code CLI; with the file missing, `/doctor` fell back to ad-hoc detection and never fired its platform gate.

**Fixes (commands only — `scripts/detect-env.py` unchanged):**

- `/doctor` — new **Step 0.5 runtime gate** before the audit: if `env-detect.json` is missing -> `NO_ENV_DETECT` hard stop (do not dispatch `devops`, do not guess versions, do not recommend `/bootstrap`); if present but `platform_supported == false` -> `UNSUPPORTED_PLATFORM` hard stop. Step 1 audit now forbids fabricating tool versions (read only from `env-detect.json`; otherwise `unknown`). Step 5 recommendation is gated behind active hard-STOP flags so `/bootstrap` is never suggested while one is live.
- `/bootstrap` — mode-detection and preflight Python probes no longer traceback on a missing `env-detect.json`; they print `NO_ENV_DETECT` and exit cleanly. Added a `NO_ENV_DETECT` per-flag remediation entry (CLI-vs-Cowork causes; warns that running `detect-env.py` inside the Cowork sandbox reports the sandbox OS, not the user's machine).
- `/preflight` — new **Step 0 runtime gate** (mirrors `/doctor`): `NO_ENV_DETECT` / `UNSUPPORTED_PLATFORM` hard-stop before any `devops`/`ba` access check; anti-fabrication in Step 1; Step 5 never reports "preflight green" / hands to the pipeline while a hard-STOP flag is active.
- `README.md` — added a **Context7 setup (`CONTEXT7_API_KEY`)** subsection (what it is, where to get the key, `~/.bashrc` export, verify, Node.js requirement).

**Verification:** marker grep passes in both command files; the guarded mode-detection probe prints `NO_ENV_DETECT` (exit 0) with the file absent. Note: `env-detect.json` is absent in the Cowork sandbox too, confirming this config is CLI-only as documented.

**Note on git:** edited on the Windows D: mount from Cowork — commit on the host per `docs/HANDOFF.md` policy (container git fails on the Windows-written index).



## 2026-05-31 — PII / sensitive-data scrub of the public template (working tree)

The repo is public; swept it for personal data, names, and IPs before it spreads further through the scaffolding templates. Working-tree-only cleanup (no git-history rewrite, per owner decision).

**Findings:**

- **Staging VPS IP `54.37.138.231`** — 7 occurrences across `CLAUDE.md`, `.claude/agents/devops.md`, `.claude/rules/docker-commands.md`, `templates/PROJECT_README.md`. The template copy was the worst: it propagated the real IP into every derived project's README. Full deploy flow (SSH → git pull → docker compose) was documented next to it.
- **Personal author identity `Vadym (@VadayI)`** — in README, `docs/HANDOFF.md`, all 5 ADRs, `.claude/rules/no-stubs.md`, `.claude/commands/fix-ci.md`, and 4 `templates/` files.
- No tokens/keys/passwords in files (`.env.example` holds only placeholders). `a@b.com` in skills are test fixtures, not real.

**Fixes:**

- IP → `<STAGING_HOST>` placeholder everywhere (0 occurrences remain).
- Author attribution removed/genericised: ADRs → `Deciders: Project maintainer`; `no-stubs.md` + `templates/STUBS.md` → `@your-handle`; `fix-ci.md` → `your-org`; README `Author:` line dropped; `docs/HANDOFF.md` → `Maintainer`; derived-project clone example → `<your-username>`.
- **Intentionally kept:** 4 `VadayI` references that are functional clone URLs of *this* public repo itself (`README.md` self-clone, `templates/{lessons,PROJECT_README,WORKLOG}.md` source attribution). The repo owner of a public GitHub repo is visible regardless; genericising these would break `git clone` and lose source attribution.

**Out of scope (owner declined history rewrite):** personal email `vadym.melnyk@wp.pl` and the IP still live in older commits (`git log`) and the `origin` remote still shows `VadayI`. Since the IP was already public, treat it as exposed — verify the VPS hardening (SSH keys only, fail2ban, firewall) independently.

**Verification:** `grep -rn '54\.37\.138\.231'` → 0 hits; `grep -rn 'Vadym\|@VadayI'` → only the 4 functional self-URLs remain. No backend code in this repo, so no ruff/pytest gate applies.

---

## 2026-05-30 — read:org scope + env-var auth path clarification (hotfix)

Real-run on `carlsberg-ir-data-service`: after creating a classic PAT via our recommended URL and running `gh auth login`, the CLI rejected the token with `missing required scope 'read:org'`. Two gaps in the docs:

1. **Missing scope in the recommended PAT URL.** `gh auth login` validates `read:org` minimum (standard for the interactive flow), but our URL only listed `repo,workflow,admin:repo_hook,delete_repo`. `/bootstrap` operations themselves (`gh repo create`, branch protection PUT, PRs) don't need `read:org`, but anyone who follows the interactive auth path hits the wall.
2. **Two auth paths weren't documented as alternatives.** `gh` can use either an exported `GITHUB_PERSONAL_ACCESS_TOKEN` env var OR stored credentials from `gh auth login`. The env-var path skips the `read:org` requirement entirely. The previous docs hinted at both but didn't say "pick ONE" or note the scope difference.

**Fixes (single commit):**

- All four files that reference the PAT scope URL or `gh auth refresh` command: `repo,workflow,admin:repo_hook,delete_repo` → `repo,workflow,admin:repo_hook,delete_repo,read:org`. 10 occurrences across `bootstrap.md`, `doctor.md`, `environment.md`, `README.md`.
- `.claude/commands/bootstrap.md` — `FINE_GRAINED_PAT_NOT_SUPPORTED` block now shows the two auth paths side-by-side with a per-scope explanation comment block (so users understand which scope is for which operation). `NO_GH_AUTH` remediation rewritten the same way (A. env-var, B. stored creds), explicitly noting that `read:org` is required for B but not A.
- `.claude/commands/doctor.md` — PAT scope audit clarifies the same nuance and downgrades `read:org` to ℹ️ when env-var auth is detected.
- `.claude/rules/environment.md` — Scope 2 PAT scopes row notes that `read:org` is only needed for `gh auth login` (not for env-var auth).

**Plan:** none — this is a docs hotfix from a real-run gap.

**Verification:** `grep -c "delete_repo,read:org"` returns 5+2+2+1 = 10 across the four files; `bootstrap.md` size 30264 → 30264 + clarification block; doctor.md size grew by ~130 B; environment.md size grew by ~130 B.

---

## 2026-05-30 — /handoff command + repo conflict probe + auditor reads HANDOFF (P3)

Closed the P3 backlog from plans 0002-0004. Reframed the original "WSL gate Skill" (a misnamed non-issue — `environment.md` already conditions WSL2 checks on Windows-only) into a third concrete polish item: the `auditor` agent reads `docs/HANDOFF.md` so `/audit` surfaces stale "Next step" and open questions in its suggestions.

**Created:**

- `.claude/commands/handoff.md` — new `/handoff` command. Read-only on everything except `docs/HANDOFF.md`. Probes: `git branch`, `git status`, `git rev-list ahead/behind`, `gh pr list --json statusCheckRollup`, `gh pr list --state merged`, `docs/STUBS.md` count, `docs/todo.md ## Now`. Generates six sections (Current state / Last finished / In progress / Next step / Open questions / Environment notes) via a 7-rule decision ladder for "Next step". "Open questions" and "Environment notes" are carry-over (the command never deletes them). Supports `--note "..."` to append a free-text line to "Current state" and `--print` for preview without writing.

**Modified:**

- `.claude/commands/bootstrap.md` Step 1 — added Guard B: `gh repo view "$OWNER/$SLUG"` probe BEFORE `gh repo create`. If repo exists remotely but local has no `origin` → STOP with new flag `REPO_ALREADY_EXISTS` and two remedies (link local to existing repo and use Mode B, or pick different slug). Closes the gap that the carlsberg run exposed (user manually created the repo mid-bootstrap; a second `/bootstrap` would otherwise re-call `gh repo create` and fail with a buried GitHub error). `REPO_ALREADY_EXISTS` is documented in the per-flag remediation block.
- `.claude/agents/auditor.md` — added `docs/HANDOFF.md` to the read list (extracts "Next step" paragraph + open `## Open questions`). New Suggestion rule 1a: **if HANDOFF.md "Next step" is concrete (not a `{TODO}` placeholder) → use it verbatim as the primary suggestion**. Rationale: the previous session already decided what comes next; surface that decision before re-deriving one from probes. Open questions surface in the Secondary list when present (up to 3).

**bootstrap.md numbering:** `REPO_ALREADY_EXISTS` slots in next to `FINE_GRAINED_PAT_NOT_SUPPORTED` and `UNSUPPORTED_PLATFORM` in the preflight remediation table.

**README.md changes:**

- Commands count `13 → 14`; new entry for `/handoff [--note "..."] [--print]` in the Commands subsection right after `/wrap-up`.

**Plan:** `docs/plans/0005-handoff-command-and-repo-probe.md`.

**Future ideas (P4, not started):**

- `/handoff --append` mode that snapshots without overwriting (for keeping a history of session-end states).
- `/audit` automatically refreshing `docs/HANDOFF.md` before suggesting (call `/handoff --print` internally).
- A pre-bootstrap classic-PAT capability probe (`gh api /user --jq '.permissions'`) for the case where a classic PAT user is unexpectedly missing repo capabilities.

**Verification:** `.claude/commands/handoff.md` 6575 B, sections present (Log/Input/Probes/Generation/Write/Hard limits); `bootstrap.md` 28857 B with markers `REPO_ALREADY_EXISTS` (2), `Guard B` (1), `gh repo view` (1+); `auditor.md` 5324 B with markers `HANDOFF.md` (3+) and the new rule 1a present; README Commands count is 14 and `/handoff` line at row 123.

---

## 2026-05-30 — HANDOFF + branch protection fallback + lessons seed (P2)

Closed the P2 backlog from plans 0002 / 0003.

**Created in `templates/`:**

- `HANDOFF.md` — multi-session handoff seed (Current state / Last finished / In progress / Next step / Open questions / Environment notes). Copied to `docs/HANDOFF.md` of the derived project. Updated by `/wrap-up` at end of session; read FIRST when a new session opens the project.

**Modified in `templates/`:**

- `lessons.md` — title now carries `{SLUG}` substitution; seeded with a first entry ("Bootstrap completed") that demonstrates the entry format, instead of an empty `## Entries` block.

**bootstrap.md changes:**

- Step 5 (Branch protection) fully rewritten:
  - Always attempt `gh api PUT branches/main/protection` regardless of the front-loaded `HAS_ADMIN` prediction (that flag is best-effort and always false for fine-grained PATs that don't expose scopes).
  - Capture HTTP status from `gh` stderr; branch on 403 / 404 / 422 / other with cause-specific remediation text:
    - 403 → PAT lacks `admin:repo_hook` (or fine-grained without `administration: write`);
    - 404 → token cannot see repo (wrong owner / not collaborator / repo never created);
    - 422 → rule already exists with a different shape.
  - Manual UI fallback now has a clickable URL (`https://github.com/$OWNER/$SLUG/settings/branches`), 8 numbered steps including a note that `backend-ci` appears in the status check dropdown only after the workflow has run at least once (already triggered by Step 4 via `workflow_dispatch`).
  - Removed the buggy `&& echo ... || { HAS_ADMIN=False }` pattern that re-assigned a variable but didn't actually re-evaluate the next branch.
- Step 2: added `templates/HANDOFF.md` → `docs/HANDOFF.md` copy line with the same `{SLUG}`/`{DATE_ISO}`/`{OWNER}` substitution as the other P1 scaffolding templates.
- Step 4 cleanup verification: `17 files` → `18 files`, with the new file in the explicit list (`docs/HANDOFF.md`).

**README.md changes:**

- Docs seeds line in the Templates subsection now lists `HANDOFF.md` with its destination and purpose; `lessons.md` description clarified to "seeded with a first entry".

**Plan:** `docs/plans/0004-bootstrap-handoff-and-branch-protection.md`.

**Out of scope (true P3, not started):**

- A `/handoff` command (extension of `/wrap-up`) that writes `docs/HANDOFF.md` from current session state automatically.
- A pre-bootstrap permission probe that calls `gh api -X GET /user --jq '.permissions // empty'` to predict `createRepository` capability for fine-grained tokens.
- A "wsl gate" Skill that quiets the WSL warnings on Linux / macOS hosts (where they don't apply).

**Verification:** `templates/HANDOFF.md` 2147 B with 8 substitution tokens; `templates/lessons.md` now has both `{SLUG}` (title) and `{DATE_ISO}` (seed entry); `bootstrap.md` 27160 B with `HANDOFF`, `18 files`, `HTTP 403/404/422`, `workflow_dispatch` markers all present; `README.md` Docs seeds line includes `HANDOFF.md`.

---

## 2026-05-30 — Project-scaffolding templates (P1)

Followed P0 with the deferred P1 items so that a derived project is born with the documents the agent pipeline assumes already exist.

**Created in `templates/`:**

- `PROJECT_README.md` — copied to the derived project's root `README.md` (Quick start, Docker commands, link to `CLAUDE.md` + `/doctor`/`/preflight`/`/synthesize-brief`, "where things live" map, staging deploy).
- `PROJECT.md` — copied to `docs/PROJECT.md`. Skeleton with empty sections (`Project`, `Goal`, `Scope`, `Domain`, `Stakeholders`, `Constraints`, `Assumptions`, `Open questions`, `Glossary`, `References`) — `/synthesize-brief` fills these from anything under `docs/`. Removes the prior failure mode where `ba` ran without a brief.
- `api_INDEX.md` — copied to `docs/api/INDEX.md`. Required by `.claude/rules/api-docs.md` lifecycle; previously absent → `docs-writer` had no file to update.
- `WORKLOG.md` — copied to `docs/WORKLOG.md` (replaces the empty `touch`). Seeded with a first "Bootstrapped from claude-django" entry plus a "Next" checklist (verify branch protection, fill `PROJECT.md`, run `/preflight`).

**Substitution tokens:** `{SLUG}`, `{DATE_ISO}`, `{OWNER}` — replaced inline by `devops` during Step 2 (sed or `pathlib.write_text(read_text().replace(...))`). `{TODO}` is intentionally left as a visible placeholder for the user.

**bootstrap.md changes:**

- Step 2 (Mode A): four new `cp` operations + explicit substitution instructions; removed the `touch docs/WORKLOG.md` (template now seeds it).
- Step 4 cleanup verification: `13 files` → `17 files`, plus a grep check to assert no unresolved tokens leak into the project.

**README.md changes:**

- Templates subsection split into four labeled groups: Infrastructure / Docs seeds / Project scaffolding (P1, new) / Language. Each template now lists its destination path and purpose.

**Plan:** `docs/plans/0003-bootstrap-project-scaffolding-templates.md`.

**Out of scope (deferred):**

- Branch protection 403 fallback when even classic-PAT `gh api PUT` fails.
- HANDOFF.md placeholder for multi-session derived projects.
- `lessons.md` initial entry seeding (file already gets copied; first entry can wait).

**Verification:** new templates 4367 / 1548 / 2665 / 1855 bytes; tokens present per file (PROJECT_README: 5, PROJECT: 15, api_INDEX: 1, WORKLOG: 3). `bootstrap.md` grep matches all expected markers; README "Project scaffolding (P1, new)" line in place.

---

## 2026-05-30 — Bootstrap robustness (P0)

Real-run audit of `/bootstrap` on `carlsberg-ir-data-service` (Windows Git Bash + fine-grained PAT + Cowork) surfaced four systemic preflight bypasses. All four were silent: the bootstrap "succeeded" because the gates never fired.

**Root cause:** `.claude/memory/env-detect.json` is the source of truth for `platform_supported`, `pat_kind`, `scopes`, etc. — but it is only written by the `SessionStart` hook in Claude Code CLI. In Cowork there is no hook; the orchestrator agent, finding the file missing, fabricated one with happy-path values (`platform_supported: true`, `has_repo_scope: true`) so that preflight passed. That bypass was never explicitly forbidden by the spec.

**Fixes (committed in one batch):**

- `README.md` — new "Where this runs (supported runtime)" section near the top: claude-django is designed for Claude Code CLI inside WSL2 Ubuntu / Linux / macOS; Cowork, Windows native shells, and Claude API/SDK are explicitly NOT supported runtimes. Rationale included.
- `scripts/detect-env.py` — `_gh_pat_kind()` helper that classifies the active credential as `classic` / `fine-grained` / `unknown` by matching the token prefix from `gh auth token` (`ghp_`/`gho_`/`ghu_`/`ghs_` → classic; `github_pat_` → fine-grained). Never logs the token value. Exposed as `gh.pat_kind`; schema bumped to v3.
- `.claude/commands/bootstrap.md` — three preflight hardenings:
  - new blocker `FINE_GRAINED_PAT_NOT_SUPPORTED` in the env-detect probe (fires when `gh.pat_kind == "fine-grained"`);
  - `UNSUPPORTED_PLATFORM` is now an explicit hard-STOP: "Do NOT offer the user an `AskUserQuestion: Proceed anyway` branch";
  - new top-of-section policy note: `env-detect.json` must never be hand-written to skip a blocker; if it is missing, run `python scripts/detect-env.py` manually or STOP `NO_PYTHON`.
- `.claude/commands/doctor.md` — mirrors the same three blockers as audit items: PAT kind audit, platform audit, env-detect.json integrity (with the explicit non-fabrication rule).
- `.claude/rules/environment.md` — new "gh PAT kind" row in Scope 2 and a new "env-detect.json integrity (hard rule)" section between Scope 2 and Scope 3 documenting that the file is the source of truth and must not be fabricated by humans or LLM agents.

**Plan:** `docs/plans/0002-bootstrap-robustness.md`.

**Out of scope (deferred to P1, now done above):**

- ~`templates/PROJECT_README.md` for new projects.~ Done in P1.
- ~`docs/api/INDEX.md` and `docs/PROJECT.md` placeholders in bootstrap Step 2.~ Done in P1.
- ~WORKLOG initial entry in derived projects.~ Done in P1.
- Branch protection fallback when `gh api PUT` returns 403 even with a classic PAT. (Still deferred to P2.)

**Verification:** `python scripts/detect-env.py` AST-parses; markers `FINE_GRAINED_PAT_NOT_SUPPORTED`, `pat_kind`, `Where this runs`, `Never hand-write` present in expected files; total batch ~76 KB across six files; no Edit-on-mount truncations after retrying critical writes via `python pathlib`.

---

## 2026-06-01 — main — Quality audit of the carlsberg test project + template hardening

**Context:** Audited `carlsberg-ir-data-service` (first real bring-up of the template: `/bootstrap` -> `/synthesize-brief` -> `/preflight` -> product-import feature -> `/wrap-up`) to judge how well the template + agent pipeline performed. Two passes: a broad inventory and a skeptical, evidence-based review (ran `manage.py check`, the OpenAPI drift gate, ruff, Python repros).

**Findings (full report: `docs/reviews/quality-audit-carlsberg-20260601.md`):**
- Strengths: TDD order honored (RED test commit precedes GREEN impl), Conventional Commits, OpenAPI drift gate passes, ruff clean, Google docstrings, DB-state assertions + real triangulation.
- Delivery (RED): PR #4 never merged - feature stranded on the branch; `/wrap-up` left `HANDOFF.md` 100% `{TODO}` and the tree dirty; WORKLOG overstated merge status.
- Feature code (RED): broad `except Exception` per row -> corruption returns HTTP 200; `format=csv` + JSON body silently creates a junk product; non-atomic 409 -> 500 under concurrency.
- Template defect: scaffolded `pyproject.toml` lacked `[tool.setuptools.packages.find]` -> `pip install -e` fails in every new project.

**Done (committed `cb33643`, pushed to origin/main):** Plan `docs/plans/0006-quality-audit-fixes.md` + 7 fixes:
- `templates/pyproject.toml` - add `[build-system]` + `[tool.setuptools.packages.find]`.
- `/wrap-up` - verify merge via `gh` before writing WORKLOG; mandatory HANDOFF regen (assert no `{TODO}`); enumerate touched doc files for the commit.
- `reviewer` - flag silent-failure anti-patterns (broad except, content-vs-format, unguarded IntegrityError->409, unbounded upload).
- `tester` - explicit 409 + file-upload edge cases (both mismatch directions, encoding, empty fields, concurrency, partial-batch).
- `app-readme` / `no-stubs` / `bootstrap` - README<->INDEX<->OpenAPI reconciliation; initialize `docs/STUBS.md` as an empty ledger.
- `scripts/session-start.sh` - clear stale empty `.git/index.lock` on /mnt.

**Decision (TDD verdict):** the agents applied TDD correctly by process (RED-first, DB assertions, triangulation) but the RED test set was too shallow to catch the two import bugs; addressed by the expanded `tester` checklist.

**Next steps / open:**
- Local `.git/index` corrupted on the /mnt mount (`bad index file sha1 signature`) and `templates/pyproject.toml` worktree file truncated by the Cowork mount - repair from the host (see HANDOFF "Next step"). History/origin intact; nothing lost.
- Verify the pyproject fix end-to-end: fresh `/bootstrap` on a clean project, confirm `pip install -e backend` / CI install succeeds.
- Clean up pre-existing half-staged truncated renames under `templates/scripts/` and `templates/todo.md` (physical files intact).

---
