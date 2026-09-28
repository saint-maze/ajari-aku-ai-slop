"""Unit tests for Git repository inspection and error handling."""

import os
import subprocess
import unittest
from unittest.mock import patch

from sysmon_cli.git_status import get_git_status


class TestGitStatus(unittest.TestCase):
    """Test Git repository status detection, branch extraction, and error handling."""

    def test_git_status_inside_repo(self):
        # Current workspace is an initialized git repository
        cwd = os.getcwd()
        res = get_git_status(repo_path=cwd)
        self.assertTrue(res["is_repo"])
        self.assertIn("branch", res)
        self.assertTrue(len(res["branch"]) > 0)
        self.assertIn("is_clean", res)
        self.assertIn("is_dirty", res)
        self.assertIn("staged_count", res)
        self.assertIn("unstaged_count", res)
        self.assertIn("untracked_count", res)
        self.assertIn("total_changes", res)
        self.assertIn("latest_commit", res)

        if res["latest_commit"]:
            self.assertIn("hash", res["latest_commit"])
            self.assertIn("message", res["latest_commit"])

    def test_git_status_nonexistent_path(self):
        res = get_git_status(repo_path="C:\\NonExistent\\Path\\12345")
        self.assertFalse(res["is_repo"])
        self.assertIn("error", res)
        self.assertIn("does not exist", res["error"])

    @patch("shutil.which")
    def test_git_status_missing_git_executable(self, mock_which):
        mock_which.return_value = None
        res = get_git_status(repo_path=".")
        self.assertFalse(res["is_repo"])
        self.assertIn("error", res)
        self.assertIn("not found", res["error"].lower())

    @patch("subprocess.run")
    def test_git_status_outside_git_repo(self, mock_run):
        # Simulate rev-parse failing because path is not in a git repo
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--is-inside-work-tree"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        )
        res = get_git_status(repo_path=".")
        self.assertFalse(res["is_repo"])
        self.assertIn("error", res)
        self.assertIn("not a git repository", res["error"].lower())

    @patch("subprocess.run")
    def test_git_status_detached_head(self, mock_run):
        # 1st call: rev-parse --is-inside-work-tree -> true
        # 2nd call: rev-parse --show-toplevel -> /repo
        # 3rd call: symbolic-ref -> fails (detached)
        # 4th call: branch --show-current -> empty
        # 5th call: rev-parse --short HEAD -> a1b2c3d
        # 6th call: status --porcelain=v1 -> empty
        # 7th call: log -1 -> hash|author|email|date|msg
        # 8th call: rev-parse @{u} -> fails
        def side_effect(cmd, **kwargs):
            subcmd = cmd[1:]
            if subcmd[0] == "rev-parse" and "--is-inside-work-tree" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "true\n", "")
            if subcmd[0] == "rev-parse" and "--show-toplevel" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "/test_repo\n", "")
            if subcmd[0] == "symbolic-ref":
                return subprocess.CompletedProcess(cmd, 1, "", "fatal: ref HEAD is not a symbolic ref")
            if subcmd[0] == "branch" and "--show-current" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if subcmd[0] == "rev-parse" and "--short" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "fedcba9\n", "")
            if subcmd[0] == "status":
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if subcmd[0] == "log":
                return subprocess.CompletedProcess(cmd, 0, "fedcba9|Tester|t@ex.com|1m ago|Test commit\n", "")
            if subcmd[0] == "rev-parse" and "@{u}" in subcmd:
                return subprocess.CompletedProcess(cmd, 1, "", "no upstream")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        mock_run.side_effect = side_effect
        res = get_git_status(repo_path=".")
        self.assertTrue(res["is_repo"])
        self.assertIn("detached", res["branch"])
        self.assertTrue(res["is_clean"])
        self.assertFalse(res["is_dirty"])

    def test_git_status_file_path(self):
        # Inspecting a file inside the repository resolves repository correctly
        pyproj = os.path.join(os.getcwd(), "pyproject.toml")
        res = get_git_status(repo_path=pyproj)
        self.assertTrue(res["is_repo"])
        self.assertIn("branch", res)

    @patch("subprocess.run")
    def test_git_status_utf8_commit(self, mock_run):
        def side_effect(cmd, **kwargs):
            subcmd = cmd[1:]
            if subcmd[0] == "rev-parse" and "--is-inside-work-tree" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "true\n", "")
            if subcmd[0] == "rev-parse" and "--show-toplevel" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "/test_repo\n", "")
            if subcmd[0] == "symbolic-ref":
                return subprocess.CompletedProcess(cmd, 0, "main\n", "")
            if subcmd[0] == "status":
                return subprocess.CompletedProcess(cmd, 0, "", "")
            if subcmd[0] == "log":
                return subprocess.CompletedProcess(cmd, 0, "1a2b3c4|René François|rene@ex.com|2h ago|feat: ✨ support emoji & 日本語\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "")

        mock_run.side_effect = side_effect
        res = get_git_status(repo_path=".")
        self.assertTrue(res["is_repo"])
        self.assertEqual(res["latest_commit"]["author_name"], "René François")
        self.assertIn("✨ support emoji & 日本語", res["latest_commit"]["message"])

    @patch("subprocess.run")
    def test_git_status_bare_repo(self, mock_run):
        def side_effect(cmd, **kwargs):
            subcmd = cmd[1:]
            if subcmd[0] == "rev-parse" and "--is-inside-work-tree" in subcmd:
                return subprocess.CompletedProcess(cmd, 128, "", "fatal: this operation must be run in a work tree")
            if subcmd[0] == "rev-parse" and "--is-bare-repository" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "true\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "")

        mock_run.side_effect = side_effect
        res = get_git_status(repo_path=".")
        self.assertTrue(res["is_repo"])
        self.assertTrue(res.get("bare"))
        self.assertEqual(res["branch"], "(bare repository)")
        self.assertTrue(res["is_clean"])
        self.assertIsNone(res["latest_commit"])

    @patch("subprocess.run")
    def test_git_status_bare_repo_with_commits(self, mock_run):
        def side_effect(cmd, **kwargs):
            subcmd = cmd[1:]
            if subcmd[0] == "rev-parse" and "--is-inside-work-tree" in subcmd:
                return subprocess.CompletedProcess(cmd, 128, "", "fatal: this operation must be run in a work tree")
            if subcmd[0] == "rev-parse" and "--is-bare-repository" in subcmd:
                return subprocess.CompletedProcess(cmd, 0, "true\n", "")
            if subcmd[0] == "log":
                return subprocess.CompletedProcess(cmd, 0, "c0ffee1\x1fBare Author\x1fbare@ex.com\x1f1d ago\x1fBare commit message\n", "")
            return subprocess.CompletedProcess(cmd, 1, "", "")

        mock_run.side_effect = side_effect
        res = get_git_status(repo_path=".")
        self.assertTrue(res["is_repo"])
        self.assertTrue(res.get("bare"))
        self.assertIsNotNone(res["latest_commit"])
        self.assertEqual(res["latest_commit"]["hash"], "c0ffee1")
        self.assertEqual(res["latest_commit"]["author_name"], "Bare Author")
        self.assertEqual(res["latest_commit"]["message"], "Bare commit message")

    @patch("subprocess.run")
    def test_git_status_command_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git"], timeout=10.0)
        res = get_git_status(repo_path=".")
        self.assertFalse(res["is_repo"])
        self.assertIn("timed out", res["error"].lower())


if __name__ == "__main__":
    unittest.main()
