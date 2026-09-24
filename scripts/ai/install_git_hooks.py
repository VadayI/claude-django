"""Connect lightweight project hooks without replacing foreign hooks."""

import argparse
from pathlib import Path
import stat
import subprocess
import sys


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one local Git query or configuration command without a shell.

    Args: root is the repository; args are separate Git argv entries.
    Returns: Completed process with captured UTF-8 output.
    Raises: OSError if Git cannot start.
    Side effects: Reads Git state; only callers passing config may change local
        core.hooksPath. No database, network, global config, refs, or index.
    """
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", check=False)


def install(root: Path, check: bool = False) -> int:
    """Connect .githooks only when no foreign hook configuration exists.

    Args: root is the project repository; check requests read-only status.
    Returns: 0 connected, 1 incompatible or absent in check mode, 2 on Git error.
    Raises: OSError for filesystem/Git launch failures.
    Side effects: Apply makes the two delivered hooks executable and sets
        repository-local core.hooksPath; no global or foreign hook edits, DB,
        or network access.
    Business rule: Existing configured paths or active default hook files are
        preserved for a manual reviewed chain instead of being overwritten.
    """
    if git(root, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return 2
    configured = git(root, "config", "--local", "--get", "core.hooksPath")
    path = configured.stdout.strip() if configured.returncode == 0 else ""
    if path.replace("\\", "/").rstrip("/") == ".githooks":
        return 0
    if path:
        print(f"Existing core.hooksPath preserved: {path}; chain hooks manually", file=sys.stderr)
        return 1
    for name in ("pre-commit", "pre-push"):
        location = git(root, "rev-parse", "--git-path", f"hooks/{name}")
        if location.returncode:
            return 2
        hook = Path(location.stdout.strip())
        if not hook.is_absolute():
            hook = root / hook
        if hook.exists():
            print(f"Existing default Git hook preserved: {name}; chain manually", file=sys.stderr)
            return 1
    if check:
        return 1
    for name in ("pre-commit", "pre-push"):
        hook = root / ".githooks" / name
        if not hook.is_file():
            print(f"Missing delivered Git hook: {hook}", file=sys.stderr)
            return 2
    for name in ("pre-commit", "pre-push"):
        hook = root / ".githooks" / name
        hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    result = git(root, "config", "--local", "core.hooksPath", ".githooks")
    return 0 if result.returncode == 0 else 2


def main() -> int:
    """Apply or inspect compatible local Git hook integration.

    Args: CLI --target selects a Git project; --apply changes local config;
        absence of --apply is a read-only check.
    Returns: 0 connected, 1 manual chain needed, 2 invalid Git state/error.
    Raises: None for supported OSError; it becomes exit two.
    Side effects: Apply may set repo-local core.hooksPath and executable bits
        on delivered hooks; no DB/network, secret read, global trust change,
        Git refs/index, release, or merge.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        return install(args.target.absolute(), check=not args.apply)
    except OSError as error:
        print(f"Git hook install error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
