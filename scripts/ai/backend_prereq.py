"""Run derived Django gates with explicit isolation and pin prerequisites.

Exit 75 means the exact runner must report NOT_VERIFIED rather than PASS.
The wrapper runs only inside the runner's disposable candidate export.
"""

import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from urllib import error as urlerror
from urllib import request as urlrequest

from backend_fixture import docker, inspect, read_marker

NOT_VERIFIED = 75


def run_live_conformance(root: Path, env: dict[str, str], shell: str, token: str) -> int:
    """Migrate the owned DB and run strict conformance on an inherited socket.

    Args: root is the disposable candidate export; env contains only a verified
        fixture DSN and allowlisted runtime values; shell is runner Bash;
        token is the verified marker's random service identity.
    Returns: Conformance exit code, or 75 if server/health is unavailable.
    Raises: OSError for unexpected local socket or process setup errors.
    Side effects: Applies migrations only to the verified ephemeral DB, starts
        one candidate WSGI child on a parent-bound loopback socket, probes its
        documented health route, then terminates that exact child in finally.
    Business rule: Health must return 200/ok plus this process's token header;
        no arbitrary localhost service or inherited DATABASE_URL is accepted.
    """
    if not sys.platform.startswith("linux") or not (root / "backend/manage.py").is_file():
        print("backend gate: Linux candidate manage.py unavailable", file=sys.stderr)
        return NOT_VERIFIED
    migrated = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                              cwd=root / "backend", env=env, check=False, timeout=120)
    if migrated.returncode:
        return migrated.returncode
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    process = None
    try:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        child_env = {**env, "AI_FIXTURE_TOKEN": token}
        process = subprocess.Popen(
            [sys.executable, "scripts/ai/backend_server.py", "--fd", str(listener.fileno())],
            cwd=root, env=child_env, pass_fds=(listener.fileno(),),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        listener.close()
        healthy = False
        for _ in range(20):
            if process.poll() is not None:
                break
            try:
                with urlrequest.urlopen(f"http://127.0.0.1:{port}/api/v1/health/", timeout=1) as response:
                    healthy = (response.status == 200
                               and response.headers.get("X-AI-Fixture-Token") == token
                               and json.loads(response.read(128)) == {"status": "ok"})
            except (OSError, ValueError, urlerror.URLError):
                pass
            if healthy and process.poll() is None:
                break
            healthy = False
            time.sleep(0.25)
        if not healthy:
            print("backend gate: run-owned live health route unavailable", file=sys.stderr)
            return NOT_VERIFIED
        child_env["CONFORMANCE_BASE_URL"] = f"http://127.0.0.1:{port}"
        return subprocess.run([shell, "scripts/check_contract_conformance.sh"],
                              cwd=root, env=child_env, check=False, timeout=420).returncode
    finally:
        listener.close()
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


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
                return run_live_conformance(root, env, shell, marker["token"])
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
