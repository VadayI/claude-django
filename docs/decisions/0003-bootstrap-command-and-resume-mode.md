# 3. `/bootstrap` command with fresh and resume modes

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** Vadym (@VadayI)
- **Tags:** orchestration, commands, git, resume

## Context

Users on this template repeatedly hit two related pain points around starting a new project:

1. **Half-bootstrapped repos.** A bootstrap can abort midway — `docker compose up` times out, `gh repo create` 401s, `django-admin startproject` errors on path encoding. The old `/kickoff` had no resume mode: the user had to manually figure out which of the 8 steps had completed, then re-run the rest by hand against the live state.
2. **Joining an in-progress project from a second machine.** When the user pulls a repo that someone else (or past-self) bootstrapped partially, they need a way to fill in the missing pieces — drf-spectacular config, branch protection, per-app READMEs, CI workflows — without redoing the whole scaffold and without violating the "no direct pushes to main" rule.

A separate consideration: the very first commit on a fresh project MUST go directly to `main` (there is no PR target until the repo exists), and this is the only place in the workflow where `git push origin main` is legitimate. The old `/kickoff` did this implicitly; the new design needs to make this exception explicit and bounded.

## Decision

`/bootstrap` ships with two modes, auto-detected from project state:

- **Mode A — Fresh.** Empty CWD with `.claude/`+templates copied but no `.git/`, no `backend/`, no GitHub remote. Runs the full scaffold end-to-end: prompts for GitHub login / slug / output language, runs `gh repo create`, lays the skeleton, copies templates, runs `docker compose up -d`, `django-admin startproject`, splits settings, configures drf-spectacular, runs `migrate`, generates `docs/api/openapi.yml`, prompts for `createsuperuser`, makes the first commit and pushes `origin main`, then enables branch protection. **This is the only command in the entire workflow allowed to direct-push to main**, documented as an explicit exception in `.claude/rules/git-operations.md`.
- **Mode B — Resume.** Existing `.git/` + GitHub remote with partial scaffold. Runs ~8 read-only probes (drf-spectacular installed? `docs/api/openapi.yml` present? branch protection enabled? `.github/workflows/backend-ci.yml` present? CI gate scripts present? `.env` exists? per-app READMEs? `docs/STUBS.md` + `docs/APP_README.md`?), and for each missing piece creates a separate feature branch + PR. **Never direct-pushes to main.**

Mode is detected automatically by `/bootstrap`'s opening Python probe (`has_git` && `has_remote_github` → Mode B; neither → Mode A; ambiguous → STOP and ask).

## Consequences

**Positive**
- Idempotent resume: re-running `/bootstrap` on a half-finished repo is safe and ships the remaining pieces as discrete PRs.
- Each Mode B fix is reviewable in isolation (CI per piece, separate diffs in git history).
- Clear separation between "direct main" (Mode A only, bounded to first commit) and "PR-only" (Mode B and everywhere else).
- Aligns with the iron rule of PR-only work without inventing a special-case bypass.

**Negative / trade-offs**
- More complexity inside a single command — Mode A and Mode B share little code, and the dispatcher logic adds a layer.
- Another documented exception in `git-operations.md` (alongside no other exceptions today). Mitigated: the exception is named, bounded to one command, and immediately followed by enabling branch protection.

## Alternatives considered

- **Mode B as a separate `/bootstrap-resume` command.** Rejected: forces the user to know in advance which mode applies; auto-detection from project state is friendlier.
- **Mode B also direct-pushes to main** (for simplicity). Rejected: violates the iron rule, removes the reviewability benefit of per-piece PRs.
- **Refuse-mode in Mode B** (just print what's missing, don't fix). Simpler to implement but worse UX — the user still has to do the work manually, which is the original pain point.

<!-- Last reviewed/updated: 2026-05-29 -->
