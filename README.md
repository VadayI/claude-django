# Claude Code configuration for Django REST Framework projects

A ready-made Claude Code configuration for **Django REST Framework** backend projects with **Test-Driven Development** discipline, an **API-first** process, **mandatory OpenAPI documentation** (drf-spectacular) locked by a CI drift gate, and work done **exclusively through Pull Requests**. A real production frontend, if needed, lives in a separate repository. This config turns Claude Code into a development team: an orchestrator delegates tasks to specialized agents through a clear pipeline.

**Stack:** Python 3.13 · Django 6 · Django REST Framework · PostgreSQL 18 · Docker · pytest + pytest-django · ruff · drf-spectacular (OpenAPI)
**Environment:** Windows + WSL2 + Docker Desktop (on Windows: WSL2 mandatory) · Staging — Debian VPS · GitHub as the source of truth

---

## Where this runs (supported runtime)

This config runs in **Claude Code CLI** (the terminal `claude` command) inside **WSL2 Ubuntu** on Windows (mandatory — ADR `0005`), **Linux**, or **macOS**. That is the only supported runner.

**Not supported:** Claude Desktop / Cowork / Code mode, Windows-native shells (PowerShell, cmd, Git Bash), and the Claude API/SDK standalone. All three lack the `SessionStart` hook that writes `.claude/memory/env-detect.json` and never load the `.claude/agents/` pipeline — so the methodology this repo is built around isn't there, and the `/doctor` / `/bootstrap` gates can't fire honestly. You *can* use Claude Desktop as a **companion** (read/edit files, discuss architecture, review a diff), but run `/bootstrap`, the feature pipelines, TDD, and PRs in **Claude Code CLI inside WSL2**.

