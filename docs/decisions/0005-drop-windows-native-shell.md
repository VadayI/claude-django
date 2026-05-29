# 5. Drop Windows-native shell support (bash only)

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** Vadym (@VadayI)
- **Tags:** environment, shell, simplification

## Context

The template historically tried to support two shells in parallel: bash (Linux / macOS / WSL2 Ubuntu) AND PowerShell (Windows native). The dual-shell support spread across many surfaces:

- `.claude/rules/environment.md` — every check table had two columns (`Check (bash)` / `Check (PS)`), nearly doubling the document's length.
- `.claude/rules/docker-commands.md` — duplicated command listings.
- `.claude/commands/kickoff.md` — branching on detected shell at every step.
- `scripts/detect-env.py` — `is_powershell` / `is_cmd` flags, `$PSVersionTable` probes, fall-through logic for unknown shells.
- `README.md` — Quick start had a bash block followed by a `<details><summary>PowerShell variant</summary>` block doing the same thing with `Copy-Item` / `Remove-Item`.

By rough count, ~30% of the lines in those files existed solely to handle the PowerShell branch. The author of the template (`@VadayI`) and every known derived-project user runs WSL2 + Docker Desktop — there were no real users on Windows-native shell. The dual-shell support was paid-for, accidental complexity.

Two reinforcing reasons make WSL2 effectively mandatory on Windows anyway: (1) Docker bind-mounts from Windows-native paths (`/mnt/c|/mnt/d`) are significantly slower than from WSL2 FS (`~/projects/<slug>`), and (2) the CI gate scripts (`scripts/check_stubs.sh`, `check_openapi_drift.sh`, `check_app_readmes.sh`) are bash by design — they run on the Linux GitHub Actions runner — so any local-test parity with CI requires bash anyway.

## Decision

**Drop Windows-native shell support entirely. The supported shells are bash (Linux / macOS / WSL2 Ubuntu) and zsh (Linux / macOS). PowerShell and cmd are not supported.**

Concretely:

- `scripts/detect-env.py` returns `platform_supported: false` when the OS is Windows but no WSL2 is detected. The `is_powershell` / `is_cmd` fields are removed.
- `/doctor` reads `platform_supported`; if `false`, it stops with explicit instructions to install WSL2 Ubuntu and re-run from inside it.
- `.claude/rules/environment.md` collapses its two-column check tables to single bash columns.
- `.claude/rules/docker-commands.md` adds a one-line bash-only directive at the top.
- `README.md` removes the `<details>PowerShell variant</details>` blocks from Quick start.
- The Remediation policy in `environment.md` switches `Remove-Item Env:...` to `unset ...` + `~/.bashrc`.

## Consequences

**Positive**
- Documentation halves in size on the shell-dependent surfaces; onboarding instructions become a single linear path.
- `detect-env.py` simplifies: one shell detection branch, no `$PSVersionTable` probing.
- Local-test parity with CI is automatic (both bash).
- Removes a class of "works on my machine" bugs from PowerShell-specific path semantics (`$env:TEMP` vs. `/tmp`, `\` vs. `/`, etc.).

**Negative / trade-offs**
- Hypothetical Windows-native users must install WSL2 Ubuntu before they can use the template. The cost: a one-time install. No known real user is affected.
- One small migration cost for the author's own machines (already on WSL2 — confirmed `/doctor` clean).

## Alternatives considered

- **Keep dual-shell with a deprecation warning.** Rejected: deferred work without payoff — the overhead stays, and the deprecation eventually has to land anyway.
- **Support only Linux / macOS** (drop Windows entirely). Rejected: Windows users with WSL2 are valid and indistinguishable from native Linux from the project's perspective.
- **Make PowerShell first-class** (drop Linux/macOS). Rejected: Docker bind-mount performance on Windows-native is poor, and CI gates are bash anyway — picking PS as the canonical shell would force ongoing translation overhead in CI.

<!-- Last reviewed/updated: 2026-05-29 -->
