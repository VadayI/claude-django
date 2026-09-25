#!/usr/bin/env python3
"""UserPromptExpansion hook (matcher ``.*``): log every slash command.

Replaces the per-command ``## Log`` block (20 copies of
``python scripts/log-cmd.py /<cmd> $ARGUMENTS``, removed in the 2026-07-07
audit, batch D). Appends the same JSONL schema ``{ts, cmd, args}`` to
``.ai-runtime/command-log.jsonl`` (a legacy ``.claude/memory/command-log.jsonl``
is moved there first by ``scripts/ai/project_state.py``); the ``auditor`` agent
(``/audit``) reads that log to suggest the next command.

Advisory infrastructure -- never blocks, never prints on success, always exit 0.
The one reported failure is a conflict between two differing log copies: the
hook refuses to append rather than create a second writable copy.
Cross-platform (ADR 0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone


def _log_path() -> pathlib.Path:
    """Resolve the canonical command log after migrating its legacy copy.

    Returns: ``<root>/.ai-runtime/command-log.jsonl``.
    Raises: ValueError for a conflicting legacy copy or a linked path; OSError
        when the legacy file cannot be moved.
    Side effects: May move legacy runtime records into ``.ai-runtime``; never
        touches project registries or unknown files.
    """
    root = pathlib.Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts" / "ai"))
    import project_state  # noqa: E402  (vendored family core; jedyny resolver stanu)

    project_state.migrate_runtime(root)
    return project_state.writable_state_path(root, "command-log.jsonl", "runtime")


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
        log_path = _log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd,
            "args": args,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except ValueError as error:
        # Konflikt kopii musi być widoczny; inne błędy zapisu pozostają ciche.
        if "Migrate legacy state" in str(error) or "Conflicting" in str(error):
            print(f"log-command: {error}", file=sys.stderr)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
