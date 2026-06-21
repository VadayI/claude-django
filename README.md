# Claude Code configuration for Django REST Framework projects

A ready-made Claude Code configuration for **Django REST Framework** backend projects with **Test-Driven Development** discipline, an **API-first (contract-first)** process, an **external API contract** (authored in `claude-api-contract`, consumed here and validated by a CI conformance gate), and work done **exclusively through Pull Requests**. A real production frontend, if needed, lives in a separate repository. This config turns Claude Code into a development team: an orchestrator delegates tasks to specialized agents through a clear pipeline.

**Stack:** Python 3.13 · Django 6 · Django REST Framework · PostgreSQL 18 · Docker · pytest + pytest-django · ruff · drf-spectacular (Swagger UI) · schemathesis + django-contract-tester (contract conformance) · djangorestframework-simplejwt (auth). REST API contract authored externally in `claude-api-contract`, pinned via `CONTRACT_VERSION`.
**Environment:** native Windows (PowerShell / Git Bash) or WSL2, + Docker Desktop · Linux / macOS · Staging — Debian VPS · GitHub as the source of truth

---

## Where this runs (supported runtime)

This config runs in **Claude Code CLI** (the terminal `claude` command) on **native Windows** (PowerShell or Git Bash), **WSL2 Ubuntu**, **Linux**, or **macOS**. The per-session hooks are cross-platform Python (ADR `0022`, which amends ADR `0005`), so `platform_supported` is `true` on all four.

**Not supported:** Claude Desktop / Cowork / Code mode and the Claude API/SDK — these do not run the `SessionStart` hook, so `.claude/memory/env-detect.json` is never written and the gates cannot evaluate. On native Windows, ensure `python` resolves on PATH (not the Microsoft Store alias); Docker Desktop still needs a WSL2 or Hyper-V backend.

