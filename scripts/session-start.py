#!/usr/bin/env python3
"""SessionStart hook entrypoint for claude-django (cross-platform).

ORDER MATTERS. Step 1 (environment detection) is mandatory: it writes
``.claude/memory/env-detect.json``, which every gate (``/doctor``,
``/bootstrap``, ``/preflight``) depends on. The optional conveniences after it
NEVER abort the hook -- each is guarded and the hook always exits 0.

Runs under any shell (PowerShell, cmd, bash, zsh, Git Bash) because the
``SessionStart`` hook invokes it as ``python scripts/session-start.py`` -- no
bash dependency (ADR 0022). Never prints secret values, never runs git
mutations.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import time


def _root() -> pathlib.Path:
    """Return the repo root (the parent of this script's ``scripts/`` dir)."""
    return pathlib.Path(__file__).resolve().parent.parent


def _clear_stale_index_lock(root: pathlib.Path) -> None:
    """Remove a stale, EMPTY ``.git/index.lock`` left by a crashed git process.

    Guarded so an ACTIVE git operation is never disturbed: only a zero-byte lock
    older than 5 minutes is touched. On bind-mounts the lock is often host-owned
    and refuses deletion; if it survives, print an actionable hint instead.
    """
    lock = root / ".git" / "index.lock"
    try:
        if not lock.is_file() or lock.stat().st_size != 0:
            return
        if time.time() - lock.stat().st_mtime <= 300:
            return
        lock.unlink(missing_ok=True)
        if not lock.exists():
            print("session-start: removed stale empty .git/index.lock", file=sys.stderr)
            return
    except OSError:
        pass
    if lock.exists():
        print(
            "session-start: stale empty .git/index.lock survived deletion -- "
            "likely host-owned on a bind-mount. Remove it from your host shell "
            "(`rm -f .git/index.lock` or `Remove-Item -Force .git/index.lock`), "
            "then relaunch.",
            file=sys.stderr,
        )


def _detect_env(root: pathlib.Path) -> None:
    """Run ``detect-env.py`` to (re)write ``.claude/memory/env-detect.json``."""
    script = root / "scripts" / "detect-env.py"
    try:
        subprocess.run([sys.executable, str(script)], cwd=str(root), check=False)
    except Exception as exc:  # never abort the hook
        print(
            f"session-start: detect-env failed ({exc}) -- env-detect.json may be stale.",
            file=sys.stderr,
        )


def _seed_env(root: pathlib.Path) -> None:
    """Seed ``.env`` from ``.env.example`` when missing (placeholders, not secrets).

    The runtime last-resort seed: ``install.sh`` and ``/bootstrap`` Mode A also
    seed earlier for UX; this hook guarantees it regardless of the entry path.
    """
    env = root / ".env"
    example = root / ".env.example"
    if not env.exists() and example.exists():
        shutil.copyfile(example, env)
        print(
            "session-start: seeded .env from .env.example -- fill in real secrets "
            "before running services.",
            file=sys.stderr,
        )


def _maybe_docker_up(root: pathlib.Path) -> None:
    """Bring services up only when ``CLAUDE_DJANGO_AUTO_UP=1`` (heavy, opt-in)."""
    if os.environ.get("CLAUDE_DJANGO_AUTO_UP", "0") != "1":
        return
    if not (root / "docker-compose.yml").is_file():
        return
    if not shutil.which("docker"):
        print(
            "session-start: CLAUDE_DJANGO_AUTO_UP=1 but docker not on PATH (skipping).",
            file=sys.stderr,
        )
        return
    print("session-start: CLAUDE_DJANGO_AUTO_UP=1 -- docker compose up -d", file=sys.stderr)
    try:
        subprocess.run(["docker", "compose", "up", "-d"], cwd=str(root), check=False)
    except Exception:
        print("session-start: docker compose up failed (continuing).", file=sys.stderr)


def main() -> int:
    """Run the SessionStart conveniences in order; never abort (always exit 0)."""
    root = _root()
    _clear_stale_index_lock(root)
    _detect_env(root)
    _seed_env(root)
    _maybe_docker_up(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
