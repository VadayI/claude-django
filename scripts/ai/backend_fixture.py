"""Own an ephemeral PostgreSQL container for one exact-runner job.

The host workflow starts and stops the fixture. Candidate checks only verify
its identity through the private TMPDIR marker; they never discover ports.
"""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

MARKER = "django-backend-fixture.json"
LABEL = "ai.django.fixture"
IMAGE = "postgres:18"
IDENTIFIER = re.compile(r"[0-9a-f]{64}\Z")


def docker(*args: str) -> str:
    """Run one Docker CLI command without shell interpolation.

    Args: args are literal Docker subcommand arguments.
    Returns: Stripped standard output.
    Raises: OSError or CalledProcessError when Docker is unavailable/fails.
    Side effects: Docker command may inspect, create, or remove one container.
    Business rule: Only the local Linux Docker socket is allowed; inherited
        remote DOCKER_HOST/context settings cannot redirect fixture commands.
    """
    socket = Path("/var/run/docker.sock")
    if not sys.platform.startswith("linux") or not socket.exists():
        raise ValueError("Local Linux Docker socket unavailable")
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
    return subprocess.run(["docker", "--host", "unix:///var/run/docker.sock", *args],
                          check=True, text=True, capture_output=True, timeout=60,
                          env=env).stdout.strip()


def inspect(marker: dict[str, str]) -> int:
    """Verify exact container identity and discover its loopback host port.

    Args: marker contains generated token, full container ID, and name.
    Returns: TCP host port for the owned running PostgreSQL container.
    Raises: ValueError or Docker errors for missing/mismatched identity/port.
    Side effects: Read-only Docker inspect; no database or filesystem writes.
    Business rule: A listening localhost port alone never establishes ownership.
    """
    identifier = marker.get("container_id", "")
    token = marker.get("token", "")
    if not IDENTIFIER.fullmatch(identifier) or not re.fullmatch(r"[0-9a-f]{32}", token):
        raise ValueError("Invalid fixture identity")
    document = json.loads(docker("inspect", identifier))
    if not isinstance(document, list) or len(document) != 1:
        raise ValueError("Container inspect is ambiguous")
    item = document[0]
    if (item.get("Id") != identifier or item.get("Name") != "/" + marker.get("name", "")
            or item.get("Config", {}).get("Labels", {}).get(LABEL) != token
            or item.get("Config", {}).get("Image") != IMAGE
            or item.get("State", {}).get("Running") is not True):
        raise ValueError("Fixture container identity mismatch")
    bindings = item.get("NetworkSettings", {}).get("Ports", {}).get("5432/tcp")
    if (not isinstance(bindings, list) or len(bindings) != 1
            or bindings[0].get("HostIp") != "127.0.0.1"):
        raise ValueError("Fixture is not bound to one loopback port")
    port = bindings[0].get("HostPort", "")
    if not isinstance(port, str) or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ValueError("Invalid fixture port")
    return int(port)


def marker_path(directory: Path) -> Path:
    """Resolve the private marker without following a symlinked directory.

    Args: directory is the explicitly created job TMPDIR.
    Returns: Path of the expected marker in that directory.
    Raises: ValueError for relative, missing, or symlinked directories.
    Side effects: Reads path metadata only; no database/network/writes.
    """
    if not directory.is_absolute() or directory.is_symlink() or not directory.is_dir():
        raise ValueError("Fixture TMPDIR must be an existing absolute directory")
    return directory / MARKER


def read_marker(directory: Path) -> dict[str, str]:
    """Load one private fixture marker with strict expected fields.

    Args: directory is the run-owned TMPDIR.
    Returns: Marker data including generated DB password.
    Raises: OSError/ValueError for missing, symlinked, or malformed marker.
    Side effects: Reads one local file; no database/network/writes.
    """
    path = marker_path(directory)
    if path.is_symlink():
        raise ValueError("Fixture marker cannot be a symlink")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict)
            or set(data) != {"schema_version", "container_id", "name", "token", "password"}
            or data["schema_version"] != 1
            or not isinstance(data["password"], str)
            or not re.fullmatch(r"[0-9a-f]{48}", data["password"])):
        raise ValueError("Invalid fixture marker")
    return data


def start(directory: Path) -> None:
    """Create one fresh Docker PostgreSQL service and private ownership marker.

    Args: directory is a new private TMPDIR created by the host workflow.
    Returns: None after the container passes identity and readiness checks.
    Raises: OSError/ValueError/Docker errors for unsafe or unavailable fixture.
    Side effects: Creates one container, marker and short-lived env file; on
        failure removes only the exact created container and owned files.
    Business rule: Docker assigns a random loopback port; no existing service
        or production DATABASE_URL is consulted.
    """
    path = marker_path(directory)
    if path.exists() or path.is_symlink() or any(directory.iterdir()):
        raise ValueError("Fixture TMPDIR must be empty")
    token = secrets.token_hex(16)
    password = secrets.token_hex(24)
    name = f"ai-django-{token}"
    env_file = directory / "postgres.env"
    identifier = ""
    try:
        env_file.write_text(f"POSTGRES_DB=app\nPOSTGRES_USER=app\nPOSTGRES_PASSWORD={password}\n",
                            encoding="utf-8")
        env_file.chmod(0o600)
        identifier = docker("run", "--rm", "--detach", "--name", name,
                            "--label", f"{LABEL}={token}", "--publish", "127.0.0.1::5432",
                            "--env-file", str(env_file), IMAGE)
        marker = {"schema_version": 1, "container_id": identifier,
                  "name": name, "token": token, "password": password}
        inspect(marker)
        ready = False
        for _ in range(20):
            try:
                docker("exec", identifier, "pg_isready", "-U", "app", "-d", "app")
                ready = True
                break
            except subprocess.CalledProcessError:
                time.sleep(1)
        if not ready:
            raise ValueError("Fixture PostgreSQL readiness timed out")
        with path.open("x", encoding="utf-8") as stream:
            json.dump(marker, stream, sort_keys=True)
            stream.write("\n")
        path.chmod(0o600)
    except BaseException:
        if identifier and IDENTIFIER.fullmatch(identifier):
            try:
                docker("rm", "--force", identifier)
            except (OSError, subprocess.SubprocessError):
                pass
        path.unlink(missing_ok=True)
        raise
    finally:
        env_file.unlink(missing_ok=True)


def stop(directory: Path) -> None:
    """Remove only a marker-matched run-owned container and local marker.

    Args: directory is the exact job TMPDIR used at start.
    Returns: None after container removal or when no marker was ever written.
    Raises: ValueError/Docker errors for identity mismatch; fails closed.
    Side effects: Removes one verified Docker container and marker; never
        removes an unknown container or recursively deletes project files.
    """
    path = marker_path(directory)
    if not path.exists() and not path.is_symlink():
        return
    marker = read_marker(directory)
    inspect(marker)
    docker("rm", "--force", marker["container_id"])
    path.unlink()


def main() -> int:
    """Dispatch explicit host fixture lifecycle operations.

    Args: CLI command is start/stop and --directory is an absolute TMPDIR.
    Returns: Zero on success; two for unavailable/invalid Docker fixture.
    Raises: None; expected lifecycle errors are reported without credentials.
    Side effects: Delegates to start/stop; never touches production DB or Git.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "stop"))
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    try:
        (start if args.command == "start" else stop)(args.directory)
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"backend fixture {args.command} failed: {type(error).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
