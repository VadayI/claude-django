# Project kickoff preflight (hard gate)

Before agents start work on a (new) project — and before the first feature pipeline — verify that the inputs and access needed to build correctly are present. This is a **hard gate**: if a critical item is missing, agents do NOT start coding; the orchestrator stops and either asks the user or fixes access. Runs automatically at project kickoff and on demand via `/preflight`.

## What to verify (all CRITICAL)

1. **Project brief / description.** A clear statement of what we are building: goals, scope, domain, key requirements. Source: `docs/PROJECT.md`, a README brief, or a description the user provided. If absent or vague → STOP and ask the user for a brief — `ba` cannot write meaningful user stories without it.
2. **Tech stack.** The stack is declared (CLAUDE.md / README: Django 6 · DRF · PostgreSQL 18 · Docker) and dependencies are resolvable (`backend/pyproject.toml` present; versions consistent). If undeclared or contradictory → STOP and confirm with the user.
3. **Library docs access — Context7.** The `context7` MCP is reachable so agents can check current Django/DRF APIs before implementing (`resolve-library-id` works; `CONTEXT7_API_KEY` set). If down → STOP, or proceed only on explicit user override (noting that APIs will be unverified against current docs).
4. **GitHub project access.** `gh auth status` is authenticated AND the project repo is reachable (`gh repo view`), so PRs, CI, and history work. `github` MCP env (`GITHUB_PERSONAL_ACCESS_TOKEN`) set. If no access → STOP.
5. **Maturity stage.** `docs/PROJECT.md` declares a stage (`demo / prototype / PoC / MVP / production`). If absent → ask the user via `AskUserQuestion` (options: demo / prototype / PoC / MVP / production / other) before dispatching `ba` — the pipeline depth depends on it (`.claude/rules/project-maturity.md`). "Other" is treated as MVP until clarified.
6. **API contract link.** `CONTRACT_VERSION` is set in `.env` to a specific `claude-api-contract` tag (e.g. `v0.2.0`) AND `docs/api/openapi.yml` exists and is non-empty. Check: `grep -q '^CONTRACT_VERSION=' .env && test -s docs/api/openapi.yml`. If absent → STOP; run `bash scripts/pull_contract.sh` after setting the version. Without a contract pin, `api-architect` cannot read the schema, `tester` cannot write conformance tests, and CI will fail.

## Gate behavior

- All six are blockers. If any is ❌ → report the readiness checklist and STOP before dispatching `ba` / the feature pipeline.
- Context7 (item 3) may be waived only on **explicit** user override; record that implementation will rely on the agent's training knowledge (knowledge cutoff), not current docs.
- Contract pin (item 6) may be waived only if the project is in `demo` or `prototype` stage AND the user explicitly confirms no conformance testing is needed for this session.
- Never start writing code, schemas, or migrations while a CRITICAL item is ❌.

## Who runs it

- The **orchestrator** runs the preflight at project kickoff (the first feature on a fresh project), delegating access checks (Context7, GitHub, stack deps) to `devops` and brief/stack comprehension to `ba`.
- `ba` confirms it has a usable brief + declared stack + maturity stage BEFORE producing user stories.
- The `/preflight` command runs the same check on demand.

## Relation to `/doctor`

`/doctor` checks the **environment** (tools, services, git hygiene). Preflight checks the **inputs to build** (brief, stack, docs/GitHub access, maturity stage, contract pin). On a fresh machine run `/doctor` first, then preflight before the first feature.

<!-- Last reviewed/updated: 2026-06-08 -->
