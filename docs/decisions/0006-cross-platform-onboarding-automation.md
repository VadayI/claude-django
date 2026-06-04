# 6. Cross-platform onboarding automation (WSL2-only stays; reduce Windows friction)

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** Project maintainer
- **Tags:** environment, onboarding, automation, dx

## Context

ADR 0005 made the config OS-portable by collapsing to a single bash path and mandating WSL2 on Windows. That removed accidental complexity, but real `/doctor` runs on the `example-service` test project surfaced recurring *onboarding* friction that the gates correctly stopped at without smoothing:

- **The wrong-runner trap.** The single most common failure is typing `claude` inside a WSL2 shell while only the **Windows** CLI is installed. PATH interop resolves `claude` to `claude.exe`, the `SessionStart` hook runs Windows-Python, and `env-detect.json` records `platform: windows`, `platform_supported: false`. `/doctor` then HARD STOPs with `UNSUPPORTED_PLATFORM` — correct, but the generic remedy ("install WSL2") is misleading when WSL2 already exists; the real fix is to install/launch the WSL2-native `claude`.
- **Manual, undocumented setup.** Bringing a fresh WSL2 up to standard (`python-is-python3`, Node/nvm, the CLI, `gh`, the PATH-precedence fix) was a hand-run checklist.
- **Per-machine command drift.** The same Docker-based commands were retyped differently across the Windows(WSL2) and Debian machines.

The maintainer asked whether the config could "work on both Windows and Debian with more automation." Note that it already runs on both — Debian natively, Windows via WSL2 — so the question is friction, not portability.

## Decision

**Keep WSL2-only (ADR 0005 stands — PowerShell is NOT reintroduced).** Optimize the WSL2 onboarding path instead, with four additive changes:

1. **`detect-env.py` -> `wrong_runner_suspected` (schema v4).** Set `true` when `platform == "windows"` AND the `wsl` executable is present. `/doctor` (Step 0.5 + Platform audit) branches the `UNSUPPORTED_PLATFORM` remedy on it: `true` -> "install/launch the WSL2-native `claude`"; `false` -> "install WSL2". `detect-env.py` also prints the targeted hint to stderr from the hook.
2. **`scripts/setup-wsl.sh`** — idempotent one-shot toolchain installer (`python-is-python3`, Node via nvm, `@anthropic-ai/claude-code`, `gh`) that also appends the `~/.bashrc` PATH export so the WSL2 npm-global bin beats Windows interop.
3. **`templates/Makefile`** — convenience wrappers (`up`/`test`/`lint`/`migrate`/`gates`/`doctor-deps`/...) identical on native Debian and WSL2, scaffolded into derived projects like `docker-compose.yml`.
4. **`scripts/session-start.sh`** — SessionStart wrapper: mandatory `detect-env.py` first, then a safe `.env` seed from `.env.example` when missing, then `docker compose up -d` **only** when `CLAUDE_DJANGO_AUTO_UP=1`.

## Consequences

**Positive**
- The wrong-runner trap self-explains (in `detect-env.py` output, `/doctor`, `README`, `environment.md`) instead of sending users to reinstall WSL2 in vain.
- One command (`bash scripts/setup-wsl.sh` / `make setup`) replaces the manual setup checklist.
- The same `make` targets work on both supported machines.
- Less manual session bring-up (`.env` seeded; services up on opt-in).
- The platform gate's integrity is unchanged: `platform_supported` is computed exactly as before; `wrong_runner_suspected` is advisory only and never relaxes a STOP.

**Negative / trade-offs**
- `settings.json` now depends on `scripts/session-start.sh` shipping next to `scripts/detect-env.py`. They copy together via `cp -r scripts ./`, so the Quick start and `/bootstrap` keep them in lockstep; an out-of-band edit that ships only one would break the hook.
- Schema bump v3 -> v4. Additive and backward-compatible (consumers read named keys, not the version), but recorded here for traceability.
- `setup-wsl.sh` and the `Makefile` host commands target apt-based distros (Ubuntu/Debian incl. WSL2 Ubuntu). macOS gets a clear "use Homebrew" message but no automated install — acceptable, since the maintainer's machines are WSL2 + Debian.

## Alternatives considered

- **Reintroduce native-Windows PowerShell support.** Rejected — reopens exactly the doubled docs/scripts ADR 0005 removed, and breaks Docker bind-mount performance and local-CI parity (the gate scripts are bash).
- **Devcontainer to unify environments.** Deferred — heavier and changes the run model; WSL2 + Docker Desktop already supplies the Linux runtime, so the payoff is small relative to the churn.
- **Auto-fix the wrong runner inside the hook** (auto-install the Linux `claude`). Rejected — the SessionStart hook must stay fast and read-only, and the project philosophy is "detect -> propose -> fix on confirm". `setup-wsl.sh` is the explicit, opt-in installer instead.

<!-- Last reviewed/updated: 2026-06-01 -->
