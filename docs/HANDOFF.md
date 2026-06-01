# HANDOFF — claude-django

> Rolling snapshot of the template-config repo. Read first when joining; update at session end.
>
> Maintainer · Last touched: 2026-06-01

## Current state

On `main`, tip `a9185b3 feat(bootstrap): manual repo + fine-grained per-repo PAT (ADR 0008)` (pushed). **Working tree has an uncommitted batch — commit it next (see Next step):** eight files — `.claude/commands/bootstrap.md`, `.claude/commands/doctor.md`, `.claude/rules/environment.md`, `.claude/rules/docker-commands.md`, `README.md`, the new `docs/decisions/0009-mnt-working-dir-supported.md`, plus the session-end `docs/WORKLOG.md` / `docs/HANDOFF.md`.

## Last finished

This session (2026-06-01) shipped two related policy reversals plus earlier onboarding/Node work:

- **ADR 0008 — manual repo + fine-grained per-repo PAT (committed `a9185b3`).** `/bootstrap` no longer creates the repo or wants a classic PAT; the user creates the empty repo by hand and `/bootstrap`+`/doctor` emit a per-repo fine-grained token template URL (`contents`/`pull_requests`/`workflows`/`administration` = RW). `FINE_GRAINED_PAT_NOT_SUPPORTED` retired; capability verified by `gh repo view` + per-operation errors.
- **ADR 0009 — `/mnt` working dir fully supported (pending commit).** Stopped recommending moving the project off `/mnt` into `~/projects`; `/doctor` reports `/mnt` as ✅, one neutral caveats note remains. Removed all "Do NOT work from /mnt" language.
- **Free-plan branch protection (pending commit).** Verified: branch protection + rulesets are unavailable for **private** repos on the free plan (public free, private needs Pro/Team). Step 5 403 handler now separates plan-limit from token-permission causes; "skip & keep private" is a documented choice; `/doctor` no longer flags absent protection on free+private as incomplete.

Earlier in the session (already committed): onboarding clarity (startup happy-path, Troubleshooting table, npm-shadow trap) + the mandatory Node 18 gate (`node_supported`, schema v5, `NO_NODE`).

All writes via `python pathlib` + `assert count==1` anchors + tail/line verification (Edit/Write truncate file tails on the `/mnt` mount; rebuild from `git show HEAD` when it happens).

## In progress

- (nothing in flight — no open feature branches)

## Next step

Commit the pending batch on the **host (PowerShell)**, direct to `main` per template-repo policy. Clear the stale lock first:

```powershell
cd D:\Dev\My\claude-django
Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
git add .claude/commands/bootstrap.md .claude/commands/doctor.md .claude/rules/environment.md .claude/rules/docker-commands.md README.md docs/decisions/0009-mnt-working-dir-supported.md docs/WORKLOG.md docs/HANDOFF.md
git commit -m "docs(env): /mnt working dir fully supported (ADR 0009) + free-plan branch-protection 403 handling"
git push origin main
```

(WSL2 bash equivalent: `rm -f .git/index.lock`, same `git add` on one line, then commit/push.)

## Open questions

- [ ] When a project upgrades to Pro/Team, prefer **rulesets** over classic branch protection in `/bootstrap` Step 5? (Rulesets are the newer mechanism; both are free-plan-blocked on private repos.)
- [ ] Should `detect-env.py` record resolved tool paths so `/doctor` can flag a Windows-npm shadow automatically? (Limited value — in the wrong-runner state the hook runs under Windows-Python.)
- [ ] Pre-commit/CI guard that fails on a truncated file tail (has bitten files across multiple sessions)?
- [ ] `/handoff --append` (snapshot history) vs the current overwrite model — still open.

## Environment notes

- **`/mnt/c`/`/mnt/d` (Windows drive) is a fully supported working dir** (ADR `0009`) — `/doctor` will not ask you to move. Caveats: slower Docker bind-mounts, CRLF, `git index.lock` on 9p (run git from the host shell). `~/projects/<slug>` is optional, never required.
- **Branch protection needs a public repo or GitHub Pro/Team** — on a free plan + private repo the API returns 403; absent protection there is expected, not a failure.
- **GitHub access = fine-grained per-repo token** (ADR `0008`); the repo is created by hand. `/bootstrap`+`/doctor` print the token template URL. Classic PATs still work but are broader than needed.
- **Node 18+ is a hard requirement** (`node_supported`, schema v5). A Linux `node` does not guarantee a Linux `npm` — check `which node npm`; fix a Windows-npm shadow with `nvm install --lts` or `bash scripts/setup-wsl.sh`.
- **Cowork on the `/mnt` mount: `Edit`/`Write` MCP tools silently truncate file tails.** Use `python pathlib.write_text()` via bash and verify with `tail -c` + line-count-vs-HEAD. Editing under `.claude/` is also blocked for the Edit tool — go through bash + python.
- Container/mount `git` is unreliable on the Windows-written index (`index.lock` "Operation not permitted"); do all `git add`/`commit`/`push` in PowerShell on the host. `git status`/`diff`/`log`/`show` read fine from the sandbox.
- Direct commits to `main` are allowed in THIS repo per template-repo policy. PR flow applies only to derived projects.

---

> Update cadence: at session end, by hand or via `/handoff`. `docs/WORKLOG.md` is the canonical chronicle; this file is the cursor.
