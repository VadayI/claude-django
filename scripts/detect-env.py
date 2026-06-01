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
      "schema_version": 5,
      "detected_at": "<ISO 8601 UTC>",
      "platform": "windows" | "linux" | "darwin",
      "platform_release": "<uname -r equivalent>",
      "platform_supported": true | false,
      "wrong_runner_suspected": true | false,
      "node_supported": true | false,
      "is_wsl2": true | false,
      "shell": "bash" | "zsh" | "unknown",
      "python": {"version": "...", "executable": "..."},
      "tools": {"git": bool, "gh": bool, "docker": bool, "wsl": bool, ...},
      "tool_versions": {"git": "git version 2.43.0", "gh": "gh version 2.40.1", ...},
      "gh": {
        "available": bool, "scopes": list[str], "has_repo_scope": bool, ...,
        "pat_kind": "classic" | "fine-grained" | "unknown"
      },
      "cwd": "<absolute path>"
    }

The ``pat_kind`` field is derived from the **prefix** of the token returned by
``gh auth token`` -- never the value itself. Fine-grained PATs (prefix
``github_pat_``) do not expose OAuth scopes via response headers, so the
existing ``has_*_scope`` probes always report ``false`` for them. Per ADR 0008
(manual repo creation + fine-grained per-repo PAT) a fine-grained token is the
**recommended** credential, so consumers (``/bootstrap``, ``/doctor``) do NOT
gate on OAuth scopes for fine-grained tokens and must NOT treat
``pat_kind == "fine-grained"`` as a blocker; capability is verified by probing
the target repo (``gh repo view``) and by per-operation errors, not by headers.

``platform_supported`` is ``true`` on Linux / macOS / WSL2 and ``false`` on
Windows-native shells (PowerShell / cmd). Windows-native shells are NOT
supported — see ADR ``docs/decisions/0005-drop-windows-native-shell.md``. On
Windows the user must install WSL2 Ubuntu and run every command (including
``gh``, ``git``, ``python``, ``docker compose``) from inside WSL2.

``wrong_runner_suspected`` is ``true`` when ``platform == "windows"`` AND the
``wsl`` executable is present. That combination almost always means the user
typed ``claude`` inside a WSL2 shell but PATH interop resolved it to the
Windows ``claude.exe`` (the Linux-native CLI was never installed in Ubuntu), so
the hook ran Windows-Python and recorded ``platform: windows``. ``/doctor`` uses
this flag to give a targeted fix (install / launch the WSL2-native ``claude``)
instead of the generic "install WSL2" message — reinstalling WSL2 would not
help here.

``node_supported`` is ``true`` when Node.js is on PATH and its major version is
>= 18. Node is a HARD REQUIREMENT, not optional: the supported runner -- the
WSL2-native Claude Code CLI -- is installed via ``npm install -g
@anthropic-ai/claude-code``, so without Node 18+ the correct ``claude`` cannot
exist. ``/doctor`` reads this derived boolean (the same pattern as the ``gh``
``has_*_scope`` flags) instead of re-parsing the version string, and reports
``NO_NODE`` when it is ``false``. A present-but-unparseable version is treated as
supported so a parse quirk never falsely blocks the user.

Commands and agents consult this file at the start of every session and pick
bash-appropriate syntax (Linux / macOS / WSL2).
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import shutil
import subprocess
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


def _tool_version(cmd: list[str]) -> str | None:
    """Return the first line of ``cmd --version`` output, or ``None`` on failure.

    Used by the SessionStart hook to record exact tool versions in
    ``env-detect.json`` so agents can detect outdated tooling without re-shelling
    out. Short timeout because every probe runs on every session start.
    """
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        out = (r.stdout or r.stderr).strip()
        return out.splitlines()[0] if out else None
    except Exception:
        return None


def _node_supported() -> bool:
    """Return whether Node.js >= 18 is on PATH.

    Node is a hard requirement: the WSL2-native Claude Code CLI is installed via
    ``npm install -g @anthropic-ai/claude-code``, so the supported runner cannot
    exist without Node 18+. Consumers (``/doctor``) gate on this flag and report
    ``NO_NODE`` when it is ``False``.

    Defensive by design -- a missing ``node`` returns ``False``, but a present
    binary whose ``--version`` string cannot be parsed returns ``True`` so a
    parse quirk never produces a false hard block. Never raises.
    """
    if not shutil.which("node"):
        return False
    ver = _tool_version(["node", "--version"])  # e.g. 'v20.11.0'
    if not ver:
        return True  # present but version unreadable -- do not falsely block
    try:
        major = int(ver.strip().lstrip("vV").split(".")[0])
        return major >= 18
    except (ValueError, IndexError):
        return True  # unparseable -- treat as supported


