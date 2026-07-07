#!/usr/bin/env python3
"""UserPromptExpansion hook (matcher ``.*``): log every slash command.

Replaces the per-command ``## Log`` block (20 copies of
``python scripts/log-cmd.py /<cmd> $ARGUMENTS``, removed in the 2026-07-07
audit, batch D). Appends the same JSONL schema ``{ts, cmd, args}`` to
``.claude/memory/command-log.jsonl``; the ``auditor`` agent (``/audit``)
reads that log to suggest the next command.

Advisory infrastructure -- never blocks, never prints, always exit 0.
Cross-platform (ADR 0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone


def main() -> int:
    """Append one log entry from the hook payload; never block (exit 0)."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = (payload.get("command_name") or "").strip()
    if not cmd:
        return 0
    if cmd.endswith(".md"):
        cmd = cmd[:-3]
    if not cmd.startswith("/"):
        cmd = "/" + cmd
    args = ""
    for key in ("arguments", "args", "command_args"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            args = val.strip()
            break
    try:
        log_dir = pathlib.Path(".claude/memory")
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd,
            "args": args,
        }
        with (log_dir / "command-log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
