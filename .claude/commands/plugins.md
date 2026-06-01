---
model: sonnet
---

Quick **plugin** setup + status for this project — a thin wrapper over `/doctor`'s plugin checks plus the paste-ready install block from `/bootstrap` Step 6. Plugin installation can NOT be automated by an agent (it runs inside the Claude UI), so this command's job is to (a) report what is installed vs expected and (b) hand you the exact lines to paste.

## Log

```bash
python scripts/log-cmd.py /plugins $ARGUMENTS
```

## Behavior

1. **Runtime gate** as `/doctor` Step 0.5 (read `.claude/memory/env-detect.json`; hard-STOP on `NO_ENV_DETECT` / `UNSUPPORTED_PLATFORM`).
2. **Status** — run the plugin portion of `/doctor`'s `claude` scope: compare installed plugins against the expected set from `@.claude/rules/environment.md` Scope 2 and `.claude/settings.json` `enabledPlugins`:
   - `superpowers@superpowers-marketplace`
   - `engineering@knowledge-work-plugins`
   - `playwright@claude-plugins-official`
   - `github@claude-plugins-official`
   - `context7@claude-plugins-official`
   - `claude-hud@claude-hud` (personal/global — recommended but not in committed `enabledPlugins`)
   Report each as ✅ installed / ❌ missing.
3. **Paste-ready install block** — for any missing plugin (or always, if the user asks), print the lines to paste inside `claude` (identical to `/bootstrap` Step 6):
   ```
   /plugin marketplace add obra/superpowers-marketplace
   /plugin install superpowers@superpowers-marketplace
   /plugin install engineering@knowledge-work-plugins
   /plugin install playwright@claude-plugins-official
   /plugin install github@claude-plugins-official
   /plugin install context7@claude-plugins-official
   /plugin marketplace add jarrodwatts/claude-hud
   /plugin install claude-hud
   /claude-hud:setup
   ```
   Note clearly: these are typed by the **user** in the Claude UI — the agent cannot run them.

## Hard limits

Inherit `/doctor`'s hard limits: no `git commit`/`push`, never print secret values, no application source edits. Never claim a plugin was installed by the agent — installation is a manual UI action.

> Pairs with `/config` (settings/MCP audit) and the full `/doctor`.
