"""Run derived Django gates with explicit DB, server, and pin prerequisites.

Exit 75 means the exact runner must report NOT_VERIFIED rather than PASS.
The wrapper runs only inside the runner's disposable candidate export.
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys

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


def port_available(host: str, port: int) -> bool:
    """Probe a declared local service before running database-backed checks.

    Args: host is loopback name; port is PostgreSQL or HTTP port.
    Returns: True when a short TCP connection succeeds.
    Raises: None; connection failures return False.
    Side effects: Opens and closes one loopback socket; no DB queries, writes,
        external network access, or project mutation.
    Business rule: An absent service yields NOT_VERIFIED, never a green skip.
    """
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def run_gate(root: Path, name: str, shell: str) -> int:
    """Run one exact derived backend gate after checking its prerequisites.

    Args: root is the disposable candidate export; name is a reviewed gate ID;
        shell is the runner-resolved Git Bash or POSIX Bash executable.
    Returns: Child exit code, or 75 for an absent DB/server/pin/tooling input.
    Raises: ValueError for unsupported gate; OSError for unreadable input.
    Side effects: Drift may fetch the pinned public contract; conformance and
        pytest may query local services and write declared transient test
        outputs. No project Git refs, secrets, release, or deployment change.
    Business rule: A failed executed gate is FAIL; unavailable prerequisites
        are NOT_VERIFIED through the runner's exit-code protocol.
    """
    backend = root / "backend"
    if not backend.is_dir():
        print("backend gate: backend/ unavailable", file=sys.stderr)
        return NOT_VERIFIED
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
    env["DJANGO_SECRET_KEY"] = "ci-nonsecret-test-key"
    env["DATABASE_URL"] = "postgres://app:app@localhost:5432/app"
    if name == "pytest":
        if not port_available("127.0.0.1", 5432):
            print("backend gate: PostgreSQL unavailable", file=sys.stderr)
            return NOT_VERIFIED
        command = [sys.executable, "-m", "pytest", "--cov=apps", "--cov-report=term-missing"]
        cwd = backend
    elif name == "conformance":
        if (not (root / "docs/api/openapi.yml").is_file()
                or not port_available("127.0.0.1", 8000)
                or not port_available("127.0.0.1", 5432)):
            print("backend gate: contract, live server, or PostgreSQL unavailable", file=sys.stderr)
            return NOT_VERIFIED
        if not shutil.which("schemathesis") or not shutil.which("pytest"):
            print("backend gate: schemathesis or pytest unavailable", file=sys.stderr)
            return NOT_VERIFIED
        env["CONFORMANCE_BASE_URL"] = "http://127.0.0.1:8000"
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
    Side effects: Delegates to run_gate in the candidate export only; no Git,
        database schema mutation by this wrapper, secret read, or deployment.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", choices=("pytest", "conformance", "drift"))
    parser.add_argument("shell")
    args = parser.parse_args()
    return run_gate(Path(__file__).resolve().parents[2], args.gate, args.shell)


if __name__ == "__main__":
    raise SystemExit(main())
