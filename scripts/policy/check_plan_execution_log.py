#!/usr/bin/env python3
"""SubagentStop hook (advisory): nudge to update the living plan's Execution log.

Fires when a core executor agent finishes (scoped by the settings.json matcher).
Silent unless a living plan exists AND its Execution log still has only the
seeded line. Never blocks (always exit 0). Cross-platform (ADR 0022): invoked as
``python`` -- no bash, no awk.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys


def main() -> int:
    """Advise (stderr) if the newest plan's Execution log has no real entry yet."""
    try:
        sys.stdin.read()  # drain stdin
    except Exception:
        pass

    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        root = (r.stdout or "").strip() or os.getcwd()
    except Exception:
        root = os.getcwd()
    try:
        os.chdir(root)
    except OSError:
        return 0

    plans = glob.glob("docs/plans/[0-9]*-*.md")
    if not plans:
        return 0
    plan = max(plans, key=os.path.getmtime)

    real_entries = 0
    in_log = False
    try:
        with open(plan, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("## Execution log"):
                    in_log = True
                    continue
                if line.startswith("## "):
                    in_log = False
                if in_log and line.startswith("- ") and "plan seeded." not in line:
                    real_entries += 1
    except OSError:
        return 0

    if real_entries > 0:
        return 0

    print(
        f"[plan-log] advisory: {plan} Execution log has no real entry yet "
        "(only the seed line).",
        file=sys.stderr,
    )
    print(
        "[plan-log] each core executor agent should append one line per finished "
        "phase (living-plan.md).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
