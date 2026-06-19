# 22. Support the native Windows runner (cross-platform Python hooks)

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project maintainer
- **Tags:** environment, shell, windows, hooks
- **Amends:** ADR 0005 (Drop Windows-native shell support)

## Context

ADR 0005 (2026-05-29) dropped Windows-native shell support and made WSL2 the only
supported runner on Windows. Its premise was partly that a Windows-native Claude
Code runner was not a real option, and that the template's machinery (a bash
`SessionStart` hook, bash policy hooks, bash CI gate scripts, Docker) effectively
required a POSIX shell.

Two things changed:

1. **Claude Code now runs natively on Windows.** Official setup docs list Windows
   10+ with "WSL, WSL 2, or Git for Windows", and a native PowerShell tool
   shipped. The runner itself is no longer the blocker.
2. **The only hard dependency on bash was our own hooks.** The `SessionStart` and
   policy hooks were bash scripts invoked as `bash scripts/...sh`. On native
   Windows, bash-form hooks are fragile — Claude Code can resolve `bash` to the
   WSL launcher stub `C:\Windows\System32\bash.exe` and hang or fail silently
   (anthropics/claude-code#37634, #18610, #24097). That fragility — not Docker or
   the CI gates — was what truly forced WSL2.

The full runner-vs-toolchain analysis is in
`docs/reviews/2026-06-19-template-windows-wsl2-audit.md`.

## Decision

**Support `claude` running natively on Windows. Make every hook cross-platform
Python so no hook depends on bash. WSL2 on Windows becomes optional — needed only
as a Docker Desktop backend, never as the shell.**

Concretely:

- The `SessionStart` hook and the three policy hooks are rewritten from bash to
  Python and invoked as `python scripts/...py` (precedent: `scripts/log-cmd.py`).
  The two PostToolUse `ruff` one-liners (`... 2>/dev/null || true`, not portable
  to PowerShell) move into `scripts/policy/auto_format.py`.
- `scripts/detect-env.py` reports `platform_supported: true` on Windows as well as
  Linux / macOS / WSL2. `wrong_runner_suspected` is retired (always `false`):
  launching the Windows `claude` is no longer a misconfiguration. `detect_shell()`
  additionally recognizes `powershell`, `cmd`, and `git-bash`.
- Because the `/doctor`, `/bootstrap`, and `/preflight` gates only STOP when
  `platform_supported == false`, they unblock on Windows automatically; their
  prose is updated to drop the "install WSL2 / Windows-native NOT supported"
  framing.
- The `.sh` CI gate scripts (`check_stubs.sh`, etc.) are unchanged: they run on
  the Linux CI runner, and locally on Windows they need Git Bash (optional, for
  `make gates`) — they are not on the per-session hot path.
- Docker is unchanged. Docker Desktop on Windows still needs a backend (WSL2 or
  Hyper-V). "Without WSL" means the user does not run `claude` / the terminal
  inside WSL; WSL2 may persist invisibly as Docker's backend.

## Consequences

**Positive**
- A project derived from this template can be driven by `claude` on native
  Windows (PowerShell or Git Bash), no WSL shell required.
- Hooks are no longer shell-fragile: Python is invoked directly, sidestepping the
  `bash`→WSL-stub hang.
- One set of `.py` hook files is genuinely cross-platform (Linux / macOS / WSL2 /
  Windows).

**Negative / trade-offs**
- The decisive proof is empirical and per-machine: only a real native-Windows
  session confirms Claude Code fires `python scripts/session-start.py` cleanly.
  Tracked as the validation step in `docs/plans/0014-native-windows-runner.md`.
- `make gates` locally on native Windows still needs Git Bash (the gate scripts
  stay bash). Acceptable: they mirror CI (Linux) and are off the per-session path.
- `python` must resolve on Windows PATH (not the Microsoft Store alias) — the same
  hard Python requirement the template already had.

## Relationship to ADR 0005

This ADR **amends**, not reverts, ADR 0005. ADR 0005's simplification (one hook
runtime; no dual bash/PowerShell command tables) stands — we did not reintroduce
PowerShell *scripts*. We replaced the single bash hook runtime with a single
**Python** hook runtime, portable across all supported platforms including native
Windows. ADR 0009 (working from `/mnt` is supported) is unaffected.

## Alternatives considered

- **Keep WSL2-only (status quo).** Rejected: the premise (no native-Windows
  runner) is outdated, and the only real blocker (bash hooks) is removable.
- **Git Bash + keep bash hooks.** Rejected as the primary path: bash-form hooks on
  native Windows are the documented fragile case (#37634); Python invocation
  avoids it entirely. Git Bash remains the optional way to run the `.sh` gate
  scripts locally.
- **Rewrite the CI gate scripts in Python too.** Deferred: they run on Linux CI
  and are off the per-session path; porting them is out of scope here (tracked as
  an open question in plan 0014).

<!-- Last reviewed/updated: 2026-06-19 -->
