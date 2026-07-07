#!/usr/bin/env python3
"""Shared runtime gate: is this a supported Claude Code CLI runtime?

Single mechanical source of the ``NO_ENV_DETECT`` / ``UNSUPPORTED_PLATFORM``
flags used by ``/doctor`` (Step 0.5 — canonical prose + remediation),
``/preflight`` (Step 0), ``/bootstrap`` (hard preflight), and — via
``/doctor`` — ``/config-check`` and ``/plugins``. Replaces the per-command
re-implementations (2026-07-07 audit, batch D).

Reads ``.claude/memory/env-detect.json`` (written ONLY by the ``SessionStart``
hook). Prints exactly one line and always exits 0 — the calling command
interprets the flag and applies /doctor Step 0.5 remediation:

    NO_ENV_DETECT                  file missing/unreadable -> hook never ran
    UNSUPPORTED_PLATFORM <name>    platform_supported == false
    RUNTIME_OK                     proceed

Never hand-write or fabricate ``env-detect.json`` to get past this gate
(see environment.md, "env-detect.json integrity").
Cross-platform (ADR 0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import json
import pathlib
import sys


def main() -> int:
    """Print one runtime flag (see module docstring); never block (exit 0)."""
    envf = pathlib.Path(".claude/memory/env-detect.json")
    if not envf.is_file():
        print("NO_ENV_DETECT")
        return 0
    try:
        env = json.loads(envf.read_text(encoding="utf-8"))
    except Exception:
        print("NO_ENV_DETECT")
        return 0
    if not env.get("platform_supported", True):
        print(f"UNSUPPORTED_PLATFORM {env.get('platform', 'unknown')}")
        return 0
    print("RUNTIME_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