The two most common runner failures — the Windows `claude.exe` shadowing the WSL2-native CLI, and a genuinely Windows-native shell — and their fixes live in **[Troubleshooting](#troubleshooting-startup--doctor-hard-stops)** below.

---

## Using Claude Code CLI (the only supported runner)

Everything here — agents, slash-commands, environment gates — runs in **Claude Code CLI**, started by typing `claude`. On Windows that terminal must be **WSL2 Ubuntu**, not PowerShell/cmd/Git Bash and not the Desktop app.

**1. Install the CLI inside WSL2** (one-time). In a real Ubuntu shell:

```bash
node --version                       # need Node 18+ (install via nvm if missing)
npm install -g @anthropic-ai/claude-code
which claude                         # MUST be /home/... or /usr/...  — NOT /mnt/c/...
```

> Installing the CLI on the Windows side does **not** give you a WSL2 `claude`. If `which claude` shows `/mnt/c/...`, the Windows binary is shadowing it on PATH — fix per [Troubleshooting](#troubleshooting-startup--doctor-hard-stops). One-shot alternative for the whole toolchain (Python / Node / `claude` / `gh` + the PATH fix): `bash scripts/setup-wsl.sh` (idempotent; never touches secrets or git).

**2. Where to put the project.** Working from `/mnt/c` or `/mnt/d` (a Windows drive) is **fully supported** (ADR `0009`); `/doctor` won't ask you to move it. The only caveats are slower Docker bind-mounts and occasional CRLF / `git index.lock` quirks (run `git` from the host shell). `~/projects/<slug>` in the WSL2 FS is optional — for faster bind-mounts only.

**3. Launch and verify the runner.** From the project root, check the startup banner: forward-slash paths and `(from .claude/settings.json)` mean a correct WSL2 launch; **backslashes** (`D:\Dev\...`, `.claude\settings.json`) mean you launched `claude.exe` — `/exit` and fix the runner. On start the `SessionStart` hook writes `.claude/memory/env-detect.json` (`platform_supported: true`, `is_wsl2: true`, `shell: bash`) — exactly what `/doctor` needs to pass the platform gate.

> Run shell fixes in the **bash terminal**, not Claude's `❯` prompt. When `/doctor` says to run `npm install …`, that goes in the terminal — pasting it into the `❯` chat just sends Claude a message.

**4. Drive the work with slash-commands.** `/doctor` first on a new machine (audits the environment, proposes fixes); `/preflight` before the first feature (brief, stack, Context7, GitHub access). Then describe a feature in plain language and the orchestrator runs `ba → api-architect → tester(RED) → django-developer(GREEN) → Quality Gate → docs-writer`. End each session with `/wrap-up`, commit, and `git pull` on the other machine.

**5. GitHub access** — create the repo by hand + a fine-grained per-repo token (ADR `0008`). Create an **empty** repo at https://github.com/new (no README/.gitignore/license), then mint a **fine-grained token scoped to just that repo** (`/bootstrap` and `/doctor` print a ready-made template URL):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_xxxxxxxx
```

Minimal permissions: **Contents** RW, **Metadata** RO (auto), **Pull requests** RW, **Workflows** RW, **Administration** RW (the last enables auto branch protection; omit it and protection becomes a manual UI step). A classic PAT works too but grants whole-account access.

Short version: **install the CLI in WSL2 → clone the repo (Windows drive is fine) → `claude` → `/doctor` → `/bootstrap` → `/preflight` → first feature.** If you must use Claude Desktop, treat it as an editor / chat companion **after** running these from the CLI.

---

## Troubleshooting startup & /doctor hard-stops

**The golden path (memorize this):** *install the CLI inside WSL2 → `which claude` shows `/home/...` (not `/mnt/c/...`) → launch `claude` from the project → `/doctor` → `/bootstrap`.* Almost every "it doesn't work" is one of the runner / PAT issues below. `/doctor` is doing its job when it HARD-STOPs — the message tells you exactly which gate failed; match the symptom here.

| Symptom (what you see) | What it actually means | Fix (run in a **bash shell**, not the `❯` prompt) |
|---|---|---|
| `🔴 UNSUPPORTED_PLATFORM` with **`wrong_runner_suspected: true`**, banner shows **backslash** paths (`D:\Dev\...`, `.claude\settings.json`), `python.executable` is `C:\…\python.exe` | You typed `claude` inside WSL2 but PATH interop launched the **Windows `claude.exe`** — the Linux CLI was never installed (or is shadowed on PATH). **WSL2 is present; this is not a "WSL2 missing" error.** | `npm install -g @anthropic-ai/claude-code` → `hash -r` → `which claude` (must be `/home/…` or `/usr/…`). If still `/mnt/c/…`: `echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc`. Relaunch `claude`. Project staying on `/mnt/d` is fine — not the cause. |
| `🔴 UNSUPPORTED_PLATFORM` with `wrong_runner_suspected: false`, `is_wsl2: false`, and a PowerShell/cmd/Git-Bash prompt (or Claude Desktop) | You are genuinely on a **Windows-native shell** with no WSL2 — bash idioms and Docker bind-mounts won't behave. | `wsl --install -d Ubuntu` (PowerShell) → `wsl --set-default Ubuntu` → inside Ubuntu install the toolchain (`sudo apt install -y git curl gh python-is-python3 python3-pip`) and the CLI (step 1), then launch `claude` from Ubuntu. |
| `🔴 NO_ENV_DETECT` — `.claude/memory/env-detect.json` is missing | The `SessionStart` hook didn't run — usually `scripts/` wasn't copied during Quick start, or Python isn't on PATH. The hook **fails silently** without `scripts/detect-env.py`. | Confirm `scripts/detect-env.py` exists in the project; run `python scripts/detect-env.py` once by hand. If it errors, fix the cause (install Python 3.10+). **Never hand-write this file** — fabricated values bypass the safety gates. |
| `🔴 NO_PYTHON_OR_HOOK` — only `python3` exists, no `python` | The hook calls `python`; Ubuntu ships it as `python3`. | `sudo apt install -y python-is-python3`, then reopen `claude`. |
| `✗ REPO_NOT_FOUND` — `/bootstrap` can't see the repo | Per ADR `0008` you create the GitHub repo **by hand**; either the empty repo wasn't created or your fine-grained token isn't scoped to it. (`FINE_GRAINED_PAT_NOT_SUPPORTED` is retired — fine-grained tokens are now the recommended credential.) | Create the empty repo at https://github.com/new, mint a fine-grained token via the template URL `/bootstrap` prints (Only select repositories → your repo; Contents/Pull requests/Workflows/Administration = RW), `export GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_…`, re-run. |
| `🔴 NO_GH_SCOPES` — classic PAT missing scopes | **Classic PATs only** — fine-grained tokens are not scope-gated (ADR `0008`). The classic token lacks `repo`/`workflow`. | `gh auth refresh -s repo,workflow,admin:repo_hook` — or better, switch to a fine-grained per-repo token (see the GitHub access step above). |
| You pasted a shell command (e.g. `npm install …`) and **nothing changed** | You typed it into Claude's `❯` chat prompt, not the terminal — Claude just replied with a note. | `/exit` (or open a second WSL2 tab), run the command in **bash**, then relaunch `claude`. |
| PowerShell: `wsl2: The term 'wsl2' is not recognized` | The command is `wsl`, not `wsl2`. | `wsl` (or `wsl -d Ubuntu`) to enter WSL2 from PowerShell. |
| `which claude` stays `/mnt/c/...` even after the `$(npm config get prefix)/bin` PATH fix | Your `npm` is the **Windows** npm (Linux `node` is present but Linux `npm` is missing), so `npm install -g` put `claude` in the Windows prefix — the PATH trick can't help because that prefix is itself a `C:\...` path. | Confirm with `which node npm`. Let `nvm` own node+npm in WSL2: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh \| bash` → `nvm install --lts` → `npm install -g @anthropic-ai/claude-code`; `which node npm claude` must all be `/home/…`. Or just run `bash scripts/setup-wsl.sh`. |
| Tests slow, `rm` fails, CRLF↔LF flips, `git index.lock` — project under `/mnt/c` or `/mnt/d` | The repo lives on a Windows drive (9p mount). **Fully supported (ADR `0009`)** — these are inherent `/mnt` caveats, not an error, and `/doctor` won't ask you to move. | No action required. Run `git` from the host shell (PowerShell/Git Bash) to avoid `index.lock`. Moving to `~/projects/<slug>` is optional (faster bind-mounts), never required. |

After applying a fix, just re-run `/doctor` — the `SessionStart` hook rewrites `env-detect.json` on each launch, so a corrected runner/PAT shows up immediately. Full rationale for the runner trap: `.claude/rules/environment.md` → *"launch the WSL2-native `claude`"*.

---

## Process philosophy

1. **API-first.** The backend REST API is the primary contract: design it, then build it test-first (models → serializers → views → routes → permissions → tests → docs). Everything else hangs off the contract.
2. **TDD in Python.** No production code without a failing test first. Red → Green → Refactor cycle.
3. **Mandatory REST API documentation.** Every endpoint is captured in OpenAPI (auto-generated by `drf-spectacular` from serializers/views, committed to `docs/api/openapi.yml`). A CI drift gate (`scripts/check_openapi_drift.sh`) regenerates the schema and fails the PR on any diff, so **code and docs cannot drift**. Swagger UI (`/api/schema/swagger/`) and Redoc (`/api/schema/redoc/`) are the interactive API client. A full production frontend, if needed, lives in a **separate repository**.
4. **Pull Requests only.** Branch → PR → review → merge. Direct commits to `main` are forbidden (branch protection).
5. **Context in Git.** Claude's work history (`CLAUDE.md`, `.claude/memory/`, `docs/WORKLOG.md`, ADRs) is committed to the repo — so it stays in sync between the two machines via a plain `git pull`.

---

## What's inside

### Core agents (11) — `.claude/agents/`

| Agent | Purpose | Model |
| --- | --- | --- |
| `ba` | Business analysis, user stories, scope, endpoint draft | opus |
| `api-architect` | REST API contract: schemas, codes, permissions, versioning | opus |
| `django-developer` | Django/DRF implementation (GREEN phase) | sonnet |
| `tester` | pytest tests, TDD (RED phase) | opus |
| `dba` | Models, migrations, indexes, PostgreSQL optimization, N+1 | sonnet |
| `reviewer` | Code review before PR | opus |
| `security-scanner` | Security audit: authz, OWASP, secrets | opus |
| `debugger` | Bug investigation, root-cause | sonnet |
| `devops` | Docker, deploy to VPS staging, reverse-proxy | sonnet |
| `ci-cd-engineer` | GitHub Actions CI on every PR | sonnet |
| `docs-writer` | `docs/api`, OpenAPI sync, ADR, WORKLOG, PR description | sonnet |

### Optional agents (11) — opt-in

Not used in every project — activate only when the task calls for it:

| Agent | Purpose | Model |
| --- | --- | --- |
| `auditor` | Workflow auditor — reads `.claude/memory/command-log.jsonl` + live state, suggests the next command (run via `/audit`) | sonnet |
| `brief-synthesizer` | Reads `docs/**` (md/txt/pdf/docx/images) and writes a structured `docs/PROJECT.md` (run via `/synthesize-brief`) | sonnet |
| `qa` | E2E/browser tests (Playwright), incl. mobile via staging | opus |
| `celery-specialist` | Background/async tasks: Celery + Redis/RabbitMQ | sonnet |
| `integration-architect` | OAuth, webhooks, payments, third-party APIs | sonnet |
| `devil` | Devil's advocate — challenges the plan during planning | opus |
| `django-refactoring-expert` | Refactoring, N+1, tech-debt cleanup (behavior-preserving) | opus |
| `domain-architect` | DDD-lite modeling for genuinely complex domains | opus |
| `guide-writer` | User-facing onboarding guides — `docs/guides/admin.md` + `docs/guides/api-consumer.md` (run via `/guides`) | sonnet |
| `code-structure-auditor` | File-size audit (800-line limit) + folder-split proposals (run via `/structure-audit`) | sonnet |
| `template-sync` | Sync a derived project's config to a newer `claude-django` version, preserving local customizations (run via `/update-from-template`) | sonnet |

### Rules (17) — `.claude/rules/`

`workflow.md` (orchestration & pipeline), `tdd.md` (Red-Green-Refactor), `no-stubs.md` (no stubs/fake data in prod — marker + `docs/STUBS.md` ledger + CI gate), `api-docs.md` (mandatory OpenAPI — `docs/api/openapi.yml` + CI drift gate), `app-readme.md` (every Django app has a local `README.md` — CI gate), `verification.md` (endpoint verification handoff — auto-generated `docs/verify/<feature>.md` from `.claude/memory/endpoints.json` + OpenAPI, feeds `/verify`), `user-guides.md` (living user-facing guides — `docs/guides/admin.md` + `docs/guides/api-consumer.md`, owned by `guide-writer`, gated by `reviewer`), `preflight.md` (kickoff hard gate — brief/stack/Context7/GitHub access before any code), `architecture.md` (API-first, structure), `code-style.md` (ruff incl. Google-style docstring `D` rules + 800-line file-size limit, CI gate `scripts/check_file_size.sh`), `testing.md` (test policy), `git-operations.md` (PR process, no direct commits to main), `docker-commands.md` (environment commands), `serializers-permissions.md` (DRF validation + permission classes, 401/403/IDOR), `migrations-tasks.md` (migration conventions + Celery tasks), `mcp-stack.md` (which MCP tool to use when), `environment.md` (the expected local environment — source of truth for `/doctor`).

### Skills (12) — `.claude/skills/`

Core: `django-specialist`, `drf-api-design`, `pytest-tdd`, `postgresql-optimization`, `docker-compose-django`, `github-actions-django`.

Review & strategy: `code-reviewer`, `security-reviewer`, `playwright-e2e`, `test-master`, `architecture-designer`, `ddd-strategic-design`.

#### Recommended external skills (enable per machine)

These are standalone skills, not vendored into the repo — enable them in your environment (Cowork → "Add", or `/plugin`/skills install) rather than copying their content here:

- `brainstorming` (Superpowers) — structured ideation for ambiguous tasks. Used during Plan Mode by the orchestrator and `ba` / `api-architect` before locking the contract. Highly recommended.
- `plan-writing` (Superpowers) — disciplined plan format (scope · sub-tasks · affected files · risks · open questions). Pairs with the Plan Mode rule in `workflow.md`. Highly recommended.
- `mcp-builder` — building MCP servers (Python/FastMCP or Node SDK). Useful when extending `.mcp.json` with a project-specific server.
- `web-artifacts-builder` — elaborate React/Tailwind/shadcn HTML artifacts. Optional — this repo is backend-only; the interactive API client is Swagger UI / Redoc (drf-spectacular), not a hand-rolled frontend.

> Superpowers marketplace is already enabled via `.claude/settings.json` (`enabledPlugins.superpowers@superpowers-marketplace`), so `brainstorming` and `plan-writing` are available without extra setup — just confirm with `/plugin` if they show as installed.

### Templates — `templates/`

Infrastructure: `docker-compose.yml`, `backend.Dockerfile`, `pyproject.toml` (includes `drf-spectacular` + ruff `FIX`, `D` for Google-style docstrings), `.env.example`, `.github/workflows/backend-ci.yml` (runs ruff + stub gate + OpenAPI drift gate + per-app README gate + file-size gate + pytest), `scripts/check_stubs.sh` (stub gate — fails on unlogged `# STUB:`/`NotImplementedError`), `scripts/check_openapi_drift.sh` (OpenAPI gate — fails if `docs/api/openapi.yml` doesn't match the schema regenerated from code), `scripts/check_app_readmes.sh` (per-app README gate — fails if any `backend/apps/<app>/` lacks `README.md`), `scripts/check_file_size.sh` (file-size gate — fails on any non-migration `*.py` over 800 lines).

Docs seeds: `STUBS.md` (copy to `docs/STUBS.md` — the stub ledger), `APP_README.md` (copy to `docs/APP_README.md` — template that `django-developer` copies into each new app), `lessons.md` (copy to `docs/lessons.md` — append-only feedback log, seeded with a first entry), `todo.md` (copy to `docs/todo.md` — cross-session backlog), `HANDOFF.md` (copy to `docs/HANDOFF.md` — multi-session handoff snapshot: current state / last finished / next step / open questions, updated by `/wrap-up`).

Project scaffolding (P1, new): `PROJECT_README.md` (copy to `README.md` of the derived project — Quick start, Docker commands, link to `CLAUDE.md` and `/doctor`/`/preflight`), `PROJECT.md` (copy to `docs/PROJECT.md` — brief skeleton with empty `Project`/`Goal`/`Scope`/`Domain`/`Stakeholders`/`Constraints`/`Glossary`/`Open questions` sections for `/synthesize-brief` or hand-fill), `api_INDEX.md` (copy to `docs/api/INDEX.md` — human endpoint index pointing at OpenAPI as the contract), `WORKLOG.md` (copy to `docs/WORKLOG.md` — seeded with an initial "Bootstrapped from claude-django" entry instead of an empty `touch`).

Language: `output-language.md` (copy to `.claude/rules/output-language.md` when the user picks a non-English working language; `/bootstrap` and `/set-language` substitute `{LANGUAGE_NATIVE}`).

Verification: `endpoints.json` (copy to `.claude/memory/endpoints.json` — the route registry `api-architect` writes and `/verify` reads), `verify_TEMPLATE.md` (copy to `docs/verify/_TEMPLATE.md` — per-feature verification-guide template that `docs-writer` renders into `docs/verify/<feature>.md`).

Guides: `guides_admin.md` (copy to `docs/guides/admin.md` — operator onboarding: first start, data loading, admin, day-2 ops) and `guides_api_consumer.md` (copy to `docs/guides/api-consumer.md` — integrator onboarding: base URL, auth, first request, conventions); both owned by `guide-writer` per `.claude/rules/user-guides.md`.

All scaffolding templates use `{SLUG}`, `{DATE_ISO}`, `{OWNER}` substitution tokens that `/bootstrap` Step 2 replaces inline. `{TODO}` tokens are intentionally left as visible placeholders for the user to fill later.

### Commands (20) — `.claude/commands/`

Slash-commands that orchestrate agents over the repo / a GitHub PR (PR commands need the `github` MCP from `.mcp.json` + an authenticated `gh`). Every command appends a single line to `.claude/memory/command-log.jsonl` so the `auditor` agent can suggest what to run next.

- `/bootstrap [slug]` — scaffold a Django backend. Front-loaded preflight: refuses to start without Python/`gh`/`docker`/templates and with a working `gh` credential (a fine-grained per-repo token is recommended — ADR `0008`). Two modes: **A. Fresh** (you create the empty GitHub repo by hand; bootstrap links `origin` to it, then scaffolds skeleton, drf-spectacular, first commit + push to main, auto-trigger `backend-ci` so GitHub registers it as a status check, auto branch protection when `admin:repo_hook` is granted — manual GitHub UI fallback otherwise), **B. Resume** (existing repo with partial scaffold — detects each missing piece and ships it as a separate PR). Each major step has a `⏸ Checkpoint — Resume` marker, so failed runs can be re-invoked safely. Run once per new project; can re-run in Mode B to fix gaps.
- `/synthesize-brief` — recursively read `docs/**` (briefs, ТЗ, PDFs, .docx, screenshots) and synthesize a structured `docs/PROJECT.md` via the `brief-synthesizer` agent. Output via feature branch + PR.
- `/audit [focus]` — workflow audit via the `auditor` agent: reads the command log + live state (git/CI/schema/STUBs) and proposes the next command to run. `focus` ∈ `git|ci|docs|gates` (default: all).
- `/doctor [scope]` — environment configurator: audits the machine against `.claude/rules/environment.md` (system tools · Claude config & access including **`gh` PAT scopes** for `/bootstrap` · project state · git hygiene), classifies the scenario (`no-config` / `fresh` / `existing-incomplete` / `active`), reports a checklist, and proposes fixes — applied only after you confirm. `scope` ∈ `system|claude|project|git` (default: all).
- `/preflight [scope]` — project kickoff hard gate: verifies access to the build inputs (project brief/description, tech stack, library docs via Context7, the GitHub project) before any feature work. If a critical input is missing, agents stop instead of guessing. `scope` ∈ `brief|stack|docs|github` (default: all).
- `/fix-ci <PR>` — pull GitHub Actions logs, diagnose the failure (lint/tests/coverage/build), fix it via `debugger` → `django-developer`, verify with ruff/pytest.
- `/review-pr <PR>` — full review posting inline comments on the diff via the `reviewer` agent.
- `/simplify [path]` — Code Simplifier: inspect the diff and simplify without changing behavior (tests stay green).
- `/create-pr [title]` — push the current branch and open a PR from the git-operations template (never to `main`).
- `/security-check [path]` — focused security audit of the working changes via `security-scanner`.
- `/update-docs [scope]` — refresh `docs/api`, `WORKLOG`, ADR, `lessons.md` via `docs-writer`.
- `/wrap-up [note]` — end-of-session: summarize, update `WORKLOG`/`lessons`, run ruff/pytest, show `git status`, propose a commit (never auto-push).
- `/handoff [--note "..."] [--print]` — regenerate `docs/HANDOFF.md` (rolling snapshot: Current state / Last finished / In progress / Next step / Open questions / Environment notes) from current git/PR/CI state. Read-only on everything except HANDOFF.md. Pairs with `/wrap-up` and is the file `/audit`'s `auditor` reads to promote a concrete next step.
- `/set-language` — pick the response language for this project (writes `.claude/rules/output-language.md` from `templates/output-language.md` with the chosen native name). Run once after `/bootstrap` if you want a non-English working language.
- `/verify [feature] [--run]` — generate the human-facing endpoint verification guide `docs/verify/<feature>.md` (Swagger steps + copy-paste `curl` with expected codes) from `.claude/memory/endpoints.json` + `docs/api/openapi.yml`. With `--run`, also executes it against the live dev server and reports pass/fail. The same guide is emitted automatically by `docs-writer` at the end of every feature pipeline (see `.claude/rules/verification.md`).
- `/guides [admin|api]` — generate/refresh the user-facing onboarding guides `docs/guides/admin.md` (operator) and `docs/guides/api-consumer.md` (integrator) via `guide-writer`, reconciling every command/endpoint they name against the code + `docs/api/openapi.yml`. Auto-refreshed in the pipeline's Documentation phase when the surface changes (see `.claude/rules/user-guides.md`).
- `/structure-audit [path]` — file-size & structure audit via `code-structure-auditor`: runs `scripts/check_file_size.sh`, lists files over/approaching the 800-line limit, and proposes concrete folder-splits (package + `__init__.py` re-exports). Read-only; hand 🔴 splits to `django-refactoring-expert`.
- `/update-from-template [url|ref] [--dry-run]` — update a project bootstrapped from `claude-django` to a newer template version via `template-sync`: overwrites only template-owned files (agents, commands, skills, rules, gate scripts), preserves project-owned ones (`CLAUDE.md` edits, `settings.json`, `.claude/memory/`, `output-language.md`, `docs/`, `backend/`), surfaces merge-by-hand files as diffs, and opens a **PR** (never pushes to `main`). See ADR `0014`.
- `/config` — thin wrapper over `/doctor`'s `claude` scope: quick audit of `.claude/settings.json`, `.mcp.json`, MCP servers (github/context7), env keys (set/unset only), and hooks.
- `/plugins` — thin wrapper over `/doctor`'s plugin checks: reports installed vs expected plugins and prints the paste-ready `/plugin install …` block (plugin install is a manual UI step the agent can't run).

### Plugins (recommended baseline)

Auto-enabled per-project via `.claude/settings.json` `enabledPlugins` (ADR `0011`, derived from the maintainer's proven setup): `superpowers@superpowers-marketplace` (brainstorming/plan-writing), `engineering@knowledge-work-plugins`, `playwright@claude-plugins-official` (browser tools used by the `qa` agent / E2E), and `github@claude-plugins-official` + `context7@claude-plugins-official` (which provide the GitHub + Context7 MCP — see below). `claude-hud@claude-hud` is recommended too but stays a **personal/global** HUD install, not committed per-project. `code-review` and `code-simplifier` are intentionally **not** in the baseline — their project-agnostic skills duplicate the project-tuned `reviewer` / `security-scanner` / `django-refactoring-expert` agents, so the canonical paths stay `/review-pr`, `/security-check`, `/simplify`. Install lines are printed by `/bootstrap` Step 6 and `/plugins` (plugin install is a manual UI action).

### MCP servers — official plugins (recommended) or `.mcp.json` (fallback)

`github` (PR data; needs env `GITHUB_PERSONAL_ACCESS_TOKEN`) and `context7` (up-to-date Django/DRF docs; needs `CONTEXT7_API_KEY`) come from the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` in the recommended baseline above. The committed `.mcp.json` + `enabledMcpjsonServers` path is an **optional fallback** — don't enable both for the same MCP (it double-registers). Either way the tool names are identical. Note: `GITHUB_PERSONAL_ACCESS_TOKEN` is required regardless, because the `gh` CLI uses it for push / PR / branch-protection — the plugin only swaps the MCP transport, not gh auth.

#### Context7 setup (`CONTEXT7_API_KEY`)

Context7 (by Upstash) serves **current** library documentation to agents, so `api-architect` / `django-developer` verify Django and DRF APIs against today's docs instead of relying on the model's training cutoff. `/preflight` treats Context7 reachability as a **hard gate** (waivable only on explicit override — see `.claude/rules/preflight.md`), so set the key before the first feature.

1. **Get the key.** Sign in at [context7.com](https://context7.com) and create an API key in the dashboard (the free tier is enough for doc lookups).
2. **Export it** in your WSL2 shell — persist it in `~/.bashrc` (or `~/.profile`) so every session and the MCP `npx` process inherit it:

   ```bash
   echo 'export CONTEXT7_API_KEY="ctx7_..."' >> ~/.bashrc
   source ~/.bashrc
   ```

   The MCP is launched as `npx -y @upstash/context7-mcp --api-key ${CONTEXT7_API_KEY}` (see `.mcp.json`), so the variable must be set **before** you start `claude`. Never commit the key — it goes in the environment, not in any tracked file.
3. **Verify.** `[ -n "$CONTEXT7_API_KEY" ] && echo set` should print `set`, and `/doctor` (Claude config scope) reports it as ✅. Because the MCP runs via `npx`, **Node.js 18+ is required** — it already is project-wide (see *Prerequisites*) to install the WSL2-native Claude Code CLI, and Context7 simply reuses the same Node.

### Project settings — `.claude/settings.json`

Per-project Claude Code config: tool permissions (allow `git`/`gh`/`docker`/`npm`, deny direct push to `main` and reading `.env`/secrets), `DJANGO_SETTINGS_MODULE`, auto-enabled plugins (Superpowers, `engineering@knowledge-work-plugins`, plus `playwright`/`github`/`context7` from `claude-plugins-official` — ADR `0011`), and a `Stop` hook that runs `ruff format` + `ruff check --fix` after each turn (silently skips if the `backend` container is down). `model` defaults to `opusplan` — change to taste. (github + context7 now come via plugins, so `enabledMcpjsonServers` is empty by default; `.mcp.json` is the fallback.)

### Development pipeline

```
Feature:   ba → api-architect → tester(RED) → django-developer(GREEN)
              → [reviewer | security-scanner | dba] → docs-writer (sync docs/api/openapi.yml)
Bug fix:   debugger → tester(regression) → django-developer → reviewer
CI/CD:     ci-cd-engineer / devops → [reviewer | security-scanner]
```

---

## Prerequisites

- [Claude Code](https://code.claude.com) CLI
- **Python 3.10+ on PATH as `python`** (hard requirement; the `SessionStart` hook runs `scripts/detect-env.py`). On Ubuntu install `python-is-python3` if only `python3` is present.
- Docker Desktop with WSL2 backend
- **Shell:** bash in WSL2 Ubuntu (Windows), bash/zsh (Linux/macOS). PowerShell native NOT supported.
- WSL2 (Ubuntu) — **mandatory on Windows**. The project can live on your Windows drive (`/mnt/...`, fully supported — ADR `0009`); `~/projects/<slug>` in the WSL2 FS is optional for faster Docker bind-mounts
- **Node.js 18+ (required, via `nvm`)** — needed to install the WSL2-native Claude Code CLI (`npm install -g @anthropic-ai/claude-code`) and for `npx`-based skills (e.g. the Context7 MCP). `/doctor` reports `NO_NODE` if it is missing or below 18
- A GitHub account

## Quick start (attach the config to an existing project)

> **First time on this Windows machine?** From PowerShell, `wsl --list --verbose` — if you only see `docker-desktop` (Docker's internal BusyBox distro, not for user work), install Ubuntu: `wsl --install -d Ubuntu` then `wsl --set-default Ubuntu`. On first launch set a Unix username/password, then install the toolchain: `sudo apt update && sudo apt install -y git curl gh python-is-python3 python3-pip`. Verify `ID=ubuntu` in `/etc/os-release` (tested on 24.04+).
>
> Then enter WSL with `wsl` (not PowerShell) and `cd` to your project — a `/mnt/c` or `/mnt/d` path is fine (ADR `0009`), no need to move into `~/projects`. The one thing that matters: `which claude` resolves to `/home/...`, not `/mnt/c/...`.

**Fastest — one-line seed.** From the root of your project folder in WSL2, this clones the template and copies the config in one go (idempotent; refuses to clobber an already-seeded folder unless `--force`):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/VadayI/claude-django/main/scripts/install.sh)
# optional args:  install.sh [TARGET_DIR] [--ref GIT_REF] [--url FORK_URL] [--force]
```

Then launch `claude` → `/doctor` → `/bootstrap`. To upgrade an *already-seeded* project use `/update-from-template` instead (it preserves your edits, ADR `0014`).

**Manual equivalent** (what `install.sh` does, if you prefer to run it by hand):

```bash
# in WSL2, from the root of your project (a /mnt/d/... Windows-drive path is fine — ADR 0009)
rm -rf /tmp/claude-django && git clone https://github.com/VadayI/claude-django.git /tmp/claude-django
cp -r /tmp/claude-django/.claude ./
cp /tmp/claude-django/CLAUDE.md ./
cp /tmp/claude-django/.mcp.json ./
cp /tmp/claude-django/.gitignore ./
cp /tmp/claude-django/.gitattributes ./
cp -r /tmp/claude-django/scripts ./          # detect-env.py (SessionStart hook) + log-cmd.py — REQUIRED; the hook fails SILENTLY without it and /doctor will STOP with NO_ENV_DETECT
cp -r /tmp/claude-django/templates ./        # FULL templates/ — /bootstrap Mode A needs all of it
cp /tmp/claude-django/templates/docker-compose.yml ./   # also at repo root (devcontainer entrypoint)
cp /tmp/claude-django/templates/Makefile ./          # dev-loop command shortcuts (make help/test/up/...)
mkdir -p .github/workflows && cp /tmp/claude-django/templates/.github/workflows/* .github/workflows/

# Wipe transient state from the template clone (these are regenerated by the SessionStart hook):
rm -f .claude/memory/env-detect.json .claude/memory/command-log.jsonl

# Before launching `claude`: confirm it is the WSL2-native CLI, not Windows `claude.exe`.
which claude    # expect /home/... or /usr/...  — if it prints /mnt/c/..., see step 1 / step 5 above
```

Then install the plugins (see below) and adjust `CLAUDE.md` for the project name. Then run **`/doctor`** inside `claude` — it detects the scenario and recommends the next command. If `/doctor` HARD-STOPs, jump to **[Troubleshooting startup](#troubleshooting-startup--doctor-hard-stops)** below.

---

## Step-by-step: a NEW project from scratch

1. **Quick start** (above) — copy `.claude/`, `CLAUDE.md`, `.mcp.json`, `.gitignore`, `scripts/`, `templates/` into the new project folder under `~/projects/<slug>` in WSL2.
2. `claude` → `/doctor` — verifies environment and detects scenario `fresh`; recommends `/bootstrap`.
3. `claude` → `/bootstrap` — runs the hard preflight (Python / `gh` / `docker` / templates + GitHub access), then scaffolds the project: links `origin` to the empty repo you created (Mode A never runs `gh repo create`), builds the skeleton + drf-spectacular config, brings Docker up, migrates, generates `docs/api/openapi.yml`, makes the first commit + push to `main`, and enables branch protection. Each step has a `⏸ Checkpoint — Resume` marker; Mode B resumes a failed run. This is the only command that direct-pushes to `main` (documented exception in `.claude/rules/git-operations.md`). Full behaviour: the `/bootstrap` entry under *Commands* above.
4. (manual) Drop your input documents into `docs/` — briefs, ТЗ, PDFs, .docx, screenshots — keeping `docs/api/`, `docs/decisions/`, `docs/plans/` for their existing purpose.
5. `claude` → `/synthesize-brief` — recursively reads `docs/**` (excluding service folders), delegates to `brief-synthesizer`, writes `docs/PROJECT.md` via feature branch + PR.
6. `claude` → `/doctor` → `/preflight` — re-verify environment and build inputs.
7. First feature through the standard pipeline (`ba → api-architect → ...`).

For an existing project from a second machine: skip step 1 (clone instead), run `/doctor` — it will detect `active` or `existing-incomplete` and tell you whether to run `/bootstrap` in resume mode.

---

## Updating an existing project from the template

A project bootstrapped from `claude-django` carries a **pinned copy** of the config from the moment it was forked (ADR `0002`) — there is no automatic upgrade channel. When the template gains new agents, rules, commands, skills, or CI gates, pull them in deliberately with **`/update-from-template`** — by default it syncs from the canonical upstream **`https://github.com/VadayI/claude-django`**:

```bash
# in WSL2, from the root of the DERIVED project
claude
> /update-from-template --dry-run     # preview: what would change, what stays
> /update-from-template                # branch chore/sync-template-<date>, sync, open a PR
```

What it does (via the `template-sync` agent): **overwrites** template-owned files (`.claude/agents/`, `commands/`, `skills/`, `rules/*.md` except your `output-language.md`, the `scripts/` helpers), **preserves** project-owned ones (`CLAUDE.md`, `settings.json`, `.mcp.json`, `.claude/memory/`, all of `docs/` and `backend/`, `.env`), shows merge-by-hand items (`CLAUDE.md` / `settings.json` / `.mcp.json` / `backend-ci.yml`) as additive-only diffs, copies in any new gate scripts, and records the synced commit in `.claude/memory/template-sync.json`. Full rules: ADR `0014` and the `/update-from-template` entry under *Commands* above.

It lands as a **PR** (the PR-only rule applies to derived projects); review the merge-by-hand diffs, merge, then run `/doctor` to re-verify the environment against the refreshed spec. If you maintain your own fork of the template, pass its URL: `/update-from-template https://github.com/<you>/claude-django.git`.

> Manual fallback (if you prefer not to use the command): clone the template to `/tmp`, copy the template-owned folders over your project's `.claude/`, and `diff` `CLAUDE.md` / `settings.json` / the CI workflow by hand. The command just automates this with the ownership rules baked in.

---

## When to run each command

| Command | When to run | How often |
|---|---|---|
| `/bootstrap [slug]` | Once per new project (Mode A) after copying this config; or in Mode B to ship missing pieces of an in-progress repo | Once for Mode A; as needed for Mode B |
| `/synthesize-brief` | When input documents accumulate in `docs/` (briefs/ТЗ/PDFs); after Mode A bootstrap; whenever the source documents change | Once per project initially, as needed for updates |
| `/doctor [scope]` | On a fresh machine; whenever environment feels off | Rare; ~once per machine |
| `/preflight [scope]` | Before the first feature on a project; after long pauses | Once per project, rare repeats |
| `/audit [focus]` | Start of a session; whenever you ask "what should I do now?" | Each session |
| `/wrap-up [note]` | End of every working session | Each session |
| `/create-pr [title]` | When a feature branch is ready to share | Once per feature |
| `/fix-ci <PR>` | As soon as CI goes red on a PR | As needed |
| `/review-pr <PR>` | Before merging any PR | Once per PR |
| `/security-check [path]` | On any change to auth, permissions, sensitive endpoints | As needed |
| `/simplify [path]` | When a freshly-landed diff feels dense | Occasionally |
| `/update-docs [scope]` | When `docs/api/`, ADRs, or WORKLOG need refresh; often automated via `/wrap-up` | As needed |
| `/verify [feature] [--run]` | After a feature is green, to (re)generate or run its manual endpoint checklist | Once per feature; auto at pipeline end |
| `/config` | Quick check that `.claude/settings.json` / `.mcp.json` / MCP keys / hooks are correct | As needed |
| `/plugins` | Check installed vs expected plugins; get the paste-ready install block | Once per machine, as needed |

The `auditor` agent (invoked by `/audit`) reads `.claude/memory/command-log.jsonl` and the live state, then suggests the right one for the moment — you don't need to memorize the table.

---

## Working from a SECOND computer

The environment lives entirely in Git, so the second machine picks up everything with a single clone:

```bash
# one-time on the new machine: WSL2 + Docker Desktop + Claude Code CLI (+ nvm if you use npx skills)
cd ~/projects
git clone https://github.com/<your-username>/my-project.git
cd my-project
docker compose up -d && docker compose exec backend pytest   # make sure it's green
# inside claude: install the plugins (Step 5), then run /doctor + /preflight to verify the environment
```

**Daily ritual on any machine:** start with `/audit` to see what's pending → work through PRs → at the end of the session run `/wrap-up` → commit → `git pull` on the other machine. This way the Claude work history is never lost between computers.

---

## First-prompt template (non-trivial task)

Paste this when starting a non-trivial task so Claude plans before touching code:

```text
Work in Plan Mode.

Task:
[describe the task]

Context:
- Stack: Django 6 / DRF / PostgreSQL 18 / Docker; drf-spectacular for OpenAPI
- Constraints: [what must not change]
- Expected result: [what should work]

Rules:
1. Analyze first; if non-trivial, break into sub-tasks.
2. Do NOT change files until I approve the plan.
3. Minimal impact — don't refactor unrelated code.
4. TDD: failing test first, then minimal code to green.
5. Check current docs via Context7 if an API is uncertain.
6. After implementing, run pytest + ruff and self-review; regenerate `docs/api/openapi.yml`.
```

## How to use (commands · agents · skills)

**Commands** are slash-commands typed inside `claude` (e.g. `/bootstrap my-project`, `/doctor`, `/wrap-up "notes"`, `/review-pr 42`); the full list is the *Commands* subsection above. PR-scoped ones need the `github` MCP + an authenticated `gh`. Every call is logged to `.claude/memory/command-log.jsonl` for `auditor`.

**Agents** you don't call directly — describe the task and the orchestrator routes it through the pipeline in `.claude/rules/workflow.md`. You *can* name one explicitly (`"use ba to draft user stories for X"`). Each agent's triggers live in `.claude/agents/<name>.md`.

**Skills** activate automatically when an agent's task matches a skill's `description:` in `.claude/skills/<name>/SKILL.md` (e.g. `pytest-tdd` for `tester`, `drf-api-design` for `api-architect`). Standalone Anthropic skills (`mcp-builder`, `web-artifacts-builder`) are enabled per machine, not vendored into the repo.

---

## Worked example: one feature, end to end

The pipeline is easiest to grasp on a single feature. Suppose the brief asks for a
**"create resource"** endpoint with deduplication — e.g. importing a record that must
not be inserted twice. You do **not** call agents by hand; you describe the feature and
the orchestrator runs the pipeline. Here is what each phase produces.

**0. You describe the task (Plan Mode for anything non-trivial).**

```text
Work in Plan Mode.

Task: a POST endpoint that imports a resource and refuses to create a duplicate
(returns the existing one instead).

Context:
- Stack: Django 6 / DRF / PostgreSQL 18 / Docker; drf-spectacular for OpenAPI.
- Dedup key: a content hash, unique at the DB level.
- Roles: only authenticated editors may import; read-only users get 403.

Rules: TDD (failing test first), minimal change, then pytest + ruff and regenerate
docs/api/openapi.yml.
```

**1. `ba` — requirements.** Turns the request into user stories + an explicit scope and
edge-case list (happy path, duplicate, unauthorized, malformed input). What's IN and
what's deferred to a later feature.

**2. `api-architect` — the contract.** Locks the endpoint *before* any code: method,
path, request body, response shapes and status codes, permissions, and the serializer
fields with `@extend_schema` annotations. For our example:

```text
POST /api/v1/<resource>/import/
  201 Created  → new record {id, ...}
  200 OK       → duplicate: return the existing record (deduplicated: true)
  400          → validation error (field-keyed)
  401 / 403    → anonymous / read-only role
  Permissions: IsAuthenticated + editor role
```

**3. `tester` — RED.** Writes *failing* DRF `APIClient` tests for the contract, using
**triangulation** (2–3 distinct cases so a hardcoded return can't pass): create-new
(201), duplicate-returns-existing (200), validation (400), anonymous (401), wrong-role
(403). Runs them — all fail because the endpoint doesn't exist yet. This is the expected
RED state. (The `pytest-tdd` skill activates automatically.)

**4. `django-developer` — GREEN.** Adds the model + migration + serializer + thin view +
route — just enough to turn the tests green. Any temporary stub is marked `# STUB:` and
logged in `docs/STUBS.md` so it can't silently reach `main`.

**5. Quality Gate — parallel.** Three independent reviews at once: `reviewer` (code
quality, thin views / fat models, no unlogged stubs), `security-scanner` (401/403, roles,
IDOR, secrets), `dba` (model/migration/indexes, the unique constraint at the DB level,
N+1). Any 🔴/🟡 sends it back to `django-developer`, then the gate re-runs (max 2 cycles).

**6. `docs-writer` — docs + PR.** Regenerates `docs/api/openapi.yml` (the CI drift gate
must pass), updates the app's `README.md` and `docs/WORKLOG.md`, then opens a PR via `gh`
— never a direct commit to `main`.

The result is one reviewed PR for one feature, with tests, docs, and an up-to-date schema.
For the next feature you repeat from step 0. If a feature would touch more than ~3 files,
split it into smaller features and run each through the pipeline separately.
