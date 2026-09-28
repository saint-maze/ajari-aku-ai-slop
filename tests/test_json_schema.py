"""Unit tests for JSON output schema validity across all CLI commands."""

import io
import json
import unittest
from unittest.mock import patch

from sysmon_cli.cli import main


class TestJSONSchema(unittest.TestCase):
    """Validate JSON output structure, data types, and numeric constraints."""

    def test_system_json_numeric_metrics(self):
        """Running system inspection with --json outputs valid JSON with numeric metrics."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["system", "--json", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)

        raw_output = stdout_buf.getvalue()
        data = json.loads(raw_output)

        # Validate CPU metrics
        self.assertIn("cpu", data)
        cpu = data["cpu"]
        self.assertIsInstance(cpu["usage_percent"], (int, float))
        self.assertGreaterEqual(cpu["usage_percent"], 0.0)
        self.assertIsInstance(cpu["count_logical"], int)
        self.assertGreaterEqual(cpu["count_logical"], 1)

        # Validate RAM metrics
        self.assertIn("memory", data)
        mem = data["memory"]
        self.assertIsInstance(mem["total_bytes"], int)
        self.assertGreater(mem["total_bytes"], 0)
        self.assertIsInstance(mem["used_bytes"], int)
        self.assertIsInstance(mem["available_bytes"], int)
        self.assertIsInstance(mem["percent"], (int, float))
        self.assertGreaterEqual(mem["percent"], 0.0)
        self.assertLessEqual(mem["percent"], 100.0)

        # Validate Disk metrics
        self.assertIn("disk", data)
        disk = data["disk"]
        self.assertIsInstance(disk, list)
        self.assertGreater(len(disk), 0)
        for part in disk:
            self.assertIsInstance(part["device"], str)
            self.assertIsInstance(part["mountpoint"], str)
            self.assertIsInstance(part["total_bytes"], int)
            self.assertGreater(part["total_bytes"], 0)
            self.assertIsInstance(part["used_bytes"], int)
            self.assertIsInstance(part["free_bytes"], int)
            self.assertIsInstance(part["percent"], (int, float))

    @patch("time.sleep")
    def test_root_json_flag(self, mock_sleep):
        """Running sysmon --json directly outputs valid system metrics in JSON."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["--json"])
        self.assertEqual(exit_code, 0)

        data = json.loads(stdout_buf.getvalue())
        self.assertIn("cpu", data)
        self.assertIn("memory", data)
        self.assertIn("disk", data)

    def test_process_json_schema(self):
        """Running process inspection with --json outputs valid JSON with process list."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["process", "--json", "-n", "3", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)

        data = json.loads(stdout_buf.getvalue())
        self.assertIn("sort_by", data)
        self.assertIn("limit", data)
        self.assertIn("count", data)
        self.assertIn("processes", data)
        self.assertIsInstance(data["processes"], list)

        for p in data["processes"]:
            self.assertIsInstance(p["pid"], int)
            self.assertIsInstance(p["name"], str)
            self.assertIsInstance(p["cpu_percent"], (int, float))
            self.assertIsInstance(p["memory_percent"], (int, float))
            self.assertIsInstance(p["memory_rss_bytes"], int)
            self.assertIsInstance(p["memory_rss_human"], str)

    def test_git_json_schema_inside_repo(self):
        """Running git inspection with --json outputs valid JSON repo status."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["git", "--json"])
        self.assertEqual(exit_code, 0)

        data = json.loads(stdout_buf.getvalue())
        self.assertTrue(data["is_repo"])
        self.assertIsInstance(data["branch"], str)
        self.assertIsInstance(data["is_clean"], bool)
        self.assertIsInstance(data["is_dirty"], bool)
        self.assertIsInstance(data["staged_count"], int)
        self.assertIsInstance(data["unstaged_count"], int)
        self.assertIsInstance(data["untracked_count"], int)

    @patch("sysmon_cli.cli.get_git_status")
    def test_git_json_schema_outside_repo(self, mock_status):
        """Running git inspection with --json outside repo outputs valid JSON error and exits non-zero."""
        mock_status.return_value = {
            "is_repo": False,
            "error": "Not a Git repository.",
            "path": "/fake/dir",
        }
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["git", "--json", "-p", "/fake/dir"])
        self.assertNotEqual(exit_code, 0)

        data = json.loads(stdout_buf.getvalue())
        self.assertFalse(data["is_repo"])
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Not a Git repository.")

    def test_all_json_schema(self):
        """Running all --json outputs consolidated JSON with system, processes, and git."""
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["all", "--json", "-n", "2", "--interval", "0.0"])
        self.assertEqual(exit_code, 0)

        data = json.loads(stdout_buf.getvalue())
        self.assertIn("system", data)
        self.assertIn("processes", data)
        self.assertIn("git", data)


if __name__ == "__main__":
    unittest.main()
