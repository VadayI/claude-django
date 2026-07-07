# claude-django — full inventory

Complete reference for every agent, rule, skill, command, template, MCP server, and setting. For the project overview, quick start, and pipeline philosophy see [README.md](../../README.md).

---

## Core agents (11) — `.claude/agents/`

| Agent | Purpose | Model |
| --- | --- | --- |
| `ba` | Business analysis, user stories, scope, endpoint draft | opus |
| `api-architect` | REST API contract: **reads** the pinned `docs/api/openapi.yml` and records this PR's routes in `.claude/memory/endpoints.json` — does NOT design the contract | opus |
| `django-developer` | Django/DRF implementation (GREEN phase) | sonnet |
| `tester` | pytest tests, TDD (RED phase) | opus |
| `dba` | Models, migrations, indexes, PostgreSQL optimization, N+1 | sonnet |
| `reviewer` | Code review before PR | opus |
| `security-scanner` | Security audit: authz, OWASP, secrets | opus |
| `debugger` | Bug investigation, root-cause | sonnet |
| `devops` | Docker, deploy to VPS staging, reverse-proxy | sonnet |
| `ci-cd-engineer` | GitHub Actions CI on every PR | sonnet |
| `docs-writer` | `docs/api`, OpenAPI sync, ADR, WORKLOG, PR description | sonnet |

## Optional agents (11) — opt-in

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

## Rules (21) — `.claude/rules/`

`workflow.md` (orchestration & pipeline), `living-plan.md` (living plans — orchestrator seeds `docs/plans/NNNN-*.md` from `templates/plan.md`, agents keep the Status table + Execution log current, changed decisions go to Amendments), `tdd.md` (Red-Green-Refactor), `no-stubs.md` (no stubs/fake data in prod — marker + `docs/STUBS.md` ledger + CI gate), `api-docs.md` (external API contract — pinned `docs/api/openapi.yml` + CI conformance gate), `app-readme.md` (every Django app has a local `README.md` — CI gate), `verification.md` (endpoint verification handoff — auto-generated `docs/verify/<feature>.md` from `.claude/memory/endpoints.json` + OpenAPI, feeds `/verify`), `user-guides.md` (living user-facing guides — `docs/guides/admin.md` + `docs/guides/api-consumer.md`, owned by `guide-writer`, gated by `reviewer`), `preflight.md` (kickoff hard gate — brief/stack/maturity stage/Context7/contract link/GitHub access before any code), `project-maturity.md` (maturity stage — scales pipeline depth and review rigour per stage; never relaxes TDD, CI gates, or contract conformance), `architecture.md` (API-first, structure), `code-style.md` (ruff incl. Google-style docstring `D` rules + 800-line file-size limit, CI gate `scripts/check_file_size.sh`), `simplicity-surgical.md` (Simplicity First + Surgical Changes — minimal code, every diff line traces to the request), `testing.md` (test policy), `git-operations.md` (PR process, no direct commits to main), `docker-commands.md` (environment commands), `serializers-permissions.md` (DRF validation + permission classes, 401/403/IDOR), `migrations-tasks.md` (migration conventions + Celery tasks), `mcp-stack.md` (which MCP tool to use when), `output-language.md` (locks the language agents respond in — copied per project by the language gate), `environment.md` (the expected local environment — source of truth for `/doctor`).

## Skills (12) — `.claude/skills/`

Core: `django-specialist`, `drf-api-design`, `pytest-tdd`, `postgresql-optimization`, `docker-compose-django`, `github-actions-django`.

Review & strategy: `code-reviewer`, `security-reviewer`, `playwright-e2e`, `test-master`, `architecture-designer`, `ddd-strategic-design`.

### Recommended external skills (enable per machine)

These are standalone skills, not vendored into the repo — enable them in your environment (Cowork → "Add", or `/plugin`/skills install) rather than copying their content here:

- `brainstorming` (Superpowers) — structured ideation for ambiguous tasks. Used during Plan Mode by the orchestrator and `ba` / `api-architect` before locking the contract. Highly recommended.
- `writing-plans` (Superpowers) — disciplined plan format (scope · sub-tasks · affected files · risks · open questions). Pairs with the Plan Mode rule in `workflow.md`. Highly recommended.
- `mcp-builder` — building MCP servers (Python/FastMCP or Node SDK). Useful when extending `.mcp.json` with a project-specific server.
- `web-artifacts-builder` — elaborate React/Tailwind/shadcn HTML artifacts. Optional — this repo is backend-only; the interactive API client is Swagger UI / Redoc (drf-spectacular), not a hand-rolled frontend.

> Superpowers marketplace is already enabled via `.claude/settings.json` (`enabledPlugins.superpowers@superpowers-marketplace`), so `brainstorming` and `writing-plans` are available without extra setup — just confirm with `/plugin` if they show as installed.

## Templates — `templates/`

