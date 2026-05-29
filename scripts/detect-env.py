#!/usr/bin/env python3
"""Detect the runtime environment for claude-django commands.

Writes ``.claude/memory/env-detect.json`` with the platform, shell, WSL2 status,
and tool availability. Invoked by the ``SessionStart`` hook in
``.claude/settings.json``. No caching — runs on every session start so the data
is always fresh.

Python is a HARD REQUIREMENT of this project. If Python cannot run, the hook
itself fails and the user is told to install Python 3.10+.

Output schema (``.claude/memory/env-detect.json``)::

    {
      "schema_version": 2,
      "detected_at": "<ISO 8601 UTC>",
      "platform": "windows" | "linux" | "darwin",
      "platform_release": "<uname -r equivalent>",
      "platform_supported": true | false,
      "is_wsl2": true | false,
      "shell": "bash" | "zsh" | "unknown",
      "python": {"version": "...", "executable": "..."},
      "tools": {"git": bool, "gh": bool, "docker": bool, "wsl": bool, ...},
      "cwd": "<absolute path>"
    }

``platform_supported`` is ``true`` on Linux / macOS / WSL2 and ``false`` on
Windows-native shells (PowerShell / cmd). Windows-native shells are NOT
supported — see ADR ``docs/decisions/0005-drop-windows-native-shell.md``. On
Windows the user must install WSL2 Ubuntu and run every command (including
``gh``, ``git``, ``python``, ``docker compose``) from inside WSL2.

Commands and agents consult this file at the start of every session and pick
bash-appropriate syntax (Linux / macOS / WSL2).
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import shutil
import sys
from datetime import datetime, timezone


def detect_shell() -> str:
    """Detect active shell. Bash family only (Windows-native shells unsupported)."""
    sh = os.environ.get("SHELL", "")
    if sh.endswith("zsh"):
        return "zsh"
    if sh.endswith("bash"):
        return "bash"
    return "unknown"


def is_wsl2() -> bool:
    """Detect whether we are running inside WSL2."""
    try:
        with open("/proc/version", "r", encoding="utf-8") as f:
            content = f.read().lower()
            return "microsoft" in content or "wsl" in content
    except (FileNotFoundError, OSError):
        return False


def main() -> int:
    """Detect the environment and write ``.claude/memory/env-detect.json``."""
    platform_supported = (
        platform.system() in ("Linux", "Darwin")
        or is_wsl2()
    )
    info = {
        "schema_version": 2,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system().lower(),  # 'windows' | 'linux' | 'darwin'
        "platform_release": platform.release(),
        "platform_supported": platform_supported,
        "is_wsl2": is_wsl2(),
        "shell": detect_shell(),
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "tools": {
            "git": shutil.which("git") is not None,
            "gh": shutil.which("gh") is not None,
            "docker": shutil.which("docker") is not None,
            "wsl": shutil.which("wsl") is not None,
            "node": shutil.which("node") is not None,
            "npm": shutil.which("npm") is not None,
        },
        "cwd": str(pathlib.Path.cwd()),
    }

    out_dir = pathlib.Path(".claude/memory")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "env-detect.json"
    out_path.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    # One non-noisy summary line for the SessionStart hook output.
    shell_label = info["shell"]
    if info["platform"] == "linux" and info["is_wsl2"]:
        shell_label = f"{shell_label} (WSL2)"
    print(
        f"env: {info['platform']} | shell: {shell_label} "
        f"| python {info['python']['version']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
