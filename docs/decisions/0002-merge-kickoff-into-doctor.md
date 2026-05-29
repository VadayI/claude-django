# 2. Merge `/kickoff` verification into `/doctor`

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** Vadym (@VadayI)
- **Tags:** orchestration, commands, process

## Context

`/kickoff` was a 215-line monolithic command that combined two distinct concerns: **preflight verification** (does the machine have Docker / `gh` auth / templates / no existing project?) and **scaffold execution** (`gh repo create`, `django-admin startproject`, drf-spectacular wiring, first commit + push, branch protection). Mixing diagnostics with actions made the command non-reentrant — if any step failed midway, the user had no way to resume without manually reading the script and guessing which step to re-run.

Separately, `/doctor` already verified the live machine against `.claude/rules/environment.md` across four scopes (system tools · Claude config & access · project state · git hygiene). Its diagnostic logic overlapped substantially with `/kickoff`'s preflight block, but neither was scenario-aware: `/doctor` did not classify the project state, and `/kickoff` re-implemented the same checks from scratch.

The combination meant: (1) duplicated detection code in two commands; (2) no way to recover from a half-finished bootstrap; (3) no single command answered "what should I run right now on this repo?".

## Decision

Split the responsibilities along the SRP boundary:

- **`/doctor` becomes scenario-aware.** It classifies the project into one of four states (`no-config` / `fresh` / `existing-incomplete` / `active`) and recommends the next command in its summary. The existing four scope-checks stay unchanged.
- **The executive half of `/kickoff` moves to a new `/bootstrap` command** (see ADR 0003) with two modes (Mode A fresh, Mode B resume), keeping `/kickoff`'s scaffold steps but making them reentrant.
- **`/kickoff` is deleted**, not deprecated. No backward-compat shim — derived projects carry their own pinned copy from when the template was forked.

`/doctor` checks the environment and recommends; `/bootstrap` does the work. Each command has a single responsibility and can be re-run safely.

## Consequences

**Positive**
- Reentry / idempotency: after a failed bootstrap, run `/doctor` again — it classifies the current state and tells the user which step to resume.
- Clear SRP boundary: diagnostics vs. actions, never mixed.
- One command (`/doctor`) for "what's the state?" at every lifecycle stage (fresh machine, mid-bootstrap, mid-feature, post-deploy).
- The scenario detection replaces the ad-hoc "is this a new project or an existing one?" guess that lived in `/kickoff`'s opening checks.

**Negative / trade-offs**
- Two commands instead of one for the new-project flow (`/doctor` → `/bootstrap`). Mitigated: `/doctor` literally prints "run `/bootstrap` next".
- `/doctor` is now "smart" — wrong scenario classification could mislead. Mitigated: `/bootstrap` Mode B has its own probe set that re-verifies independently.

## Alternatives considered

- **Keep `/kickoff` as-is.** Rejected: the non-reentry problem is real and recurring (the user already hit it twice when bootstrap aborted mid-`docker compose up`).
- **Split into three commands** (`/kickoff-verify` + `/kickoff-execute` + `/synthesize-brief`). Rejected: `/kickoff-verify` would duplicate `/doctor`'s existing audit logic instead of consolidating it.
- **Subcommand arguments** (`/kickoff verify | execute`). Rejected: argument-routed commands hide the SRP boundary and require the user to remember the flag. A flat slash-command surface is easier to discover.

<!-- Last reviewed/updated: 2026-05-29 -->
