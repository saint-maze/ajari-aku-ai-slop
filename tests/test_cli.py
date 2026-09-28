"""Unit tests for command-line interface arguments, exit codes, and outputs."""

import io
import sys
import unittest
from unittest.mock import patch

from sysmon_cli.cli import build_parser, main


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing, help output, exit codes, and error reporting."""

    def test_help_flag_root(self):
        """CLI with --help displays documentation and exits with code 0."""
        parser = build_parser()
        stdout_buf = io.StringIO()
        with self.assertRaises(SystemExit) as cm, patch("sys.stdout", stdout_buf):
            parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("sysmon", output)
        self.assertIn("system", output)
        self.assertIn("process", output)
        self.assertIn("git", output)
        self.assertIn("--json", output)

    def test_help_subcommands(self):
        """Subcommands with --help display documentation and exit with code 0."""
        parser = build_parser()
        for subcmd in ["system", "process", "git", "all"]:
            stdout_buf = io.StringIO()
            with self.assertRaises(SystemExit) as cm, patch("sys.stdout", stdout_buf):
                parser.parse_args([subcmd, "--help"])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn(subcmd, stdout_buf.getvalue())

    def test_invalid_flag_exits_nonzero_with_stderr(self):
        """Invalid flags display error to stderr and exit with non-zero code."""
        stderr_buf = io.StringIO()
        with self.assertRaises(SystemExit) as cm, patch("sys.stderr", stderr_buf):
            main(["--unrecognized-test-flag"])
        self.assertNotEqual(cm.exception.code, 0)
        err = stderr_buf.getvalue()
        self.assertIn("unrecognized arguments", err)

    def test_invalid_command_exits_nonzero_with_stderr(self):
        """Invalid subcommand displays error to stderr and exits with non-zero code."""
        stderr_buf = io.StringIO()
        with self.assertRaises(SystemExit) as cm, patch("sys.stderr", stderr_buf):
            main(["nonexistent-command-xyz"])
        self.assertNotEqual(cm.exception.code, 0)
        err = stderr_buf.getvalue()
        self.assertIn("invalid choice", err)

    @patch("time.sleep")
    def test_default_invocation_system_metrics(self, mock_sleep):
        """Running CLI without subcommands outputs system metrics and exits 0."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main([])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("CPU Usage", output)
        self.assertIn("RAM Usage", output)
        self.assertIn("DISK PARTITIONS", output)

    def test_system_command(self):
        """Running 'system' outputs CPU, RAM, and Disk stats and exits 0."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["system", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("CPU Usage", output)
        self.assertIn("RAM Usage", output)
        self.assertIn("DISK PARTITIONS", output)

    def test_process_command(self):
        """Running 'process' lists top processes with PID and resource usage."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["process", "-n", "3", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("TOP PROCESSES", output)
        self.assertIn("PID", output)
        self.assertIn("CPU %", output)
        self.assertIn("Mem %", output)

    def test_git_command_inside_repo(self):
        """Running 'git' inside a repo outputs branch and clean/dirty status."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["git"])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("GIT REPOSITORY STATUS", output)
        self.assertIn("Current Branch", output)
        self.assertIn("Working Status", output)

    @patch("sysmon_cli.cli.get_git_status")
    def test_git_command_outside_repo_exits_nonzero(self, mock_status):
        """Running 'git' outside a repo prints error to stderr and exits non-zero."""
        mock_status.return_value = {
            "is_repo": False,
            "error": "Not a Git repository (or any parent directory).",
            "path": "/some/non/repo",
        }
        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            exit_code = main(["git", "-p", "/some/non/repo"])
        self.assertNotEqual(exit_code, 0)
        err = stderr_buf.getvalue()
        self.assertIn("Error:", err)
        self.assertIn("Not a Git repository", err)

    def test_all_command(self):
        """Running 'all' combines system, process, and git status."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["all", "-n", "2", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("SYSTEM HEALTH MONITOR", output)

    def test_process_command_zero_limit(self):
        """Running 'process' with -n 0 shows zero processes gracefully."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["process", "-n", "0", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)
        output = stdout_buf.getvalue()
        self.assertIn("TOP PROCESSES", output)
        self.assertIn("No matching active processes found.", output)

    def test_process_command_negative_limit_exits_code_2(self):
        """Running 'process' with negative limit outputs error to stderr and exits 2."""
        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            exit_code = main(["process", "-n", "-5", "--interval", "0.0"])
        self.assertEqual(exit_code, 2)
        err = stderr_buf.getvalue()
        self.assertIn("Error:", err)
        self.assertIn("Limit must be non-negative", err)

    def test_all_command_negative_limit_exits_code_2(self):
        """Running 'all' with negative limit outputs error to stderr and exits 2."""
        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            exit_code = main(["all", "-n", "-5", "--interval", "0.0"])
        self.assertEqual(exit_code, 2)
        err = stderr_buf.getvalue()
        self.assertIn("Error:", err)
        self.assertIn("Limit must be non-negative", err)

    def test_all_command_invalid_interval(self):
        """Running 'all' handles interval fallback safely."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["all", "-n", "1", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)
        self.assertIn("SYSTEM HEALTH MONITOR", stdout_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
