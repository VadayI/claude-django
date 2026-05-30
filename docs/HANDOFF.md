# HANDOFF — claude-django

> Rolling snapshot of the template-config repo. Read first when joining; update at session end.
>
> Owner: [@VadayI](https://github.com/VadayI) · Last touched: 2026-05-30

## Current state

On `main`, working tree clean, in sync with `origin/main`. Last commit: `fc975bb docs(bootstrap): add read:org to PAT URLs + clarify env-var vs gh-auth-login paths`. The four P0-P3 batches AND a follow-up `read:org` hotfix all landed in this session — five separate commits in `main`:

- `8cdb6a6` — P0 (preflight robustness) + P1 (scaffolding templates) merged
- `e03c0c3` — P2 (HANDOFF template, lessons seed, branch protection 403 fallback)
- `b565a68` — P3 (`/handoff` command, `REPO_ALREADY_EXISTS` probe, auditor reads HANDOFF)
- `36dd18b` — session-end snapshot (docs/HANDOFF.md + docs/lessons.md)
- `fc975bb` — `read:org` scope clarification + env-var vs `gh auth login` split

`docs/WORKLOG.md` carries the full per-batch chronicle. `docs/plans/0002-0005` carry the matching plans (no plan for the `read:org` hotfix — it was a direct doc fix from a real-run gap).

## Last finished

- Commit `fc975bb` (read:org hotfix) — pushed to `main` on 2026-05-30. The carlsberg real-run had hit `gh auth login: missing required scope 'read:org'` after creating a classic PAT via our recommended URL; docs now distinguish the env-var auth path (no `read:org` needed) from the stored-creds path (requires `read:org`).

## In progress

- (nothing in flight — main is stable, no open feature branches in this repo)

## Next step

Smoke-test the hardened bootstrap on a fresh derived project from Claude Code CLI inside WSL2:

```bash
cd ~/projects
mkdir test-bootstrap-v3 && cd test-bootstrap-v3
# Copy .claude/, CLAUDE.md, templates/ from claude-django (or use 'Use this template' on GitHub)
claude
> /doctor
> /bootstrap
> /handoff
> /audit
```

Expected: 0 manual interventions except the one-time PAT login (must be **classic** `ghp_...`), filling `.env` secrets, and (optionally) `createsuperuser`. If any of the 4 hard-STOP flags fires (`UNSUPPORTED_PLATFORM`, `FINE_GRAINED_PAT_NOT_SUPPORTED`, `REPO_ALREADY_EXISTS`, `NO_GH_SCOPES`) the message should be self-explanatory.

## Open questions

- [ ] Should `/handoff --append` be implemented as P4 (snapshot history) or is the overwrite model good enough long-term?
- [ ] Worth front-loading a classic-PAT capability probe (`gh api /user --jq '.permissions'`) on top of `pat_kind` detection, or is `pat_kind == "classic"` already a sufficient predictor?
- [ ] `templates/output-language.md` substitution token `{LANGUAGE_NATIVE}` is the only one outside the `{SLUG}/{DATE_ISO}/{OWNER}/{TODO}` convention — keep it for backward compat or unify?
- [ ] Are there other `gh` subcommands (besides `auth login`) that silently require scopes beyond what `/bootstrap` operations actually use? The `read:org` discovery suggests there might be more — worth a `gh` surface audit before someone else hits one.

## Environment notes

- Editing claude-django from Cowork on the Windows D: mount triggers two known issues, both worked around in this session:
  - **`Edit`/`Write` tools silently truncate on large writes.** Pattern: use bash + `python pathlib` to rewrite the whole file, verify with `wc -c` + `grep` for the new markers. Memory: `feedback_cowork_write_unreliable_on_mount.md`.
  - **Container `git` fails on Windows-written index** (`error: index uses pS:6 extension`). All `git add`/`commit`/`push` happens in PowerShell on the host. Memory: `feedback_bind_mount_locked_files.md`.
- Direct commits to `main` are allowed in this repo per template-repo policy (memory: `feedback_template_repo_direct_main.md`). PR flow applies only to derived projects.

---

> Update cadence: at session end, by hand or via `/handoff` (once the command lands in Claude Code CLI). The four-batch series in `docs/WORKLOG.md` is canonical; this file is the cursor.
