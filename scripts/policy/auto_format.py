#!/usr/bin/env python3
"""PostToolUse hook: run ruff in the backend container, swallowing all errors.

Cross-platform (ADR 0022) replacement for the bash ``... 2>/dev/null || true``
one-liners (``|| true`` and ``2>/dev/null`` are not portable to PowerShell).
Best-effort auto-format / lint-fix; never fails a tool call (always exit 0).
Arg ``format`` -> ``ruff format .``; ``check`` -> ``ruff check --fix .``.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run ``ruff format`` / ``ruff check --fix`` in the backend container; exit 0."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "format"
    ruff = ["ruff", "format", "."] if mode == "format" else ["ruff", "check", "--fix", "."]
    try:
        subprocess.run(
            ["docker", "compose", "exec", "-T", "backend", *ruff],
            capture_output=True, text=True, timeout=120,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
