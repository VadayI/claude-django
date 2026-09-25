#!/usr/bin/env python3
"""Claude SessionStart adapter for explicit environment detection.

Runs two visible probes and reports their real exit status: the shared family
detector (``scripts/ai/detector.py --write`` → ``.ai-runtime/environment.json``)
and the Django stack probe (``scripts/detect-env.py`` → ``.ai-runtime/env-detect.json``).
It then prints the shared session context (``scripts/ai/session_context.py``:
Git state, documentation map, latest session record) without reading
``.ai-runtime``. The adapter never touches Git locks, secrets, dependencies,
services, or project files.
"""

from pathlib import Path
import os
import subprocess
import sys


def main() -> int:
    """Run both probes and print the session context, exposing the first failure.

    Args: None; the script path identifies the project root.
    Returns: 0 when every step succeeds, the first nonzero exit code
        otherwise, or 2 if a suitable Python cannot start them.
    Raises: None; supported launch errors are reported on stderr.
    Side effects: Runs detector.py and detect-env.py, which write only their
        documented gitignored runtime reports, then session_context.py, which
        only reads Git/project documents. No Git lock deletion, env seeding,
        Docker, install, database, secret read, push, merge, or project file
        mutation occurs here.
    Business rule: Failed detection is visible rather than a green session; a
        failing shared detector does not skip the stack probe or the context.
        Continuity findings (e.g. no session record yet) do not fail the start;
        only an invalid documentation map or settings file does.
    """
    root = Path(__file__).resolve().parent.parent
    launcher = os.environ.get("AI_PYTHON", sys.executable)
    if launcher == sys.executable and sys.version_info < (3, 13):
        print("session-start: set AI_PYTHON to Python 3.13+", file=sys.stderr)
        return 2
    # Kolejność: wspólny detektor (raport kanoniczny), probe stacku Django,
    # na końcu kontekst sesji dla agenta (bez .ai-runtime).
    commands = (
        [launcher, str(root / "scripts" / "ai" / "detector.py"), "--repository", str(root), "--write"],
        [launcher, str(root / "scripts" / "detect-env.py")],
        [launcher, str(root / "scripts" / "ai" / "session_context.py"), "--root", str(root)],
    )
    status = 0
    for argv in commands:
        try:
            code = subprocess.run(argv, cwd=root, check=False).returncode
        except OSError as error:
            print(f"session-start: detector unavailable: {error}", file=sys.stderr)
            return 2
        if code and not status:
            status = code
    return status


if __name__ == "__main__":
    raise SystemExit(main())
