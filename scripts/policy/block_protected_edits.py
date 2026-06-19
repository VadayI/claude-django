#!/usr/bin/env python3
"""PreToolUse hook: block hand-edits of the vendored external contract.

Matcher ``Write|Edit|MultiEdit``. Hard-blocks any edit whose target file is
``openapi.yml`` -- the vendored copy pulled from ``claude-api-contract``
(api-docs.md, ADR 0017), never authored here. Reads the hook payload as JSON on
stdin; exit 2 + stderr blocks the call, exit 0 allows. Cross-platform (ADR
0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    """Block the edit (exit 2) iff it targets ``openapi.yml``; else allow (0)."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool_name = payload.get("tool_name") or ""
    if tool_name not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0
    if os.path.basename(file_path) == "openapi.yml":
        print(
            f"[protected-edits] BLOCKED hand-edit of: {file_path}\n"
            "docs/api/openapi.yml is the VENDORED external contract -- pulled from\n"
            "claude-api-contract, never hand-edited (api-docs.md, ADR 0017).\n"
            "To change the contract: design it in claude-api-contract, bump\n"
            "CONTRACT_VERSION in .env, then: bash scripts/pull_contract.sh",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
