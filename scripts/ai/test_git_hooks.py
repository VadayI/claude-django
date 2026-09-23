"""Verify Django index hooks, per-ref push checks, and hook path ownership."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_hooks
import install_git_hooks


class GitHookTests(unittest.TestCase):
    """Exercise hook behavior without changing the source repository."""

    def test_precommit_checks_staged_patch_only(self):
        """Reject staged whitespace errors while ignoring unstaged edits.

        Args: None; a temporary repository supplies staged and unstaged bytes.
        Returns: None after index-only assertions.
        Raises: AssertionError for an incorrect staged-index policy.
        Side effects: Temporary Git commits and file edits; no DB or network.
        """
        with tempfile.TemporaryDirectory(prefix="django index hook ") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
            file = root / "app" / "views.py"
            file.parent.mkdir()
            file.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "baseline"], check=True)
            file.write_text("VALUE = 2\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            file.write_text("VALUE = 2   \n", encoding="utf-8")
            self.assertEqual(git_hooks.pre_commit(root), 0)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            file.write_text("VALUE = 2\n", encoding="utf-8")
            self.assertEqual(git_hooks.pre_commit(root), 1)

    def test_prepush_checks_each_ref_and_creation_base(self):
        """Run exact checks on two branches and skip only a deletion.

        Args: None; mocked Git and runner model three stdin records.
        Returns: None after candidate/base assertions.
        Raises: AssertionError for missing or incorrect runner calls.
        Side effects: No filesystem, DB, or network; all subprocesses mocked.
        """
        old, first, second, zero = "a" * 40, "b" * 40, "c" * 40, "0" * 40
        updates = git_hooks.ref_updates(
            f"refs/heads/one {first} refs/heads/one {old}\n"
            f"refs/heads/two {second} refs/heads/two {zero}\n"
            f"(delete) {zero} refs/heads/gone {old}\n"
        )

        def fake_git(_root: Path, *args: str) -> bytes:
            """Resolve fixture refs without invoking Git.

            Args: _root is unused; args are Git command words.
            Returns: Matching fixture OID as bytes.
            Raises: AssertionError for any unreviewed Git command.
            Side effects: None; no DB, filesystem, or network.
            """
            if args[-1] == "refs/heads/one^{commit}":
                return (first + "\n").encode()
            if args[-1] == "refs/heads/two^{commit}":
                return (second + "\n").encode()
            raise AssertionError(args)

        with mock.patch.object(git_hooks, "git", side_effect=fake_git), mock.patch.object(
            git_hooks, "assert_candidate_tooling"
        ), mock.patch.object(
            git_hooks, "creation_base", return_value=old
        ) as creation, mock.patch.object(
            git_hooks.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as runner:
            self.assertEqual(git_hooks.pre_push(Path("C:/fixture"), updates, "github"), 0)
            self.assertEqual(runner.call_count, 2)
            self.assertEqual([call.args[0][call.args[0].index("--candidate") + 1]
                              for call in runner.call_args_list], [first, second])
            self.assertEqual([call.args[0][call.args[0].index("--base") + 1]
                              for call in runner.call_args_list], [old, old])
            creation.assert_called_once()
        with self.assertRaisesRegex(ValueError, "Tag push"):
            git_hooks.pre_push(Path("C:/fixture"), [("refs/tags/v1", first, "refs/tags/v1", zero)], "github")

    def test_creation_base_requires_verified_remote_main(self):
        """Use merge-base with observed main and reject stale local tracking.

        Args: None; a mocked remote supplies fixed commit IDs.
        Returns: None after fork and stale-tracking assertions.
        Raises: AssertionError when a branch's earlier commits are skipped.
        Side effects: No Git, DB, filesystem, or actual network activity.
        """
        main, fork, candidate = "a" * 40, "b" * 40, "c" * 40

        def response(_root: Path, *args: str) -> bytes:
            """Map the verified remote queries to test commit IDs.

            Args: _root is unused; args are Git command words.
            Returns: Remote, tracking, or fork OID bytes.
            Raises: AssertionError for an unexpected Git query.
            Side effects: None; no DB, disk, or network.
            """
            if args[:2] == ("ls-remote", "--exit-code"):
                return f"{main}\trefs/heads/main\n".encode()
            if args[:2] == ("rev-parse", "--verify"):
                return (main + "\n").encode()
            if args[:1] == ("merge-base",):
                self.assertEqual(args[1:], (main, candidate))
                return (fork + "\n").encode()
            raise AssertionError(args)

        with mock.patch.object(git_hooks, "git", side_effect=response):
            self.assertEqual(git_hooks.creation_base(Path("C:/fixture"), "github", candidate), fork)
        with mock.patch.object(git_hooks, "git", side_effect=lambda _root, *args:
                               f"{main}\trefs/heads/main\n".encode() if args[0] == "ls-remote" else
                               (fork + "\n").encode()):
            with self.assertRaisesRegex(ValueError, "stale"):
                git_hooks.creation_base(Path("C:/fixture"), "github", candidate)

    def test_installer_preserves_foreign_hook_path(self):
        """Connect an empty repo and preserve a foreign hooks directory.

        Args: None; disposable repositories hold repo-local configuration.
        Returns: None after check, apply, repeat, and foreign-path assertions.
        Raises: AssertionError if an existing hooks path is overwritten.
        Side effects: Temporary repo-local Git config only; no global config,
            DB, network, source repository mutation, or installation.
        """
        with tempfile.TemporaryDirectory(prefix="django hook install ") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hooks = root / ".githooks"
            hooks.mkdir()
            for name in ("pre-commit", "pre-push"):
                (hooks / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            self.assertEqual(install_git_hooks.install(root, check=True), 1)
            self.assertEqual(install_git_hooks.install(root), 0)
            self.assertEqual(install_git_hooks.install(root, check=True), 0)
            subprocess.run(["git", "-C", str(root), "config", "--local", "core.hooksPath", "custom/hooks"], check=True)
            self.assertEqual(install_git_hooks.install(root), 1)
            observed = subprocess.check_output(
                ["git", "-C", str(root), "config", "--local", "--get", "core.hooksPath"]
            ).decode().strip()
            self.assertEqual(observed, "custom/hooks")


if __name__ == "__main__":
    unittest.main()
