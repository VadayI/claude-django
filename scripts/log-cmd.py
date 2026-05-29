#!/usr/bin/env python3
"""Append a single JSONL entry to ``.claude/memory/command-log.jsonl``.

Used by every slash command (``/audit``, ``/kickoff``, ``/doctor``, ...) to log
each invocation. Cross-shell helper — replaces the bash one-liner
``mkdir -p .claude/memory && printf '...' >> .claude/memory/command-log.jsonl``
which broke in PowerShell/cmd.

Usage::

    python scripts/log-cmd.py /audit $ARGUMENTS

The first argv is the command name (e.g. ``/audit``); the rest are joined with
spaces and stored as ``args``. The auditor agent reads the log to suggest the
next command.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone


def main() -> int:
    """Append one log entry; print nothing on success."""
    cmd = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    log_dir = pathlib.Path(".claude/memory")
    log_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cmd": cmd,
        "args": args,
    }
    with (log_dir / "command-log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
