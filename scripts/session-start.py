#!/usr/bin/env python3
"""Claude SessionStart adapter for explicit environment detection.

The detector may update its documented runtime report. The adapter never
touches Git locks, secrets, dependencies, services, or project files.
"""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    """Run the project's detector and expose its real exit status.

    Args: None; the script path identifies the project root.
    Returns: The detector exit code, or 2 if Python cannot start it.
    Raises: None; supported launch errors are reported on stderr.
    Side effects: Runs detect-env.py, which may write its documented runtime
        report. No Git lock deletion, env seeding, Docker, install, database,
        secret read, push, merge, or project file mutation occurs here.
    Business rule: Failed detection is visible rather than a green session.
    """
    root = Path(__file__).resolve().parent.parent
    detector = root / "scripts" / "detect-env.py"
    try:
        return subprocess.run([sys.executable, str(detector)], cwd=root, check=False).returncode
    except OSError as error:
        print(f"session-start: detector unavailable: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
