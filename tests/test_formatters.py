"""Unit tests for human-readable terminal formatters and JSON serialization."""

import json
import unittest

from sysmon_cli.formatters import (
    format_all_report,
    format_git_report,
    format_process_report,
    format_system_report,
    to_json,
)


class TestFormatters(unittest.TestCase):
    """Test formatting edge cases, missing data, and None/NaN handling."""

    def test_format_system_report_full(self):
        data = {
            "platform": {
                "system": "Linux",
                "release": "6.1.0",
                "hostname": "workstation",
                "uptime_seconds": 7320,
            },
            "cpu": {
                "usage_percent": 24.5,
                "count_logical": 8,
                "count_physical": 4,
                "frequency_mhz": {"current": 3200.0},
            },
            "memory": {
                "percent": 45.2,
                "used_human": "7.20 GB",
                "total_human": "16.00 GB",
                "available_human": "8.80 GB",
            },
            "swap": {
                "total_bytes": 2048,
                "percent": 12.0,
                "used_human": "245 MB",
                "total_human": "2.00 GB",
            },
            "disk": [
                {
                    "device": "/dev/sda1",
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "total_human": "500 GB",
                    "used_human": "200 GB",
                    "free_human": "300 GB",
                    "percent": 40.0,
                }
            ],
        }
        output = format_system_report(data)
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("workstation", output)
        self.assertIn("Linux 6.1.0", output)
        self.assertIn("2h 2m", output)
        self.assertIn("CPU Usage:", output)
        self.assertIn("24.5%", output)
        self.assertIn("RAM Usage:", output)
        self.assertIn("45.2%", output)
        self.assertIn("Swap Usage:", output)
        self.assertIn("/dev/sda1", output)

    def test_format_system_report_empty_and_none_values(self):
        # Empty dict or dict with None values must not raise TypeError
        data = {
            "platform": {},
            "cpu": {"usage_percent": None, "count_logical": None, "count_physical": None, "frequency_mhz": None},
            "memory": {"percent": None, "used_human": None, "total_human": None, "available_human": None},
            "swap": None,
            "disk": [],
        }
        output = format_system_report(data)
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("CPU Usage:", output)
        self.assertIn("0.0%", output)
        self.assertIn("RAM Usage:", output)
        self.assertIn("No disk partitions detected.", output)

    def test_format_system_report_nan_values(self):
        data = {
            "platform": {"uptime_seconds": None},
            "cpu": {"usage_percent": float("nan")},
            "memory": {"percent": float("nan")},
            "swap": {"total_bytes": 1000, "percent": float("nan")},
            "disk": [{"device": "C:", "percent": float("nan")}],
        }
        output = format_system_report(data)
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("0.0%", output)

    def test_format_system_report_inf_and_invalid_string_types(self):
        # float('inf') uptime must not crash with OverflowError
        # Invalid string numbers must not crash with ValueError
        data = {
            "platform": {"uptime_seconds": float("inf")},
            "cpu": {"usage_percent": "corrupted", "count_logical": "invalid", "frequency_mhz": {"current": "bad"}},
            "memory": {"percent": "invalid"},
            "swap": {"total_bytes": 1000, "percent": "bad"},
            "disk": [{"device": "C:", "percent": "unparseable"}],
        }
        output = format_system_report(data)
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("Uptime: N/A", output)
        self.assertIn("0.0%", output)

    def test_format_process_report_empty(self):
        data = {"sort_by": "cpu", "count": 0, "limit": 10, "processes": []}
        output = format_process_report(data)
        self.assertIn("TOP PROCESSES (RANKED BY CPU)", output)
        self.assertIn("No matching active processes found.", output)

    def test_format_process_report_with_items(self):
        data = {
            "sort_by": "memory",
            "count": 2,
            "limit": 5,
            "processes": [
                {
                    "pid": 1234,
                    "name": "python.exe",
                    "cpu_percent": 12.3,
                    "memory_percent": 5.4,
                    "memory_rss_human": "256 MB",
                    "status": "running",
                },
                {
                    "pid": 5678,
                    "name": "node.exe",
                    "cpu_percent": None,
                    "memory_percent": float("nan"),
                    "memory_rss_human": "128 MB",
                    "status": "sleeping",
                },
            ],
        }
        output = format_process_report(data)
        self.assertIn("TOP PROCESSES (RANKED BY MEMORY)", output)
        self.assertIn("1234", output)
        self.assertIn("python.exe", output)
        self.assertIn("12.3%", output)
        self.assertIn("5678", output)
        self.assertIn("0.0%", output)

    def test_format_process_report_invalid_types_and_none_pid(self):
        data = {
            "sort_by": "cpu",
            "count": 1,
            "limit": 5,
            "processes": [
                {
                    "pid": None,
                    "name": None,
                    "cpu_percent": "corrupted",
                    "memory_percent": "bad",
                    "memory_rss_human": None,
                    "status": None,
                },
            ],
        }
        output = format_process_report(data)
        self.assertIn("TOP PROCESSES (RANKED BY CPU)", output)
        self.assertIn("unknown", output)
        self.assertIn("0.0%", output)

    def test_format_git_report_not_repo(self):
        data = {
            "is_repo": False,
            "error": "Not a Git repository.",
            "path": "/some/path",
        }
        output = format_git_report(data)
        self.assertIn("Error: Not a Git repository.", output)
        self.assertIn("/some/path", output)

    def test_format_git_report_clean(self):
        data = {
            "is_repo": True,
            "root_dir": "/repo",
            "branch": "main",
            "is_clean": True,
            "is_dirty": False,
            "total_changes": 0,
            "latest_commit": {
                "hash": "a1b2c3d",
                "message": "Initial commit",
                "author_name": "Dev",
                "relative_date": "2 hours ago",
            },
            "upstream": {
                "tracking_branch": "origin/main",
                "ahead": 0,
                "behind": 0,
            },
        }
        output = format_git_report(data)
        self.assertIn("GIT REPOSITORY STATUS", output)
        self.assertIn("main", output)
        self.assertIn("CLEAN (Working tree clean)", output)
        self.assertIn("[a1b2c3d] Initial commit", output)
        self.assertIn("Up to date", output)

    def test_format_git_report_dirty_and_diverged(self):
        data = {
            "is_repo": True,
            "root_dir": "/repo",
            "branch": "feature",
            "is_clean": False,
            "is_dirty": True,
            "total_changes": 3,
            "staged_count": 1,
            "unstaged_count": 1,
            "untracked_count": 1,
            "latest_commit": None,
            "upstream": {
                "tracking_branch": "origin/feature",
                "ahead": 2,
                "behind": 1,
            },
        }
        output = format_git_report(data)
        self.assertIn("DIRTY (3 uncommitted changes)", output)
        self.assertIn("1 staged, 1 unstaged, 1 untracked", output)
        self.assertIn("No commits recorded", output)
        self.assertIn("Diverged (+2, -1)", output)

    def test_format_git_report_ahead_behind_separate(self):
        data_ahead = {
            "is_repo": True,
            "is_clean": True,
            "upstream": {"tracking_branch": "origin/dev", "ahead": 3, "behind": 0},
        }
        out_ahead = format_git_report(data_ahead)
        self.assertIn("Ahead by 3 commits", out_ahead)

        data_behind = {
            "is_repo": True,
            "is_clean": True,
            "upstream": {"tracking_branch": "origin/dev", "ahead": 0, "behind": 4},
        }
        out_behind = format_git_report(data_behind)
        self.assertIn("Behind by 4 commits", out_behind)

    def test_format_all_report(self):
        data = {
            "system": {"platform": {}, "cpu": {}, "memory": {}, "disk": []},
            "processes": {"sort_by": "cpu", "count": 0, "limit": 5, "processes": []},
            "git": {"is_repo": False, "error": "Not a Git repo", "path": "."},
        }
        output = format_all_report(data)
        self.assertIn("SYSTEM HEALTH MONITOR", output)
        self.assertIn("TOP PROCESSES", output)
        self.assertIn("Error: Not a Git repo", output)

    def test_to_json(self):
        sample = {"numeric": 42, "text": "hello", "list": [1, 2, 3]}
        raw = to_json(sample)
        loaded = json.loads(raw)
        self.assertEqual(loaded, sample)


if __name__ == "__main__":
    unittest.main()
