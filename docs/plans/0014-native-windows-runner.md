# Plan 0014 — Native Windows runner (no WSL required)

> Status: 🟡 IN PROGRESS · seeded 2026-06-19 · Driver: user request — "хочу щоб працював без WSL"
> Type: config-template change (no backend production code). Amends ADR 0005.
>
> **Living plan** — discipline in `.claude/rules/living-plan.md`.

## Status

| Step | State | Owner |
|---|---|---|
| PR1. Cross-platform hook runtime (detect-env + Python hooks + settings.json) | in_progress | orchestrator |
| PR2. Relax /doctor · /bootstrap · /preflight · config-check · plugins gate prose | pending | orchestrator |
| PR3. Rewrite environment.md · docker-commands.md · CLAUDE.md · README.md | pending | orchestrator |
| PR4. ADR 0022 (amends 0005) + context sync (audit/HANDOFF/WORKLOG) | pending | orchestrator |
| V. Empirical validation on native Windows (claude in PowerShell, no WSL) | blocked | user |

## Goal

A project derived from this template can be driven by `claude` running natively on Windows (PowerShell / Git Bash), without opening a WSL shell. WSL2 may remain only as a Docker Desktop backend. Closes the WSL2 hard-requirement from ADR 0005, whose premise (no native-Windows Claude Code) is now outdated.

## Approach

- Hooks → cross-platform **Python** (user decision). SessionStart + 3 policy hooks + the 2 PostToolUse ruff one-liners become `python scripts/...py`; no bash in any hook command. Precedent: `log-cmd.py`.
- `detect-env.py`: `platform_supported` true on Windows too; `wrong_runner_suspected` retired (always False); shell detection learns powershell/cmd/git-bash. Once `platform_supported` is true on Windows, the existing `/doctor`·`/bootstrap`·`/preflight` gates stop STOPping automatically — PR2 only fixes their now-stale prose.
- Docker unchanged: Docker Desktop still needs a backend (WSL2 or Hyper-V). "Without WSL" here means the user does not run claude/terminal inside WSL; WSL2 may persist invisibly as Docker's backend.
- The reversal is documented in a new ADR 0022 that **amends** (does not delete) ADR 0005.

## Steps

1. PR1 — runtime: port hooks to Python, edit detect-env.py + settings.json, remove old .sh hooks (host `git rm`), prove the Windows branch.
2. PR2 — refresh command-gate prose (functionally already unblocked by PR1).
3. PR3 — rewrite environment/docker-commands/CLAUDE/README narrative for native Windows.
4. PR4 — ADR 0022 + context sync.
5. V — user launches claude natively on Windows and confirms env-detect.json (`platform_supported: true`, no hang).

## Verification

- `python -m py_compile` on every new/edited script; 0 NUL; 0 CR (LF); settings.json parses as JSON.
- Mock proof: `_platform_supported()` True for Windows/Linux/Darwin; `detect_shell()` → powershell/cmd/git-bash on faked Windows.
- Real run of detect-env.py executes and writes valid JSON (sandbox reports linux; the Windows path is proven by mock since the sandbox is Linux).
- **The decisive gate is empirical (V)** — only the user's real Windows machine confirms Claude Code fires `python scripts/session-start.py` and does not hang on a bash stub.

## Open questions

- [ ] Node hard-requirement: with the native Windows installer, Node is no longer needed to install `claude`. Soften `NO_NODE` from hard-STOP to advisory? (PR2/PR3)
- [ ] Gate `.sh` scripts (`make gates`) on native Windows need Git Bash; document as optional, or port to Python later?

## Execution log

- 2026-06-19 — plan seeded.
- 2026-06-19 — PR1 (working tree): detect-env.py platform gate → Windows supported, wrong_runner retired; session-start + 3 policy hooks + auto_format ported to Python; settings.json hook commands → python. py_compile / NUL / CR / JSON + mock Windows-branch proof green. Old .sh removal + git deferred to host (9p blocks rm + git).

## Amendments

_(none yet)_