Infrastructure: `docker-compose.yml`, `backend.Dockerfile`, `pyproject.toml` (includes `drf-spectacular`, `schemathesis`, `django-contract-tester`, `djangorestframework-simplejwt` + ruff `FIX`, `D` for Google-style docstrings), `.env.example`, `.github/workflows/backend-ci.yml` (runs ruff + stub gate + contract conformance gate + per-app README gate + file-size gate + pytest), `scripts/check_stubs.sh` (stub gate — fails on unlogged `# STUB:`/`NotImplementedError`), `scripts/pull_contract.sh` (vendors `docs/api/openapi.yml@CONTRACT_VERSION` from `claude-api-contract`), `scripts/check_contract_conformance.sh` (conformance gate — validates the implementation against the pinned external contract), `scripts/check_app_readmes.sh` (per-app README gate — fails if any `backend/apps/<app>/` lacks `README.md`), `scripts/check_file_size.sh` (file-size gate — fails on any non-migration `*.py` over 800 lines).

Docs seeds: `STUBS.md` (copy to `docs/STUBS.md` — the stub ledger), `APP_README.md` (copy to `docs/APP_README.md` — template that `django-developer` copies into each new app), `lessons.md` (copy to `docs/lessons.md` — append-only feedback log, seeded with a first entry), `todo.md` (copy to `docs/todo.md` — cross-session backlog), `HANDOFF.md` (copy to `docs/HANDOFF.md` — multi-session handoff snapshot: current state / last finished / next step / open questions, updated by `/wrap-up`).

Project scaffolding (P1, new): `PROJECT_README.md` (copy to `README.md` of the derived project), `PROJECT.md` (copy to `docs/PROJECT.md` — brief skeleton with **Maturity stage**, **Contract**, `Project`/`Goal`/`Scope`/`Domain`/`Stakeholders`/`Constraints`/`Glossary`/`Open questions` sections, and **Definition of Done (§7)** checklist; filled by `/synthesize-brief` or by hand), `api_INDEX.md` (copy to `docs/api/INDEX.md` — human endpoint index pointing at OpenAPI as the contract), `WORKLOG.md` (copy to `docs/WORKLOG.md` — seeded with an initial "Bootstrapped from claude-django" entry).

Language: `output-language.md` (copy to `.claude/rules/output-language.md` when the user picks a non-English working language; `/bootstrap` and `/set-language` substitute `{LANGUAGE_NATIVE}`).

Verification: `endpoints.json` (copy to `.claude/memory/endpoints.json` — the route registry `api-architect` writes and `/verify` reads), `verify_TEMPLATE.md` (copy to `docs/verify/_TEMPLATE.md` — per-feature verification-guide template that `docs-writer` renders into `docs/verify/<feature>.md`).

Guides: `guides_admin.md` (copy to `docs/guides/admin.md` — operator onboarding: first start, data loading, admin, day-2 ops) and `guides_api_consumer.md` (copy to `docs/guides/api-consumer.md` — integrator onboarding: base URL, auth, first request, conventions); both owned by `guide-writer` per `.claude/rules/user-guides.md`.

All scaffolding templates use `{SLUG}`, `{DATE_ISO}`, `{OWNER}` substitution tokens that `/bootstrap` Step 2 replaces inline. `{TODO}` tokens are intentionally left as visible placeholders for the user to fill later.

## Commands (20) — `.claude/commands/`

Slash-commands that orchestrate agents over the repo / a GitHub PR (PR commands need the `github` MCP from `.mcp.json` + an authenticated `gh`). Every command appends a single line to `.claude/memory/command-log.jsonl` so the `auditor` agent can suggest what to run next.

- `/bootstrap [slug]` — scaffold a Django backend. Front-loaded preflight: refuses to start without Python/`gh`/`docker`/templates and with a working `gh` credential (a fine-grained per-repo token is recommended — ADR `0008`). Two modes: **A. Fresh** (you create the empty GitHub repo by hand; bootstrap links `origin` to it, then scaffolds skeleton, drf-spectacular, first commit + push to main, auto-trigger `backend-ci` so GitHub registers it as a status check, auto branch protection when `admin:repo_hook` is granted — manual GitHub UI fallback otherwise), **B. Resume** (existing repo with partial scaffold — detects each missing piece and ships it as a separate PR). Each major step has a `⏸ Checkpoint — Resume` marker, so failed runs can be re-invoked safely. Run once per new project; can re-run in Mode B to fix gaps.
- `/synthesize-brief` — recursively read `docs/**` (briefs, ТЗ, PDFs, .docx, screenshots) and synthesize a structured `docs/PROJECT.md` via the `brief-synthesizer` agent. Records **maturity stage** (demo/prototype/PoC/MVP/production), **`CONTRACT_VERSION`** (contract link to `claude-api-contract`), and **Definition of Done (§7)** — the brief is incomplete until all three are set. Output via feature branch + PR.
- `/audit [focus]` — workflow audit via the `auditor` agent: reads the command log + live state (git/CI/schema/STUBs) and proposes the next command to run. `focus` ∈ `git|ci|docs|gates` (default: all).
- `/doctor [scope]` — environment configurator: audits the machine against `.claude/rules/environment.md` (system tools · Claude config & access including **`gh` PAT scopes** for `/bootstrap` · project state · git hygiene), classifies the scenario (`no-config` / `fresh` / `existing-incomplete` / `active`), reports a checklist, and proposes fixes — applied only after you confirm. `scope` ∈ `system|claude|project|git` (default: all).
- `/preflight [scope]` — project kickoff hard gate: verifies six build inputs (project brief/description, tech stack, maturity stage, library docs via Context7, API contract link (`CONTRACT_VERSION` + `docs/api/openapi.yml`), GitHub project access) before any feature work. If any input is missing, agents stop instead of guessing. `scope` ∈ `brief|stack|docs|github` (default: all).
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
- `/config-check` — thin wrapper over `/doctor`'s `claude` scope: quick audit of `.claude/settings.json`, `.mcp.json`, MCP servers (github/context7), env keys (set/unset only), and hooks.
- `/plugins` — thin wrapper over `/doctor`'s plugin checks: reports installed vs expected plugins and prints the paste-ready `/plugin install …` block (plugin install is a manual UI step the agent can't run).

