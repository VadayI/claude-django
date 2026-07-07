# MCP Stack — Tool Usage Guide

Configured in `.mcp.json`, enabled in `.claude/settings.json` (`enabledMcpjsonServers`). Set the env vars before use.

> **Recommended mechanism (ADR `0011`):** `github` and `context7` are provided by the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` (auto-enabled via `enabledPlugins`). The `.mcp.json` + `enabledMcpjsonServers` setup below is the **optional committed fallback** — do NOT enable both at once (the same MCP would be registered twice). Either way the **tool names are identical**, so everything below applies unchanged. Tokens are still required: `GITHUB_PERSONAL_ACCESS_TOKEN` (also used by the `gh` CLI) and `CONTEXT7_API_KEY`.

## GitHub MCP (`github`) — env `GITHUB_PERSONAL_ACCESS_TOKEN`

PR data and review automation. Prefer these over scraping or `curl`.

| Tool | When to use |
|------|-------------|
| `pull_request_read` | Read PR details (review, fix-ci) |
| `list_pull_requests` | List open PRs |
| `pull_request_review_write` | Create/submit a review |
| `add_comment_to_pending_review` | Post inline review comments |
| `create_pull_request` | Open a PR (`docs-writer` only) |

For GitHub Actions data (run logs, job status) use the `gh` CLI (`gh run list/view`, `gh pr checks`), not the MCP.

## Context7 (`context7`) — env `CONTEXT7_API_KEY`

Up-to-date library docs.

| Tool | When to use |
|------|-------------|
| `resolve-library-id` | Find the library id first |
| `get-library-docs` | Current docs for Django, DRF, PostgreSQL when knowledge may be stale |

## Notes

- Web/CI data restrictions: do not bypass blocked fetches via `curl`/scripts.
- Secrets (tokens/keys) only via env — never commit them.
- Vet third-party MCP servers/skills before enabling: check what they run, where (local `npx`/Docker), and what they can access (keys, repo, filesystem). Prefer audited, well-known sources.

## Binds these agents (referenced from each agent's prompt)

- `docs-writer` — opens the PR (`create_pull_request` / `gh pr create`).
- `reviewer` — reads PR details via `pull_request_read` at the Quality Gate.
- `api-architect`, `django-developer` — verify current Django/DRF/PostgreSQL APIs via context7 (`resolve-library-id` → `get-library-docs`) before designing/implementing.

> Loaded per-agent via `@.claude/rules/mcp-stack.md` in each agent's prompt, not via the global CLAUDE.md import block (the orchestrator rarely calls MCP directly).
<!-- Last reviewed/updated: 2026-06-01 (github/context7 via official plugins; .mcp.json is fallback — ADR 0011) -->
