#!/usr/bin/env python3
"""PreToolUse hook (matcher ``create-pr``): advisory PR preconditions.

Fires when the ``/create-pr`` command expands. ADVISORY only -- prints notices
to stdout (injected into Claude's context), never blocks (always exit 0).
Cross-platform (ADR 0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys


def _run(args: list[str]) -> str:
    """Return stripped stdout of ``args``, or '' on any failure."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def main() -> int:
    """Print advisories for ``/create-pr`` preconditions; never block (exit 0)."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cmd = (payload.get("command_name") or "").lstrip("/")
    if cmd.endswith(".md"):
        cmd = cmd[:-3]
    if cmd != "create-pr":
        return 0

    root = _run(["git", "rev-parse", "--show-toplevel"]) or os.getcwd()
    try:
        os.chdir(root)
    except OSError:
        pass

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "main":
        print(
            "[command-gate] advisory (/create-pr): you are on 'main' -- PRs must "
            "come from a feature branch (git-operations.md)."
        )
    if not sorted(glob.glob("docs/plans/[0-9]*-*.md")):
        print(
            "[command-gate] advisory (/create-pr): no docs/plans/NNNN-*.md found -- "
            "non-trivial work should carry a living plan (living-plan.md)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
