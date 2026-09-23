#!/usr/bin/env python3
"""Claude PreToolUse early guard for the vendored external openapi.yml.

This runtime-specific parser does not intercept arbitrary shell writes. The
contract pin and CI drift gate remain the authoritative checks.
"""

from __future__ import annotations

import json
import re
import sys

PATH_KEYS = frozenset({"file_path", "notebook_path", "path", "old_path", "new_path", "source_path", "destination_path"})
PATCH_KEYS = frozenset({"patch", "diff", "patch_text"})
EDIT_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
PATCH_LINE = re.compile(r"^(?:\*\*\* (?:Add File|Delete File|Update File|Move to): |\+\+\+ |--- )(.+)$")


def patch_paths(patch: str) -> list[str]:
    """Find paths named in recognized apply_patch or unified-diff headers.

    Args: patch is the tool's patch text or an apply_patch shell command.
    Returns: Paths from add, update, delete, move, and unified diff headers.
    Raises: ValueError if a patch marker has no recognized path.
    Side effects: None; no database, filesystem, Git, or network access.
    Business rule: An unparseable patch cannot silently pass the early guard.
    """
    paths = []
    marked = False
    for line in patch.splitlines():
        if line == "*** Begin Patch" or line.startswith("diff --git "):
            marked = True
        match = PATCH_LINE.match(line)
        if match and match.group(1) != "/dev/null":
            path = re.sub(r"^[ab]/", "", match.group(1).strip())
            if path:
                paths.append(path)
    if marked and not paths:
        raise ValueError("patch has no recognized file path")
    return paths


def collect_paths(value: object) -> list[str]:
    """Collect only path-bearing fields from a structured Claude tool input.

    Args: value is a parsed tool_input object or nested list.
    Returns: All recognized paths, including multi-file and patch entries.
    Raises: ValueError for an unparseable patch subfield.
    Side effects: None; no database, filesystem, Git, or network access.
    Business rule: Source/destination paths of rename both count as edits.
    """
    paths: list[str] = []
    if isinstance(value, list):
        for item in value:
            paths.extend(collect_paths(item))
    elif isinstance(value, dict):
        for key, child in value.items():
            if key in PATH_KEYS and isinstance(child, str):
                paths.append(child)
            if key in ("file_paths", "paths") and isinstance(child, list):
                paths.extend(item for item in child if isinstance(item, str))
            if key in PATCH_KEYS and isinstance(child, str):
                paths.extend(patch_paths(child))
            if isinstance(child, (dict, list)):
                paths.extend(collect_paths(child))
    return paths


def protected(path: str) -> bool:
    """Identify the generated contract under POSIX or Windows separators.

    Args: path is one path from a structured tool payload.
    Returns: True for a file named openapi.yml, matching the legacy guard.
    Raises: None.
    Side effects: None; no database, filesystem, Git, or network access.
    Business rule: The vendored contract must be updated by the pin workflow.
    """
    return path.replace("\\", "/").strip("\"'").rstrip("/").split("/")[-1] == "openapi.yml"


def main() -> int:
    """Parse one Claude event and block recognized direct contract edits.

    Args: Reads one JSON tool event from standard input.
    Returns: 0 for an unaffected tool, 2 for protected or malformed edits.
    Raises: None for supported JSON/shape errors; reports them on stderr.
    Side effects: Reads stdin and may write a diagnostic to stderr; no DB,
        filesystem, Git, network, install, release, or deployment effects.
    Business rule: Arbitrary Bash commands are outside tool-hook coverage;
        recognized apply_patch commands are checked by file header.
    """
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("invalid payload object")
        name = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        if not isinstance(name, str) or not isinstance(tool_input, dict):
            raise ValueError("missing tool name/input")
        if name in EDIT_TOOLS:
            paths = collect_paths(tool_input)
            if not paths:
                raise ValueError("edit payload has no recognized file path")
        elif name == "Bash":
            command = tool_input.get("command")
            if not isinstance(command, str):
                raise ValueError("Bash payload has no command")
            if "apply_patch" not in command:
                return 0
            paths = patch_paths(command)
            if not paths:
                raise ValueError("apply_patch command has no recognized file path")
        else:
            return 0
        if any(protected(path) for path in paths):
            print("[protected-edits] BLOCKED direct edit of vendored openapi.yml; update the contract pin.",
                  file=sys.stderr)
            return 2
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"[protected-edits] Cannot verify Claude edit payload: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