Startup and `/doctor` hard-stops (e.g. `python` not on PATH, missing `gh` or PAT) and their fixes live in **[Troubleshooting](#troubleshooting-startup--doctor-hard-stops)** below.

---

## Using Claude Code CLI (the only supported runner)

Everything here — agents, slash-commands, environment gates — runs in **Claude Code CLI**, started by typing `claude`. On Windows that means **PowerShell or Git Bash** (native) or **WSL2 Ubuntu** — all supported since ADR `0022`; not the Desktop app.

**1. Install the CLI** (one-time). On **native Windows**, use the Claude Code Windows installer (or `npm install -g @anthropic-ai/claude-code`) and confirm `claude --version` works in PowerShell or Git Bash. On **WSL2 / Linux / macOS**, install inside that shell:

```bash
node --version                       # need Node 18+ (install via nvm if missing)
npm install -g @anthropic-ai/claude-code
which claude                         # MUST be /home/... or /usr/...  — NOT /mnt/c/...
```

> **WSL2 only:** installing the CLI on the Windows side does **not** give you a WSL2 `claude`; if `which claude` shows `/mnt/c/...` the Windows binary is shadowing it on PATH — fix per [Troubleshooting](#troubleshooting-startup--doctor-hard-stops), or run `bash scripts/setup-wsl.sh` (whole toolchain: Python / Node / `claude` / `gh` + PATH fix; idempotent, never touches secrets or git). On **native Windows** there is no shadowing — a `C:\...\claude.exe` on PATH is the correct runner.

**2. Where to put the project.** Working from `/mnt/c` or `/mnt/d` (a Windows drive) is **fully supported** (ADR `0009`); `/doctor` won't ask you to move it. The only caveats are slower Docker bind-mounts and occasional CRLF / `git index.lock` quirks (run `git` from the host shell). `~/projects/<slug>` in the WSL2 FS is optional — for faster bind-mounts only.

**3. Launch and verify the runner.** From the project root, launch `claude` — on native Windows that is `claude` in PowerShell or Git Bash; on WSL2 / Linux / macOS it is `claude` in your shell. Both are correct (ADR `0022`). On start the `SessionStart` hook runs `python scripts/session-start.py` and writes `.claude/memory/env-detect.json` with `platform_supported: true` and the detected `platform` / `shell` — exactly what `/doctor` needs to pass the platform gate. (Backslash paths in the banner are normal on native Windows and no longer signal a "wrong runner".)

> Run shell fixes in the **bash terminal**, not Claude's `❯` prompt. When `/doctor` says to run `npm install …`, that goes in the terminal — pasting it into the `❯` chat just sends Claude a message.

**4. Drive the work with slash-commands.** `/doctor` first on a new machine (audits the environment, proposes fixes); `/preflight` before the first feature (brief, stack, **maturity stage**, Context7, **contract link**, GitHub access). Then describe a feature in plain language and the orchestrator runs `ba → api-architect → tester(RED) → django-developer(GREEN) → Quality Gate → docs-writer`. End each session with `/wrap-up`, commit, and `git pull` on the other machine.

**5. GitHub access** — create the repo by hand + a fine-grained per-repo token (ADR `0008`). Create an **empty** repo at https://github.com/new (no README/.gitignore/license), then mint a **fine-grained token scoped to just that repo** (`/bootstrap` and `/doctor` print a ready-made template URL):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_xxxxxxxx
```

Minimal permissions: **Contents** RW, **Metadata** RO (auto), **Pull requests** RW, **Workflows** RW, **Administration** RW (the last enables auto branch protection; omit it and protection becomes a manual UI step). A classic PAT works too but grants whole-account access.

Short version: **install the CLI (native Windows or WSL2) → seed the config → `claude` → `/doctor` → `/bootstrap` → `/preflight` → first feature.** If you must use Claude Desktop, treat it as an editor / chat companion **after** running these from the CLI.

---

## Troubleshooting startup & /doctor hard-stops

**The golden path (memorize this):** *install the CLI (native Windows installer / npm, or inside WSL2) → `claude --version` works → launch `claude` from the project → `/doctor` → `/bootstrap`.* Almost every "it doesn't work" is one of the runner / PAT issues below. `/doctor` is doing its job when it HARD-STOPs — the message tells you exactly which gate failed; match the symptom here.

| Symptom (what you see) | What it actually means | Fix (run in a **bash shell**, not the `❯` prompt) |
|---|---|---|
| `🔴 UNSUPPORTED_PLATFORM` (now rare) | `platform_supported: false` only occurs on a platform that is **not** Windows, macOS, Linux, or WSL2 — ADR `0022` made native Windows a supported runner, so all four pass. | Note the detected `platform` in `env-detect.json`; if it is one of the supported four, re-run `python scripts/detect-env.py`. `wrong_runner_suspected` is retired. |
| `🔴 NO_ENV_DETECT` — `.claude/memory/env-detect.json` is missing | The `SessionStart` hook didn't run — usually `scripts/` wasn't copied during Quick start, or Python isn't on PATH. The hook **fails silently** without `scripts/detect-env.py`. | Confirm `scripts/detect-env.py` exists in the project; run `python scripts/detect-env.py` once by hand. If it errors, fix the cause (install Python 3.10+). **Never hand-write this file** — fabricated values bypass the safety gates. |
| `🔴 NO_PYTHON_OR_HOOK` — only `python3` exists, no `python` | The hook calls `python`; Ubuntu ships it as `python3`. | `sudo apt install -y python-is-python3`, then reopen `claude`. |
| `✗ REPO_NOT_FOUND` — `/bootstrap` can't see the repo | Per ADR `0008` you create the GitHub repo **by hand**; either the empty repo wasn't created or your fine-grained token isn't scoped to it. (`FINE_GRAINED_PAT_NOT_SUPPORTED` is retired — fine-grained tokens are now the recommended credential.) | Create the empty repo at https://github.com/new, mint a fine-grained token via the template URL `/bootstrap` prints (Only select repositories → your repo; Contents/Pull requests/Workflows/Administration = RW), `export GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_…`, re-run. |
| `🔴 NO_GH_SCOPES` — classic PAT missing scopes | **Classic PATs only** — fine-grained tokens are not scope-gated (ADR `0008`). The classic token lacks `repo`/`workflow`. | `gh auth refresh -s repo,workflow,admin:repo_hook` — or better, switch to a fine-grained per-repo token (see the GitHub access step above). |
| You pasted a shell command (e.g. `npm install …`) and **nothing changed** | You typed it into Claude's `❯` chat prompt, not the terminal — Claude just replied with a note. | `/exit` (or open a second WSL2 tab), run the command in **bash**, then relaunch `claude`. |
| PowerShell: `wsl2: The term 'wsl2' is not recognized` | The command is `wsl`, not `wsl2`. | `wsl` (or `wsl -d Ubuntu`) to enter WSL2 from PowerShell. |
| `which claude` stays `/mnt/c/...` even after the `$(npm config get prefix)/bin` PATH fix | Your `npm` is the **Windows** npm (Linux `node` is present but Linux `npm` is missing), so `npm install -g` put `claude` in the Windows prefix — the PATH trick can't help because that prefix is itself a `C:\...` path. | Confirm with `which node npm`. Let `nvm` own node+npm in WSL2: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh \| bash` → `nvm install --lts` → `npm install -g @anthropic-ai/claude-code`; `which node npm claude` must all be `/home/…`. Or just run `bash scripts/setup-wsl.sh`. |
| Tests slow, `rm` fails, CRLF↔LF flips, `git index.lock` — project under `/mnt/c` or `/mnt/d` | The repo lives on a Windows drive (9p mount). **Fully supported (ADR `0009`)** — these are inherent `/mnt` caveats, not an error, and `/doctor` won't ask you to move. | No action required. Run `git` from the host shell (PowerShell/Git Bash) to avoid `index.lock`. Moving to `~/projects/<slug>` is optional (faster bind-mounts), never required. |

After applying a fix, just re-run `/doctor` — the `SessionStart` hook rewrites `env-detect.json` on each launch, so a corrected runner/PAT shows up immediately. Full runtime guidance (native Windows vs WSL2): `.claude/rules/environment.md` → *"Windows: native or WSL2"*.

---

## Process philosophy

1. **API-first (contract-first).** The REST API contract is authored externally in `claude-api-contract` and pinned via `CONTRACT_VERSION`; pull it, then build the backend test-first against it (models → serializers → views → routes → permissions → tests → docs). Everything else hangs off the contract.
2. **TDD in Python.** No production code without a failing test first. Red → Green → Refactor cycle.
3. **External REST API contract.** The canonical OpenAPI schema is authored in `claude-api-contract` and pinned via `CONTRACT_VERSION`; `scripts/pull_contract.sh` vendors it to `docs/api/openapi.yml`. A CI **conformance gate** (`scripts/check_contract_conformance.sh` — schemathesis + django-contract-tester) validates the implementation against the pinned contract, so **the backend can't drift from the published API** (it never regenerates the canon). Swagger UI (`/api/schema/swagger/`) and Redoc (`/api/schema/redoc/`) are the interactive client. A full production frontend, if needed, lives in a **separate repository**.
4. **Pull Requests only.** Branch → PR → review → merge. Direct commits to `main` are forbidden (branch protection).
5. **Context in Git.** Claude's work history (`CLAUDE.md`, `.claude/memory/`, `docs/WORKLOG.md`, ADRs) is committed to the repo — so it stays in sync between the two machines via a plain `git pull`.
6. **Maturity-scaled process.** Each project declares a maturity stage (demo / prototype / PoC / MVP / production) in `docs/PROJECT.md` that scales pipeline depth and review rigour — never relaxing TDD, the CI gates, or contract conformance (`.claude/rules/project-maturity.md`). The brief also records a **Definition of Done** (§​7) — the gate checklist a feature must pass before merging.

---

## What's inside

- **Agents (22)** — 11 core (`ba`, `api-architect`, `django-developer`, `tester`, `dba`, `reviewer`, `security-scanner`, `debugger`, `devops`, `ci-cd-engineer`, `docs-writer`) + 11 optional opt-in (`auditor`, `brief-synthesizer`, `qa`, `celery-specialist`, `integration-architect`, `devil`, `django-refactoring-expert`, `domain-architect`, `guide-writer`, `code-structure-auditor`, `template-sync`)
- **Rules (21)** — `workflow.md` (pipeline), `tdd.md`, `no-stubs.md`, `api-docs.md`, `project-maturity.md` (maturity stage scales process depth; never relaxes TDD/gates), `preflight.md` (6-blocker kickoff gate), `architecture.md`, `code-style.md`, `simplicity-surgical.md`, `testing.md`, `git-operations.md`, `docker-commands.md`, `serializers-permissions.md`, `migrations-tasks.md`, `mcp-stack.md`, `output-language.md`, `environment.md`, and 4 more.
- **Skills (12)** — 6 core + 6 review/strategy in `.claude/skills/`.
- **Commands (20)** — `/bootstrap`, `/doctor`, `/preflight`, `/audit`, `/wrap-up`, `/synthesize-brief`, `/handoff`, `/verify`, `/guides`, and 11 more in `.claude/commands/`.
- **Templates** — Docker, CI, pyproject.toml with linting + test deps, docs seeds, scaffolding with `{SLUG}` tokens.
- **Plugins** — `superpowers`, `engineering`, `playwright`, `github`, `context7` (auto-enabled via `.claude/settings.json`).
- **MCP servers** — `github` (PR data) + `context7` (up-to-date Django/DRF docs), provided by the official plugins.
- **Project settings** — `.claude/settings.json`: tool permissions, `DJANGO_SETTINGS_MODULE`, plugin baseline, `Stop` hook (ruff after each turn).

> Full inventory (every agent, rule, skill, command, template, MCP server, setting) → [docs/reference/inventory.md](docs/reference/inventory.md).

### Development pipeline

```
Feature:   ba → api-architect → tester(RED) → django-developer(GREEN)
              → [reviewer | security-scanner | dba] → docs-writer (INDEX + verify, contract-pinned)
Bug fix:   debugger → tester(regression) → django-developer → reviewer
CI/CD:     ci-cd-engineer / devops → [reviewer | security-scanner]
```

---

## Prerequisites

- [Claude Code](https://code.claude.com) CLI
- **Python 3.10+ on PATH as `python`** (hard requirement; the `SessionStart` hook runs `scripts/detect-env.py`). On Ubuntu install `python-is-python3` if only `python3` is present.
- Docker Desktop (WSL2 or Hyper-V backend)
- **Shell:** PowerShell or Git Bash on native Windows, bash in WSL2 Ubuntu, or bash/zsh on Linux/macOS — all supported (ADR `0022`).
- WSL2 (Ubuntu) — **optional on Windows** (one of two runners; the other is native PowerShell / Git Bash). Docker Desktop still needs a WSL2 or Hyper-V backend. The project can live on your Windows drive (`/mnt/...` from WSL2, `D:\...` natively — fully supported, ADR `0009`); `~/projects/<slug>` in the WSL2 FS is optional for faster bind-mounts
- **Node.js 18+ (via `nvm`; the native Windows installer needs none)** — needed to install the Claude Code CLI via `npm install -g @anthropic-ai/claude-code` and for `npx`-based skills (e.g. the Context7 MCP). `/doctor` reports `NO_NODE` if it is missing or below 18
- A GitHub account

## Quick start (attach the config to an existing project)

> **First time on this Windows machine?** Two options. **(a) Native Windows:** install Python 3.10+ (make sure `python --version` works — not the Microsoft Store alias), Node 18+ (only if installing the CLI via npm), `git`, `gh`, and Docker Desktop; run everything from PowerShell or Git Bash. **(b) WSL2:** from PowerShell `wsl --install -d Ubuntu` then `wsl --set-default Ubuntu`, set a Unix user/password, and install the toolchain: `sudo apt update && sudo apt install -y git curl gh python-is-python3 python3-pip` (verify `ID=ubuntu` in `/etc/os-release`, 24.04+).
>
> Then open your shell at the project: PowerShell or Git Bash at `D:\...` (native), or `wsl` and `cd /mnt/d/...` (WSL2) — a Windows-drive path is fine either way (ADR `0009`). On WSL2 the one thing that matters is `which claude` resolving to `/home/...` (not `/mnt/c/...`); on native Windows a `claude.exe` on PATH is correct.

**Fastest — one-line seed.** From the root of your project folder in **Git Bash or WSL2**, this clones the template and copies the config in one go (idempotent; refuses to clobber an already-seeded folder unless `--force`):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/VadayI/claude-django/main/scripts/install.sh)
# optional args:  install.sh [TARGET_DIR] [--ref GIT_REF] [--url FORK_URL] [--force]
```

**On a corporate network (Git Bash) and hitting `CRYPT_E_NO_REVOCATION_CHECK`?** schannel can't reach the revocation server. Turn off revocation checking for **both** git and curl — the certificate is still validated, only the CRL/OCSP step is skipped (`git config` covers the `git clone` inside `install.sh`; the `curl` flag covers fetching the script):

```bash
git config --global http.schannelCheckRevoke false
bash <(curl -fsSL --ssl-no-revoke https://raw.githubusercontent.com/VadayI/claude-django/main/scripts/install.sh)
```

If deep TLS inspection still blocks it, seed from **WSL2** instead (it uses OpenSSL, not schannel): `wsl` → `cd /mnt/d/...your-project` → run the plain one-liner above (no flag) → `exit`, then launch `claude` natively in Git Bash / PowerShell.

Then launch `claude` → `/doctor` → `/bootstrap`. To upgrade an *already-seeded* project use `/update-from-template` instead (it preserves your edits, ADR `0014`).

**Manual equivalent** (what `install.sh` does, if you prefer to run it by hand):

```bash
# Git Bash or WSL2, from the root of your project (a Windows-drive path is fine — ADR 0009)
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

# WSL2 only: confirm `claude` is the Linux-native CLI, not the Windows `claude.exe` (no shadowing on native Windows).
which claude    # WSL2/Linux/macOS: expect /home/... or /usr/...  (if /mnt/c/..., see step 1 / step 5 above)
```

Then install the plugins (see below) and adjust `CLAUDE.md` for the project name. Then run **`/doctor`** inside `claude` — it detects the scenario and recommends the next command. If `/doctor` HARD-STOPs, jump to **[Troubleshooting startup](#troubleshooting-startup--doctor-hard-stops)** below.

---

## Step-by-step: a NEW project from scratch

1. **Quick start** (above) — copy `.claude/`, `CLAUDE.md`, `.mcp.json`, `.gitignore`, `scripts/`, `templates/` into the new project folder (a Windows-drive path like `D:\...` is fine; `~/projects/<slug>` in WSL2 is optional).
2. `claude` → `/doctor` — verifies environment and detects scenario `fresh`; recommends `/bootstrap`.
3. `claude` → `/bootstrap` — runs the hard preflight (Python / `gh` / `docker` / templates + GitHub access), then scaffolds the project: links `origin` to the empty repo you created (Mode A never runs `gh repo create`), builds the skeleton + drf-spectacular config, brings Docker up, migrates, pulls the external contract to `docs/api/openapi.yml` (when published), makes the first commit + push to `main`, and enables branch protection. Each step has a `⏸ Checkpoint — Resume` marker; Mode B resumes a failed run. This is the only command that direct-pushes to `main` (documented exception in `.claude/rules/git-operations.md`). Full behaviour: the `/bootstrap` entry under *Commands* above.
4. (manual) Drop your input documents into `docs/` — briefs, ТЗ, PDFs, .docx, screenshots — keeping `docs/api/`, `docs/decisions/`, `docs/plans/` for their existing purpose.
5. `claude` → `/synthesize-brief` — recursively reads `docs/**` (excluding service folders), delegates to `brief-synthesizer`, writes `docs/PROJECT.md` via feature branch + PR. Records **maturity stage**, **`CONTRACT_VERSION`** (contract link), and **Definition of Done (§7)** — the brief is incomplete until all three are set.
6. `claude` → `/doctor` → `/preflight` — re-verify environment and build inputs (six blockers: brief, stack, maturity stage, Context7, contract link, GitHub access).
7. First feature through the standard pipeline (`ba → api-architect → ...`).

For an existing project from a second machine: skip step 1 (clone instead), run `/doctor` — it will detect `active` or `existing-incomplete` and tell you whether to run `/bootstrap` in resume mode.

---

## Updating an existing project from the template

A project bootstrapped from `claude-django` carries a **pinned copy** of the config from the moment it was forked (ADR `0002`) — there is no automatic upgrade channel. When the template gains new agents, rules, commands, skills, or CI gates, pull them in deliberately with **`/update-from-template`** — by default it syncs from the canonical upstream **`https://github.com/VadayI/claude-django`**:

```bash
# Git Bash or WSL2, from the root of the DERIVED project
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
| `/config-check` | Quick check that `.claude/settings.json` / `.mcp.json` / MCP keys / hooks are correct | As needed |
| `/plugins` | Check installed vs expected plugins; get the paste-ready install block | Once per machine, as needed |

The `auditor` agent (invoked by `/audit`) reads `.claude/memory/command-log.jsonl` and the live state, then suggests the right one for the moment — you don't need to memorize the table.

---

## Working from a SECOND computer

The environment lives entirely in Git, so the second machine picks up everything with a single clone:

```bash
# one-time on the new machine: Claude Code CLI + Docker Desktop (native Windows, or WSL2) (+ nvm if you use npx skills)
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
- Stack: Django 6 / DRF / PostgreSQL 18 / Docker; drf-spectacular for Swagger UI; REST contract consumed from claude-api-contract
- Constraints: [what must not change]
- Expected result: [what should work]

Rules:
1. Analyze first; if non-trivial, break into sub-tasks.
2. Do NOT change files until I approve the plan.
3. Minimal impact — don't refactor unrelated code.
4. TDD: failing test first, then minimal code to green.
5. Check current docs via Context7 if an API is uncertain.
6. After implementing, run pytest + ruff and self-review; validate against the pinned contract (`bash scripts/check_contract_conformance.sh`).
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
- Stack: Django 6 / DRF / PostgreSQL 18 / Docker; drf-spectacular for Swagger UI; REST contract consumed from claude-api-contract.
- Dedup key: a content hash, unique at the DB level.
- Roles: only authenticated editors may import; read-only users get 403.

Rules: TDD (failing test first), minimal change, then pytest + ruff and validate
against the pinned contract (`bash scripts/check_contract_conformance.sh`).
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

**6. `docs-writer` — docs + PR.** Updates `docs/api/INDEX.md` (pointing at the external
contract + `CONTRACT_VERSION`; the CI conformance gate must pass), the app's `README.md`
and `docs/WORKLOG.md`, then opens a PR via `gh` — never a direct commit to `main`.

The result is one reviewed PR for one feature, with tests, docs, and an up-to-date schema.
For the next feature you repeat from step 0. If a feature would touch more than ~3 files,
split it into smaller features and run each through the pipeline separately.
