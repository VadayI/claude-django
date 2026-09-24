"""Run derived Django gates with explicit isolation and pin prerequisites.

Exit 75 means the exact runner must report NOT_VERIFIED rather than PASS.
The wrapper runs only inside the runner's disposable candidate export.
"""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from backend_fixture import docker, inspect, read_marker

NOT_VERIFIED = 75


def pinned_version(path: Path) -> str | None:
    """Read a checked-in contract version without loading private env files.

    Args: path is the candidate's public .env.example file.
    Returns: A nonempty CONTRACT_VERSION value, or None when unresolved.
    Raises: OSError for unreadable existing input.
    Side effects: Reads one public candidate file; no DB, network, or writes.
    Business rule: A private .env value cannot silently define CI provenance.
    """
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"CONTRACT_VERSION=([A-Za-z0-9._-]+)", line.strip())
        if match:
            return match.group(1)
    return None


def run_gate(root: Path, name: str, shell: str) -> int:
    """Run a backend gate only with its declared public/owned prerequisites.

    Args: root is the disposable candidate export; name is a reviewed gate ID;
        shell is the runner-resolved Git Bash or POSIX Bash executable.
    Returns: Child exit code, or 75 for unverified isolation/pin/tooling.
    Raises: ValueError for unsupported gate; OSError for unreadable input.
    Side effects: Drift may fetch the pinned public contract. DB/conformance
        tests may write only to a marker-bound temporary PostgreSQL container;
        no Git refs, production DB, release, or deployment state changes.
    Business rule: An open localhost port does not prove service ownership.
        Missing Docker/marker/matching ID/label/port returns NOT_VERIFIED.
    """
    backend = root / "backend"
    if not backend.is_dir():
        print("backend gate: backend/ unavailable", file=sys.stderr)
        return NOT_VERIFIED
    env = {key: os.environ[key] for key in
           ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR", "LANG", "LC_ALL")
           if key in os.environ}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if name in {"pytest", "conformance"}:
        temporary = os.environ.get("TMPDIR")
        if not temporary:
            print("backend gate: run-owned TMPDIR unavailable", file=sys.stderr)
            return NOT_VERIFIED
        try:
            marker = read_marker(Path(temporary))
            port = inspect(marker)
            docker("exec", marker["container_id"], "pg_isready", "-U", "app", "-d", "app")
        except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
            print("backend gate: run-owned PostgreSQL identity unavailable", file=sys.stderr)
            return NOT_VERIFIED
        env["DATABASE_URL"] = f"postgres://app:{marker['password']}@127.0.0.1:{port}/app"
        env["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
        env["DJANGO_SECRET_KEY"] = marker["token"]
        if name == "pytest":
            command = ["pytest", "--cov=apps", "--cov-report=term-missing"]
            cwd = backend
        else:
            stage_file = root / "docs/PROJECT.md"
            stage = stage_file.read_text(encoding="utf-8") if stage_file.is_file() else ""
            if re.search(r"(?im)^\*\*Maturity stage:\*\*.*\b(MVP|production)\b", stage):
                print("backend gate: strict live conformance server unavailable", file=sys.stderr)
                return NOT_VERIFIED
            command = [shell, "scripts/check_contract_conformance.sh"]
            cwd = root
    elif name == "drift":
        version = pinned_version(root / ".env.example")
        if not version:
            print("backend gate: public CONTRACT_VERSION unavailable", file=sys.stderr)
            return NOT_VERIFIED
        env["CONTRACT_VERSION"] = version
        command = [shell, "scripts/pull_contract.sh", "--check"]
        cwd = root
    else:
        raise ValueError(f"Unsupported backend gate: {name}")
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=False).returncode
    except FileNotFoundError as error:
        print(f"backend gate: command unavailable: {error}", file=sys.stderr)
        return NOT_VERIFIED


def main() -> int:
    """Dispatch a reviewed candidate backend gate from command-line input.

    Args: CLI gate is pytest, conformance, or drift; shell is runner-resolved.
    Returns: 0 pass, 75 unavailable prerequisite, otherwise child failure.
    Raises: None for supported validation errors; argparse reports bad input.
    Side effects: Delegates to run_gate in the candidate export; may run
        tests against the verified ephemeral fixture, never a production DB.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=("pytest", "conformance", "drift"))
    parser.add_argument("shell")
    args = parser.parse_args()
    return run_gate(Path(__file__).resolve().parents[2], args.gate, args.shell)


if __name__ == "__main__":
    raise SystemExit(main())
