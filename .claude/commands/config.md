---
model: sonnet
description: "[claude-django] Quick audit of this project's Claude configuration (settings.json, .mcp.json, MCP/plugins) — wrapper over /doctor's claude scope."
---

Quick audit of this project's **Claude configuration** — a thin wrapper over `/doctor`'s `claude` scope (`.claude/settings.json`, `.mcp.json`, MCP servers, env keys, hooks). Use it for a fast "is my Claude setup correct?" check without running the full four-scope environment audit.

## Log

```bash
python scripts/log-cmd.py /config $ARGUMENTS
```

## Behavior

This command does NOT reimplement audit logic. It runs `/doctor` restricted to the **`claude`** scope. Concretely:

1. Run the **Runtime gate** exactly as `/doctor` Step 0.5 (read `.claude/memory/env-detect.json`; hard-STOP on `NO_ENV_DETECT` / `UNSUPPORTED_PLATFORM`). The config audit is meaningless if the runtime is unverified.
2. Execute `/doctor` with scope `claude` (equivalent to the user running `/doctor claude`) — see `.claude/commands/doctor.md` Step 1, "Claude config & access" checks in `@.claude/rules/environment.md` Scope 2:
   - plugins installed (`superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`, `claude-hud`) vs `.claude/settings.json` `enabledPlugins`;
   - MCP for github + context7: provided by the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` (recommended baseline, ADR `0011`); the `.mcp.json` + `enabledMcpjsonServers` path is an optional fallback — flag if BOTH are enabled for the same MCP;
   - MCP env keys set/unset only (`GITHUB_PERSONAL_ACCESS_TOKEN`, `CONTEXT7_API_KEY`) — never print values;
   - `gh` auth status + PAT kind (fine-grained recommended per ADR `0008`);
   - hooks wired in `settings.json` (`SessionStart`, `Stop`).
3. Report the `claude`-scope checklist and propose fixes (propose-then-apply; manual/sensitive items printed for the user). Same remediation policy as `/doctor`.

For plugin install specifically, point the user to `/plugins` (the paste-ready install block).

## Hard limits

Inherit `/doctor`'s hard limits: no `git commit`/`push`, never print secret values, environment/config only (no application source edits).

> Pairs with `/plugins` (plugin install/status) and the full `/doctor` (all four scopes).