## Plugins (recommended baseline)

Auto-enabled per-project via `.claude/settings.json` `enabledPlugins` (ADR `0011`, derived from the maintainer's proven setup): `superpowers@superpowers-marketplace` (brainstorming/writing-plans), `engineering@knowledge-work-plugins`, `playwright@claude-plugins-official` (browser tools used by the `qa` agent / E2E), and `github@claude-plugins-official` + `context7@claude-plugins-official` (which provide the GitHub + Context7 MCP — see below). `claude-hud@claude-hud` is recommended too but stays a **personal/global** HUD install, not committed per-project. `code-review` and `code-simplifier` are intentionally **not** in the baseline — their project-agnostic skills duplicate the project-tuned `reviewer` / `security-scanner` / `django-refactoring-expert` agents, so the canonical paths stay `/review-pr`, `/security-check`, `/simplify`. Install lines are printed by `/bootstrap` Step 6 and `/plugins` (plugin install is a manual UI action).

## MCP servers — official plugins (recommended) or `.mcp.json` (fallback)

`github` (PR data; needs env `GITHUB_PERSONAL_ACCESS_TOKEN`) and `context7` (up-to-date Django/DRF docs; needs `CONTEXT7_API_KEY`) come from the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` in the recommended baseline above. The committed `.mcp.json` + `enabledMcpjsonServers` path is an **optional fallback** — don't enable both for the same MCP (it double-registers). Either way the tool names are identical. Note: `GITHUB_PERSONAL_ACCESS_TOKEN` is required regardless, because the `gh` CLI uses it for push / PR / branch-protection — the plugin only swaps the MCP transport, not gh auth.

### Context7 setup (`CONTEXT7_API_KEY`)

Context7 (by Upstash) serves **current** library documentation to agents, so `api-architect` / `django-developer` verify Django and DRF APIs against today's docs instead of relying on the model's training cutoff. `/preflight` treats Context7 reachability as a **hard gate** (waivable only on explicit override — see `.claude/rules/preflight.md`), so set the key before the first feature.

1. **Get the key.** Sign in at [context7.com](https://context7.com) and create an API key in the dashboard (the free tier is enough for doc lookups).
2. **Export it** in your WSL2 shell — persist it in `~/.bashrc` (or `~/.profile`) so every session and the MCP `npx` process inherit it:

   ```bash
   echo 'export CONTEXT7_API_KEY="ctx7_..."' >> ~/.bashrc
   source ~/.bashrc
   ```

   The MCP is launched as `npx -y @upstash/context7-mcp --api-key ${CONTEXT7_API_KEY}` (see `.mcp.json`), so the variable must be set **before** you start `claude`. Never commit the key — it goes in the environment, not in any tracked file.
3. **Verify.** `[ -n "$CONTEXT7_API_KEY" ] && echo set` should print `set`, and `/doctor` (Claude config scope) reports it as ✅. Because the MCP runs via `npx`, **Node.js 18+ is required** — it already is project-wide (see *Prerequisites*) to install the WSL2-native Claude Code CLI, and Context7 simply reuses the same Node.

## Project settings — `.claude/settings.json`

Per-project Claude Code config: tool permissions (allow `git`/`gh`/`docker`/`npm`, deny direct push to `main` and reading `.env`/secrets), `DJANGO_SETTINGS_MODULE`, auto-enabled plugins (Superpowers, `engineering@knowledge-work-plugins`, plus `playwright`/`github`/`context7` from `claude-plugins-official` — ADR `0011`), and a `Stop` hook that runs `ruff format` + `ruff check --fix` after each turn (silently skips if the `backend` container is down). `model` defaults to `opusplan` — change to taste. (github + context7 now come via plugins, so `enabledMcpjsonServers` is empty by default; `.mcp.json` is the fallback.)
