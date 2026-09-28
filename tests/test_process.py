"""Unit tests for process inspection and ranking."""

import unittest
from unittest.mock import MagicMock, patch
import psutil

from sysmon_cli.process import get_top_processes


class TestProcessInspection(unittest.TestCase):
    """Test process inspection, sorting, and error handling."""

    def test_top_processes_default(self):
        res = get_top_processes(limit=5, sort_by="cpu", interval=0.0)
        self.assertIn("processes", res)
        self.assertIn("sort_by", res)
        self.assertEqual(res["sort_by"], "cpu")
        self.assertEqual(res["limit"], 5)
        self.assertLessEqual(len(res["processes"]), 5)

        for p in res["processes"]:
            self.assertIn("pid", p)
            self.assertIn("name", p)
            self.assertIn("cpu_percent", p)
            self.assertIn("memory_percent", p)
            self.assertIn("memory_rss_bytes", p)
            self.assertIn("memory_rss_human", p)
            self.assertIn("status", p)
            self.assertIsInstance(p["pid"], int)
            self.assertIsInstance(p["cpu_percent"], float)
            self.assertIsInstance(p["memory_percent"], float)

    @patch("time.sleep")
    def test_top_processes_sorted_by_cpu(self, mock_sleep):
        proc1 = MagicMock()
        proc1.pid = 101
        proc1.name.return_value = "proc1"
        proc1.cpu_percent.return_value = 15.0
        proc1.memory_percent.return_value = 1.0
        proc1.memory_info.return_value = MagicMock(rss=1000)
        proc1.status.return_value = "running"
        proc1.username.return_value = "u1"

        proc2 = MagicMock()
        proc2.pid = 102
        proc2.name.return_value = "proc2"
        proc2.cpu_percent.return_value = 85.0
        proc2.memory_percent.return_value = 2.0
        proc2.memory_info.return_value = MagicMock(rss=2000)
        proc2.status.return_value = "running"
        proc2.username.return_value = "u2"

        with patch("psutil.process_iter", return_value=[proc1, proc2]):
            res = get_top_processes(limit=10, sort_by="cpu", interval=0.05)
            mock_sleep.assert_called_once_with(0.05)
            procs = res["processes"]
            self.assertEqual(len(procs), 2)
            self.assertEqual(procs[0]["pid"], 102)
            self.assertEqual(procs[1]["pid"], 101)

    def test_top_processes_sorted_by_memory(self):
        proc1 = MagicMock()
        proc1.pid = 201
        proc1.name.return_value = "proc1"
        proc1.cpu_percent.return_value = 5.0
        proc1.memory_percent.return_value = 10.0
        proc1.memory_info.return_value = MagicMock(rss=1000)
        proc1.status.return_value = "running"
        proc1.username.return_value = "u1"

        proc2 = MagicMock()
        proc2.pid = 202
        proc2.name.return_value = "proc2"
        proc2.cpu_percent.return_value = 1.0
        proc2.memory_percent.return_value = 50.0
        proc2.memory_info.return_value = MagicMock(rss=5000)
        proc2.status.return_value = "running"
        proc2.username.return_value = "u2"

        with patch("psutil.process_iter", return_value=[proc1, proc2]):
            res = get_top_processes(limit=10, sort_by="memory", interval=0.0)
            procs = res["processes"]
            self.assertEqual(len(procs), 2)
            self.assertEqual(procs[0]["pid"], 202)
            self.assertEqual(procs[1]["pid"], 201)

    def test_invalid_sort_key_raises_error(self):
        with self.assertRaises(ValueError):
            get_top_processes(limit=5, sort_by="invalid_key")

    def test_include_idle_flag(self):
        idle_proc = MagicMock()
        idle_proc.pid = 0
        idle_proc.name.return_value = "System Idle Process"
        idle_proc.cpu_percent.return_value = 90.0
        idle_proc.memory_percent.return_value = 0.0
        idle_proc.memory_info.return_value = MagicMock(rss=0)
        idle_proc.status.return_value = "running"
        idle_proc.username.return_value = "SYSTEM"

        app_proc = MagicMock()
        app_proc.pid = 123
        app_proc.name.return_value = "app.exe"
        app_proc.cpu_percent.return_value = 10.0
        app_proc.memory_percent.return_value = 5.0
        app_proc.memory_info.return_value = MagicMock(rss=1000)
        app_proc.status.return_value = "running"
        app_proc.username.return_value = "user"

        with patch("psutil.process_iter", return_value=[idle_proc, app_proc]):
            # Exclude idle by default
            res_no_idle = get_top_processes(limit=20, include_idle=False, interval=0.0)
            pids_no_idle = [p["pid"] for p in res_no_idle["processes"]]
            self.assertNotIn(0, pids_no_idle)
            self.assertIn(123, pids_no_idle)

            # Include idle when requested
            res_with_idle = get_top_processes(limit=20, include_idle=True, interval=0.0)
            pids_with_idle = [p["pid"] for p in res_with_idle["processes"]]
            self.assertIn(0, pids_with_idle)
            self.assertIn(123, pids_with_idle)

    @patch("psutil.process_iter")
    def test_process_disappearing_handling(self, mock_iter):
        mock_proc1 = MagicMock()
        mock_proc1.pid = 100
        mock_proc1.name.return_value = "app.exe"
        mock_proc1.cpu_percent.return_value = 10.0
        mock_proc1.memory_percent.return_value = 2.0
        mock_info = MagicMock()
        mock_info.rss = 1048576
        mock_proc1.memory_info.return_value = mock_info
        mock_proc1.status.return_value = "running"
        mock_proc1.username.return_value = "user"

        mock_proc2 = MagicMock()
        mock_proc2.pid = 101
        # Raises NoSuchProcess when queried
        mock_proc2.name.side_effect = psutil.NoSuchProcess(101)

        mock_iter.return_value = [mock_proc1, mock_proc2]

        res = get_top_processes(limit=5, interval=0.0)
        self.assertEqual(len(res["processes"]), 1)
        self.assertEqual(res["processes"][0]["pid"], 100)

    def test_top_processes_zero_limit(self):
        res = get_top_processes(limit=0, interval=0.0)
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["processes"], [])

    def test_top_processes_negative_limit_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_top_processes(limit=-1, interval=0.0)

    @patch("psutil.process_iter")
    def test_top_processes_cpu_ranking_accuracy(self, mock_iter):
        proc_low = MagicMock()
        proc_low.pid = 201
        proc_low.name.return_value = "low.exe"
        proc_low.cpu_percent.return_value = 5.0
        proc_low.memory_percent.return_value = 1.0
        info_low = MagicMock()
        info_low.rss = 1000
        proc_low.memory_info.return_value = info_low
        proc_low.status.return_value = "running"
        proc_low.username.return_value = "low_user"

        proc_high = MagicMock()
        proc_high.pid = 202
        proc_high.name.return_value = "high.exe"
        proc_high.cpu_percent.return_value = 85.0
        proc_high.memory_percent.return_value = 0.5
        info_high = MagicMock()
        info_high.rss = 500
        proc_high.memory_info.return_value = info_high
        proc_high.status.return_value = "running"
        proc_high.username.return_value = "high_user"

        mock_iter.return_value = [proc_low, proc_high]
        res = get_top_processes(limit=2, sort_by="cpu", interval=0.0)
        self.assertEqual(len(res["processes"]), 2)
        self.assertEqual(res["processes"][0]["pid"], 202)
        self.assertEqual(res["processes"][0]["cpu_percent"], 85.0)
        self.assertEqual(res["processes"][1]["pid"], 201)
        self.assertEqual(res["processes"][1]["cpu_percent"], 5.0)

    @patch("psutil.process_iter")
    def test_process_access_denied_on_name(self, mock_iter):
        proc_locked = MagicMock()
        proc_locked.pid = 4
        proc_locked.name.side_effect = psutil.AccessDenied(4)
        proc_locked.cpu_percent.return_value = 12.0
        proc_locked.memory_percent.return_value = 1.0
        info = MagicMock()
        info.rss = 4096
        proc_locked.memory_info.return_value = info
        proc_locked.status.return_value = "running"
        proc_locked.username.side_effect = psutil.AccessDenied(4)

        mock_iter.return_value = [proc_locked]
        res = get_top_processes(limit=5, interval=0.0)
        self.assertEqual(len(res["processes"]), 1)
        self.assertEqual(res["processes"][0]["pid"], 4)
        self.assertEqual(res["processes"][0]["name"], "unknown")
        self.assertEqual(res["processes"][0]["cpu_percent"], 12.0)
        self.assertIsNone(res["processes"][0]["username"])

    @patch("psutil.process_iter")
    def test_process_nan_cpu_and_mem_percent(self, mock_iter):
        proc_nan = MagicMock()
        proc_nan.pid = 999
        proc_nan.name.return_value = "nan_proc"
        proc_nan.cpu_percent.return_value = float("nan")
        proc_nan.memory_percent.return_value = float("nan")
        proc_nan.memory_info.return_value = MagicMock(rss=100)
        proc_nan.status.return_value = "running"
        proc_nan.username.return_value = "user"

        mock_iter.return_value = [proc_nan]
        res = get_top_processes(limit=5, interval=0.0)
        self.assertEqual(len(res["processes"]), 1)
        self.assertEqual(res["processes"][0]["cpu_percent"], 0.0)
        self.assertEqual(res["processes"][0]["memory_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
