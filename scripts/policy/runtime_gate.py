#!/usr/bin/env python3
"""Shared runtime gate: is this a supported Claude Code CLI runtime?

Single mechanical source of the ``NO_ENV_DETECT`` / ``UNSUPPORTED_PLATFORM``
flags used by ``/doctor`` (Step 0.5 — canonical prose + remediation),
``/preflight`` (Step 0), ``/bootstrap`` (hard preflight), and — via
``/doctor`` — ``/config-check`` and ``/plugins``. Replaces the per-command
re-implementations (2026-07-07 audit, batch D).

Since P07 the gate calls the shared family detector (``scripts/ai/detector.py``)
in-process instead of trusting a JSON file that a hook may or may not have
written: nothing needs to run before it, and a hand-written
``env-detect.json`` cannot satisfy it. Prints exactly one line and always
exits 0 — the calling command interprets the flag and applies /doctor Step
0.5 remediation:

    NO_ENV_DETECT                  shared detector unavailable (Python 3.13+
                                   or scripts/ai/detector.py missing/broken)
    UNSUPPORTED_PLATFORM <name>    platform outside Linux/macOS/Windows
    RUNTIME_OK                     proceed

Stack-specific facts (WSL2, gh PAT kind, shell) stay in the probe report
``.ai-runtime/env-detect.json`` written by ``scripts/detect-env.py``.
Cross-platform (ADR 0022): invoked as ``python`` -- no bash, no jq.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

SUPPORTED_SYSTEMS = ("Linux", "Darwin", "Windows")


def _load_detector():
    """Import the vendored shared detector without a package install.

    Args: None; the module path is fixed relative to this script.
    Returns: The loaded ``detector`` module.
    Raises: ImportError/OSError/SyntaxError when the core file is missing or
        broken; the caller maps that to ``NO_ENV_DETECT``.
    Side effects: Imports one local module; no subprocess, DB, or network.
    """
    path = pathlib.Path(__file__).resolve().parents[1] / "ai" / "detector.py"
    spec = importlib.util.spec_from_file_location("family_detector", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Shared detector not found: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flag() -> str:
    """Compute the runtime flag from a fresh in-process detector report.

    Args: None.
    Returns: One of the documented flag lines.
    Raises: None; every expected failure becomes ``NO_ENV_DETECT``.
    Side effects: Runs the shared detector's bounded local tool probes; writes
        no files and reads no JSON report.
    """
    try:
        report = _load_detector().report()
        system = str(report["platform"]["system"])
    except Exception:  # noqa: BLE001 - dowolna awaria sondy = runtime niezweryfikowany
        return "NO_ENV_DETECT"
    if system not in SUPPORTED_SYSTEMS:
        return f"UNSUPPORTED_PLATFORM {system or 'unknown'}"
    return "RUNTIME_OK"


def main() -> int:
    """Print one runtime flag (see module docstring); never block (exit 0)."""
    print(flag())
    return 0


if __name__ == "__main__":
    sys.exit(main())