def _gh_pat_kind() -> str:
    """Return ``"classic"`` / ``"fine-grained"`` / ``"unknown"`` for the active credential.

    Determined from the prefix of ``gh auth token`` (per GitHub token-format
    conventions). The token value itself is NEVER logged or returned -- only
    the prefix is matched and discarded. Used by ``/bootstrap`` and ``/doctor``
    for diagnostics. Per ADR 0008 fine-grained PATs are the recommended
    credential and are NOT blocked; because they don't expose OAuth scopes via
    response headers, consumers skip the scope-header gate for them and verify
    capability by probing the target repo and via per-operation errors.

    Prefix table (GitHub docs):
        - ``ghp_``         -> classic PAT
        - ``gho_``         -> OAuth user-to-server (carries scopes; treated as classic)
        - ``ghu_``         -> GitHub App user-to-server (treated as classic)
        - ``ghs_``         -> GitHub App server-to-server (treated as classic)
        - ``github_pat_``  -> fine-grained PAT
        - anything else / missing token -> ``"unknown"``
    """
    if not shutil.which("gh"):
        return "unknown"
    try:
        r = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        token = (r.stdout or "").strip()
        if not token:
            return "unknown"
        if token.startswith("github_pat_"):
            return "fine-grained"
        if token.startswith(("ghp_", "gho_", "ghu_", "ghs_")):
            return "classic"
        return "unknown"
    except Exception:
        return "unknown"


def _gh_scopes() -> list[str]:
    """Return the OAuth scopes attached to the active ``gh`` credential.

    Parses the ``X-OAuth-Scopes`` response header from ``gh api /user --include``.
    Returns an empty list if ``gh`` is not on PATH or the user is not
    authenticated. Used by ``/bootstrap`` and ``/doctor`` to verify that the
    active PAT carries ``repo``, ``workflow``, and ``admin:repo_hook`` before
    attempting automated repo creation and branch protection.
    """
    if not shutil.which("gh"):
        return []
    try:
        r = subprocess.run(
            ["gh", "api", "/user", "--include"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in r.stderr.splitlines() + r.stdout.splitlines():
            if line.lower().startswith("x-oauth-scopes:"):
                _, _, scopes = line.partition(":")
                return [s.strip() for s in scopes.split(",") if s.strip()]
    except Exception:
        pass
    return []


def main() -> int:
    """Detect the environment and write ``.claude/memory/env-detect.json``."""
    platform_supported = (
        platform.system() in ("Linux", "Darwin")
        or is_wsl2()
    )
    # A Windows-native run while WSL2 exists almost always means the user typed
    # `claude` in a WSL2 shell but PATH interop resolved it to the Windows binary
    # (no Linux-native CLI installed in Ubuntu). Flag it so /doctor can give a
    # targeted fix instead of the generic "install WSL2" message.
    wrong_runner_suspected = (
        platform.system() == "Windows" and shutil.which("wsl") is not None
    )
    scopes = _gh_scopes()
    pat_kind = _gh_pat_kind()
    node_supported = _node_supported()
    info = {
        "schema_version": 5,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system().lower(),  # 'windows' | 'linux' | 'darwin'
        "platform_release": platform.release(),
        "platform_supported": platform_supported,
        "wrong_runner_suspected": wrong_runner_suspected,
        "node_supported": node_supported,
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
        "tool_versions": {
            "git": _tool_version(["git", "--version"]),
            "gh": _tool_version(["gh", "--version"]),
            "docker": _tool_version(["docker", "--version"]),
            "node": _tool_version(["node", "--version"]),
            "python": _tool_version([sys.executable, "--version"]),
        },
        "gh": {
            "available": shutil.which("gh") is not None,
            "scopes": scopes,
            "has_repo_scope": "repo" in scopes,
            "has_workflow_scope": "workflow" in scopes,
            "has_admin_scope": any(s.startswith("admin:") for s in scopes),
            "pat_kind": pat_kind,
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
    if wrong_runner_suspected:
        print(
            "WRONG RUNNER: platform=windows but WSL2 is installed -- you launched "
            "the Windows `claude`, not the WSL2-native one.",
            file=sys.stderr,
        )
        print(
            "Fix: in a WSL2 Ubuntu shell run `npm install -g @anthropic-ai/claude-code`, "
            "then `hash -r` and relaunch `claude` from there "
            "(see README -> 'Where this runs').",
            file=sys.stderr,
        )
    if not node_supported:
        node_ver = info["tool_versions"]["node"]
        detail = f"found {node_ver}" if node_ver else "node not on PATH"
        print(
            f"NO_NODE: Node.js 18+ is required ({detail}). It is needed to install "
            "the WSL2-native Claude Code CLI. Install Node 18+ (nvm recommended), "
            "then `npm install -g @anthropic-ai/claude-code`.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
